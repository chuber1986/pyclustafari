"""Function wrapper classes."""

import logging
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Tuple

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


def _get_function_name(fn: Callable):
    if hasattr(fn, "func"):
        return _get_function_name(fn.func)

    return fn.__qualname__


def _get_partial_arguments(fn: Callable) -> Tuple[Tuple, Mapping]:
    if hasattr(fn, "func") and hasattr(fn, "args") and hasattr(fn, "keywords"):
        return fn.args, fn.keywords

    return tuple(), {}


class Runnable:
    """Runner class."""

    def __init__(
        self,
        fn: Callable,
        *args,
        return_object=False,
        **kwargs,
    ):
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

        logging.info("Create Runnable: %s", repr(self))

    @property
    def result(self) -> Any:
        return self._result

    @result.setter
    def result(self, result):
        if self.result is not None:
            raise RunnableStateError("Results already set.")

        if self._state != RunState.READY:
            raise RunnableStateError("Result can only be set by an RUNNING Runnable.")

        self._result = result
        self._state = RunState.FINISHED

    def execute(self):
        if self._state != RunState.INITIALIZED:
            raise RunnableStateError(
                f"Executing Runnable is only possible in state "
                f"{RunState.INITIALIZED} but got {self._state}."
            )

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

            logging.debug(
                "Dump serialized Runnable '%s' to file '%s'",
                repr(self),
                str(self.tempfile),
            )
            joblib.dump(function_data, self.tempfile)
            self._state = RunState.READY
        except RuntimeError as err:
            self._state = RunState.FAILED
            self._info.log += str(err)

    def _get_hash(self):
        return joblib.hash((self.function, self.args, self.kwargs, self._timestamp))

    def is_finished(self):
        if self._state == RunState.FINISHED:
            return True

        return self._state == RunState.READY and self._read_state_file() in [
            State.FAILED,
            State.FINISHED,
        ]

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

    def _read_job_file(self, file: Path | None):
        if file is None or not file.exists():
            return ""

        try:
            return joblib.load(file)
        except EOFError:
            return None

    def _read_file(self, file: Path | None):
        if file is None or not file.exists():
            return ""

        try:
            with file.open("r") as f:
                return f.read()
        except RuntimeError:
            return ""

    def _read_result_files(self):
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

    def get(self, blocking: bool = False, timeout: int = -1) -> Any:
        if self._state == RunState.INITIALIZED:
            raise RunnableStateError("Job was not stated.")

        runtime = 0.0
        while not self.is_finished() and blocking:
            if self._state == RunState.FAILED:
                raise RunnableStateError("Execution failed. No result available.")

            time.sleep(0.1)
            runtime += 0.1

            if 0 < timeout < runtime:
                raise TimeoutException("Result not ready. Timeout reached.")

        if not self.is_finished() and not blocking:
            raise RunnableStateError("Job not finished. Result not ready.")

        if self._state == RunState.READY:
            self._read_result_files()

        if self._state == RunState.FAILED:
            raise StateError(
                "Job was cancelled. No result available.\nClustafari Log:\n"
                f"{self._info.log}\n\nExecution Error:\n{str(self._info.error)}"
            )

        if self.return_object:
            return self._object, self._result

        return self._result

    def get_function_name(self):
        return _get_function_name(self.function)

    def __del__(self):
        del self._info
        self._delete_temp_files()

    def __repr__(self):
        fn_name = _get_function_name(self.function)
        pargs, pkwargs = _get_partial_arguments(self.function)

        a = [str(arg) for arg in list(pargs) + list(self.args)]
        kwa = [f"{str(k)}={str(v)}" for k, v in {**pkwargs, **self.kwargs}.items()]

        astr = ", ".join(a)
        kwastr = ", ".join(kwa)
        return f"{fn_name}({astr}, {kwastr})"
