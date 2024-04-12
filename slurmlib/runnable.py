"""Runnable information classes."""

import logging
import time
from enum import Enum, auto
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol, Tuple

import joblib
from utils import (
    State,
    get_error_file,
    get_log_file,
    get_output_file,
    get_result_file,
    get_state_file,
    redirect_io,
)

from slurmlib import SLURMLIB_DIR


def _get_function_name(fn: Callable):
    if hasattr(fn, "func"):
        return _get_function_name(fn.func)

    return fn.__qualname__


def _get_partial_arguments(fn: Callable) -> Tuple[Tuple, Mapping]:
    if hasattr(fn, "func") and hasattr(fn, "args") and hasattr(fn, "keywords"):
        return fn.args, fn.keywords

    return tuple(), {}


class _RunState(Enum):
    """RunState class."""

    INITIALIZED = auto()
    RUNNING = auto()
    FAILED = auto()
    FINISHED = auto()


class RunInformation:
    """RunInformation class."""

    def __init__(self):
        self.output: str = ""
        self.error: str = ""
        self.result: Any = None
        self.log: str = ""

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, output: str):
        self._output = output

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, error):
        self._error = error

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, result):
        self._result = result


class Runner(Protocol):
    def run(self, function: "Runnable", resource: dict) -> RunInformation: ...


class RunnableStateError(RuntimeError):
    pass


class TimeoutException(Exception):
    pass


class Runnable:
    """Runner class."""

    def __init__(
        self, runner: Runner | None, resources: dict, fn: Callable, *args, **kwargs
    ):
        self._state: _RunState = _RunState.INITIALIZED
        self._info: RunInformation = RunInformation()
        self._result: Any = None

        self.runner = runner
        self.resources = resources
        self.function: Callable = fn
        self.args: Iterable = args
        self.kwargs: Mapping = kwargs

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

        if self._state != _RunState.RUNNING:
            raise RunnableStateError("Result can only be set by an RUNNING Runnable.")

        self._result = result
        self._state = _RunState.FINISHED

    def execute(self):
        if self._state != _RunState.INITIALIZED:
            raise RunnableStateError(
                f"Executing Runnable is only possible in state "
                f"{_RunState.INITIALIZED} but got {self._state}."
            )

        self._state = _RunState.RUNNING
        try:
            if self.runner is None:
                logging.info("Execute '%s' without runner.", repr(self))
                out = StringIO()
                err = StringIO()
                with redirect_io(err=err, out=out):
                    self.result = self.function(*self.args, **self.kwargs)

                self._info.output = str(out)
                self._info.error = str(err)

                return

            function_data = (self.function, self.args, self.kwargs)

            self.tempdir = SLURMLIB_DIR / f"{self._get_hash()}"
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

            logging.info(
                "Execute '%s' with %s", repr(self), self.runner.__class__.__name__
            )
            self._info = self.runner.run(self, self.resources)
        except RuntimeError as err:
            self._state = _RunState.FAILED
            self._info.log += str(err)

    def _get_hash(self):
        return joblib.hash((self.function, self.args, self.kwargs, self._timestamp))

    def is_finished(self):
        if self._state == _RunState.FINISHED:
            return True

        return self._state == _RunState.RUNNING and self._read_state_file() in [
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

    def _read_file(self, file):
        if file is None or not file.exists():
            return ""

        return joblib.load(file)

    def _read_result_files(self):
        assert self.is_finished(), "Must not read results before they are ready."
        self._result = self._read_file(self.resultfile)

        out = self._read_file(self.outputfile)
        err = self._read_file(self.errorfile)

        log = self._read_file(self.logfile)

        self._info.output = out
        self._info.error = err
        self._info.log = log

        if self._read_state_file() == State.FINISHED:
            self._state = _RunState.FINISHED
        else:
            self._state = _RunState.FAILED

        self._delete_temp_files()

    def get(self, blocking: bool = False, timeout: int = -1) -> Any:
        if self._state == _RunState.INITIALIZED:
            raise RunnableStateError("Job was not stated.")

        runtime = 0.0
        while not self.is_finished() and blocking:
            if self._state == _RunState.FAILED:
                raise RunnableStateError("Execution failed. No result available.")

            time.sleep(0.1)
            runtime += 0.1

            if 0 < timeout < runtime:
                raise TimeoutException("Result not ready. Timeout reached.")

        if not self.is_finished() and not blocking:
            raise RunnableStateError("Job not finished. Result not ready.")

        if self._state == _RunState.RUNNING:
            self._read_result_files()

        if self._state == _RunState.FAILED:
            raise RunnableStateError(
                f"Job was cancelled. No result available.\n{self._info.log}\n\n{str(self._info.error)}"
            )

        return self._result

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
