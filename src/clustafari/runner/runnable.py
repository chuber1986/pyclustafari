"""Function wrapper classes."""

import logging
import pickle
import shutil
import struct
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

import joblib

from clustafari.exceptions import CancelledError, RunnableStateError, StateError, TimeoutException
from clustafari.paths import CLUSTAFARI_DIR
from clustafari.utils import (
    State,
    get_error_file,
    get_log_file,
    get_output_file,
    get_result_file,
    get_state_file,
)

from .info import RunInformation
from .state import _STATUS_BY_WORKER_STATE, RunState, RunStatus

logger = logging.getLogger(__name__)


def _get_function_name(fn: Callable):
    if hasattr(fn, "func"):
        return _get_function_name(fn.func)  # type: ignore  # noqa: PGH003

    assert hasattr(fn, "__qualname__"), "Function has no __qualname__ attribute."
    return fn.__qualname__


def _get_partial_arguments(fn: Callable) -> tuple[tuple, Mapping]:
    if hasattr(fn, "func") and hasattr(fn, "args") and hasattr(fn, "keywords"):
        return fn.args, fn.keywords  # type: ignore  # noqa: PGH003

    return (), {}


class Runnable:
    """Runner class."""

    def __init__(
        self,
        fn: Callable,
        *args: Any,
        return_object: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize Runnable with callable function and arguments."""
        self._state: RunState = RunState.INITIALIZED
        self._info: RunInformation = RunInformation()
        self._result: Any = None
        self._object: Any = None

        self.function: Callable = fn
        self.args: Iterable = args
        self.kwargs: Mapping = kwargs

        self.return_object = return_object

        self._timestamp: int = time.monotonic_ns()
        self.tempdir: Path | None = None
        self.tempfile: Path | None = None
        self.resultfile: Path | None = None
        self.outputfile: Path | None = None
        self.errorfile: Path | None = None
        self.logfile: Path | None = None
        self.statefile: Path | None = None

        logger.info("Create Runnable: %s", self.get_function_name())

    @property
    def state(self) -> RunState:
        """Return the current execution state."""
        return self._state

    @property
    def status(self) -> RunStatus:
        """Return the run's progress as a caller-facing status.

        Combines the caller-side state machine with the worker's reported
        progress (the state file): terminal caller states win, a run that
        was never dispatched is `NOT_STARTED`, and a dispatched run whose
        backing worker process or cluster job is observed dead without a
        terminal state-file report is `FAILED`.
        """
        if self._state == RunState.INITIALIZED:
            return RunStatus.NOT_STARTED
        if self._state in (RunState.FINISHED, RunState.FAILED, RunState.CANCELLED):
            return RunStatus(self._state.value)

        worker_state = self._read_state_file()
        if worker_state not in (State.IDLE, State.FINISHED, State.FAILED) and self._info.terminated():
            # The worker died before writing its terminal state: no further
            # progress will ever be reported and `get()` will fail this run.
            return RunStatus.FAILED
        return _STATUS_BY_WORKER_STATE[worker_state]

    @property
    def result(self) -> Any:
        """Return the result of the execution."""
        return self._result

    def fail(self, message: str) -> None:
        """Mark the execution as failed with an error message."""
        if self._state in (RunState.INITIALIZED, RunState.READY):
            self._state = RunState.FAILED
            self._info.error += message

    def finish(self, obj: Any, result: Any) -> None:
        """Mark the execution as finished with an owning object and a result."""
        if self._state != RunState.READY:
            msg = "A Runnable can only be finished in the READY state."
            raise RunnableStateError(msg)

        self._object = obj
        self._result = result
        self._state = RunState.FINISHED

    def cancel(self) -> None:
        """Cancel the run, transitioning it to the CANCELLED terminal state.

        From INITIALIZED the run is cancelled outright (it was never
        dispatched, so there is nothing to stop). From READY the run's
        information object is asked to stop the backing execution
        best-effort: a failing stop mechanism is logged as a warning and
        does not prevent the transition. From any terminal state (FAILED,
        FINISHED, CANCELLED) the call is a no-op.
        """
        if self._state in (RunState.FAILED, RunState.FINISHED, RunState.CANCELLED):
            return

        if self._state == RunState.READY:
            try:
                self._info.cancel()
            except Exception:  # noqa: BLE001
                logger.warning(
                    "Cancellation of run '%s' failed to stop the backing execution.",
                    self.get_function_name(),
                    exc_info=True,
                )

        self._state = RunState.CANCELLED
        logger.info("Cancel Runnable: %s", self.get_function_name())

    @property
    def info(self) -> Any:
        """Return the result of the execution."""
        return self._info

    @info.setter
    def info(self, info: Any) -> None:
        self._info = info

    def execute(self) -> None:
        """Prepare the executable for deployment."""
        if self._state != RunState.INITIALIZED:
            msg = f"Executing Runnable is only possible in state {RunState.INITIALIZED} but got {self._state}."
            raise RunnableStateError(msg)

        try:
            function_data = (self.function, self.args, self.kwargs)

            self.tempdir = CLUSTAFARI_DIR / f"{self._get_hash()}"
            self.tempdir.mkdir(exist_ok=True)

            self.tempfile = self.tempdir / f"{_get_function_name(self.function)}.joblib"
            self.resultfile = get_result_file(self.tempfile)
            self.outputfile = get_output_file(self.tempfile)
            self.errorfile = get_error_file(self.tempfile)
            self.logfile = get_log_file(self.tempfile)
            self.statefile = get_state_file(self.tempfile)

            logger.debug(
                "Dump serialized Runnable '%s' to file '%s'",
                self.get_function_name(),
                str(self.tempfile),
            )
            joblib.dump(function_data, self.tempfile)
            self._state = RunState.READY
        except Exception as err:  # noqa: BLE001
            # A preparation failure (hashing, directory creation, or
            # serialization) is not a job failure. Mark the run as failed so
            # callers report it through `get()` instead of leaking a raw
            # exception (e.g. `PicklingError`) out of `apply_async`.
            logger.debug("Prepare Runnable '%s' failed", self.get_function_name(), exc_info=True)
            self.fail(str(err))

    def _get_hash(self) -> str:
        return joblib.hash((self.function, self.args, self.kwargs, self._timestamp))

    def is_finished(self) -> bool:
        """Return whether the execution is finished."""
        if self._state in (RunState.FINISHED, RunState.FAILED, RunState.CANCELLED):
            return True

        if self._state != RunState.READY:
            return False

        if self._read_state_file() in [State.FAILED, State.FINISHED]:
            return True

        # The backing job ended on the cluster side (e.g. killed by the
        # kernel) without the worker writing a state file. Fail the run
        # instead of waiting for a state file that will never appear.
        if self._info.terminated():
            self.fail(self._termination_error_message())
            return True

        return False

    def _termination_error_message(self) -> str:
        # Backends that own the backing execution (e.g. the subprocess worker)
        # build a richer message including the exit code; fall back to the
        # generic state-file-based message otherwise.
        build = getattr(self._info, "termination_error_message", None)
        if build is not None:
            return build()

        err = self._read_file(self.errorfile).strip()
        if err:
            return f"Job terminated without writing a state file. Standard error:\n{err}"
        return "Job terminated without writing a state file (the worker died before reporting its state)."

    def _delete_temp_files(self):
        if self.tempdir is None or not self.tempdir.exists():
            return

        # Best-effort recursive removal. A plain unlink-then-rmdir races with
        # the (subprocess/slurm) worker, which can still be closing or creating
        # files in the directory at this point, leaving rmdir with a non-empty
        # directory and raising OSError. rmtree + ignore_errors removes what's
        # there and never fails the run for a cleanup hiccup.
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def _read_state_file(self) -> State:
        if self.statefile is None or not self.statefile.exists():
            return State.IDLE

        with self.statefile.open("r") as f:
            content = f.read().strip()

        if not content:
            # A freshly touched (still empty) state file must not go through
            # State(content): the miss would log a warning on every poll
            # until the worker writes the first real state.
            return State.IDLE
        return State(content.lower())

    def _read_job_file(self, file: Path | None) -> tuple[Any, Any]:
        if file is None or not file.exists():
            return None, None

        try:
            return joblib.load(file)
        except (EOFError, struct.error, OSError, ValueError, pickle.UnpicklingError):
            # The result file is written by the worker (possibly over NFS) and
            # can be truncated or corrupted mid-read (a torn pickle raises
            # struct.error/EOFError, a partial write OSError). Treat any
            # unreadable result as "no result" so get() reports a failed run
            # instead of crashing with a raw deserialization error.
            return None, None

    def _read_file(self, file: Path | None) -> str:
        if file is None or not file.exists():
            return ""

        try:
            with file.open("r") as f:
                return f.read()
        except RuntimeError:
            return ""

    def _read_result_files(self) -> None:
        assert self.is_finished(), "Must not read results before they are ready."
        self._object, self._result = self._read_job_file(self.resultfile)

        out = self._read_file(self.outputfile)
        err = self._read_file(self.errorfile)

        log = self._read_file(self.logfile)

        self._info.output = out
        self._info.error = err
        self._info.log = log

        if self._read_state_file() == State.FINISHED:
            self._state = RunState.FINISHED
        else:
            self._state = RunState.FAILED

        self._delete_temp_files()

    def get(self, blocking: bool = False, timeout: float = -1) -> Any:  # noqa: FBT001, FBT002
        """Retrieve the result of the execution.

        If 'blocking', blocks until the result is ready. If 'blocking' and 'timeout' is set to a positive value,
        raises a TimeoutException if the result is not ready within the timeout period.
        """
        if self._state == RunState.INITIALIZED:
            msg = "Job was not started."
            raise RunnableStateError(msg)

        deadline = time.monotonic() + timeout if timeout > 0 else None
        while not self.is_finished() and blocking:
            time.sleep(0.1)

            if deadline is not None and time.monotonic() > deadline:
                msg = "Result not ready. Timeout reached."
                raise TimeoutException(msg)

        if not self.is_finished() and not blocking:
            msg = "Job not finished. Result not ready."
            raise RunnableStateError(msg)

        if self._state == RunState.READY:
            self._read_result_files()

        if self._state == RunState.CANCELLED:
            # The run was cancelled: no result exists and the temp artifacts
            # are no longer needed. Raise the dedicated error so callers can
            # distinguish cancellation from failure.
            self._delete_temp_files()
            msg = "Execution was cancelled. No result available."
            raise CancelledError(msg)

        if self._state == RunState.FAILED:
            # The worker has reported its terminal (failed) state, so no
            # process will touch the run's artifacts anymore. Delete them now
            # (the success path cleans up in _read_result_files); otherwise a
            # failed run whose handle outlives get() (e.g. a DummyRunner
            # failure) leaves the tempdir behind until garbage collection.
            self._delete_temp_files()
            msg = (
                "Execution failed. No result available.\nClustafari Log:\n"
                f"{self._info.log}\n\nExecution Error:\n{self._info.error!s}"
            )
            raise StateError(msg)

        if self.return_object:
            return self._object, self._result

        return self._result

    def get_function_name(self) -> str:
        """Return the name of the wrapped function."""
        return _get_function_name(self.function)

    def __del__(self) -> None:
        del self._info
        self._delete_temp_files()

    def __repr__(self) -> str:
        fn_name = _get_function_name(self.function)
        pargs, pkwargs = _get_partial_arguments(self.function)

        a = [str(arg) for arg in list(pargs) + list(self.args)]
        kwa = [f"{k!s}={v!s}" for k, v in {**pkwargs, **self.kwargs}.items()]

        astr = ", ".join(a)
        kwastr = ", ".join(kwa)
        return f"{fn_name}({astr}, {kwastr})"

    def __str__(self) -> str:
        """Return the run description with its current status (and job ID)."""
        jobid = getattr(self._info, "jobid", None)
        job = f", job {jobid}" if jobid is not None else ""
        return f"{self!r} [{self.status.value}{job}]"
