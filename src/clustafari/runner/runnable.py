"""Function wrapper classes."""

import logging
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

import joblib

from clustafari.exceptions import RunnableStateError, StateError, TimeoutException
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
from .state import RunState

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
        *args: list,
        return_object: bool = False,
        **kwargs: dict,
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

        logger.info("Create Runnable: %s", repr(self))

    @property
    def state(self) -> RunState:
        """Return the current execution state."""
        return self._state

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
                repr(self),
                str(self.tempfile),
            )
            joblib.dump(function_data, self.tempfile)
            self._state = RunState.READY
        except RuntimeError as err:
            self.fail(str(err))

    def _get_hash(self) -> str | None:
        return joblib.hash((self.function, self.args, self.kwargs, self._timestamp))

    def is_finished(self) -> bool:
        """Return whether the execution is finished."""
        if self._state in (RunState.FINISHED, RunState.FAILED):
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
        err = self._read_file(self.errorfile).strip()
        if err:
            return f"Job terminated without writing a state file. Standard error:\n{err}"
        return "Job terminated without writing a state file (the worker died before reporting its state)."

    def _delete_temp_files(self):
        if self.tempdir is None or not self.tempdir.exists():
            return

        for file in self.tempdir.iterdir():
            file.unlink(missing_ok=True)

        self.tempdir.rmdir()

    def _read_state_file(self) -> State:
        if self.statefile is None or not self.statefile.exists():
            return State.IDLE

        with self.statefile.open("r") as f:
            content = f.read().strip()

        return State(content.lower())

    def _read_job_file(self, file: Path | None) -> tuple[Any, Any]:
        if file is None or not file.exists():
            return None, None

        try:
            return joblib.load(file)
        except EOFError:
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

        if self._state == RunState.FAILED:
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
