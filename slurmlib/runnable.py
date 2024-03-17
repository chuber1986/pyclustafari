"""Runnable information classes."""

import logging
import sys
import time
from contextlib import contextmanager
from enum import Enum, auto
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol, Tuple

import joblib
from utils import get_result_file

from slurmlib import SLURMLIB_DIR


@contextmanager
def redirected(out=sys.stdout, err=sys.stderr):
    saved = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        yield
    finally:
        sys.stdout, sys.stderr = saved


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
        self.error: str | None = None
        self.result: Any = None

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
    def run(self, function: "Runnable") -> RunInformation: ...


class RunnableStateError(RuntimeError):
    pass


class TimeoutException(Exception):
    pass


class Runnable:
    """Runner class."""

    def __init__(self, runner: Runner, fn: Callable, *args, **kwargs):
        self._state: _RunState = _RunState.INITIALIZED
        self._info: RunInformation = RunInformation()
        self._result: Any = None

        self.runner = runner
        self.function: Callable = fn
        self.args: Iterable = args
        self.kwargs: Mapping = kwargs

        self._timestamp: int = time.monotonic_ns()
        self.tempfile: Path | None = None
        self.resultfile: Path | None = None

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
                stream = StringIO()
                with redirected(err=stream, out=stream):
                    self.result = self.function(*self.args, **self.kwargs)

                self._info.output = str(stream)
                return

            function_data = (self.function, self.args, self.kwargs)
            self.tempfile = SLURMLIB_DIR / f"{self._get_hash()}.joblib"
            self.resultfile = get_result_file(self.tempfile)

            logging.debug(
                "Dump serialized Runnable '%s' to file '%s'",
                repr(self),
                str(self.tempfile),
            )
            joblib.dump(function_data, self.tempfile)

            logging.info(
                "Execute '%s' with %s", repr(self), self.runner.__class__.__name__
            )
            self._info = self.runner.run(self)
        except RuntimeError as err:
            self._state = _RunState.FAILED
            self._info.error = err

    def _get_hash(self):
        return joblib.hash((self.function, self.args, self.kwargs, self._timestamp))

    def is_result_available(self):
        if self._state == _RunState.FINISHED:
            return True

        return (
            self._state == _RunState.RUNNING
            and self.resultfile
            and self.resultfile.exists()
        )

    def _delete_temp_files(self):
        if self.tempfile is not None:
            self.tempfile.unlink(missing_ok=True)
        if self.resultfile is not None:
            self.resultfile.unlink(missing_ok=True)

    def _read_result_file(self):
        self._result = joblib.load(self.resultfile)
        self._state = _RunState.FINISHED
        self._delete_temp_files()

    def get(self, blocking: bool = False, timeout: int = -1) -> Any:
        if self._state == _RunState.INITIALIZED:
            raise RunnableStateError("Job was not stated.")

        runtime = 0.0
        while not self.is_result_available() and blocking:
            if self._state == _RunState.FAILED:
                raise RunnableStateError("Job was cancelled. No result available.")

            time.sleep(0.1)
            runtime += 0.1

            if 0 < timeout < runtime:
                raise TimeoutException("Result not ready. Timeout reached.")

        if not self.is_result_available() and not blocking:
            raise RunnableStateError("Job not finished. Result not ready.")

        if self._state == _RunState.RUNNING:
            self._read_result_file()
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
