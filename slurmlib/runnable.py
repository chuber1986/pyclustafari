"""Runnable information classes."""
import time
import tempfile
from enum import Enum, auto
from typing import Callable, Iterable, Mapping, Tuple, Any

import joblib

from slurmlib import SLURMLIB_DIR


class _RunState(Enum):
    """RunState class."""
    INITIALIZED = auto()
    RUNNING = auto()
    FAILED = auto()
    FINISHED = auto()


class _RunInformation:
    """RunInformation class."""

    def __init__(self):
        pass


def _get_function_name(fn: Callable):
    if hasattr(fn, "func"):
        return _get_function_name(fn.func)

    return fn.__qualname__


def _get_partial_arguments(fn: Callable) -> Tuple[Tuple, Mapping]:
    if hasattr(fn, "func") and hasattr(fn, "args") and hasattr(fn, "keywords"):
        return fn.args, fn.keywords

    return tuple(), dict()


class Runnable:
    """Runner class."""

    def __init__(self, fn: Callable, *args, **kwargs):
        self._state: _RunState = _RunState.INITIALIZED
        self._info: _RunInformation = _RunInformation()

        self.function: Callable = fn
        self.args: Iterable = args
        self.kwargs: Mapping = kwargs

        self.result: Any = None

    def execute(self):
        self._state = _RunState.RUNNING
        try:
            self.result = self.function(*self.args, **self.kwargs)

            function_data = (self.function, self.args, self.kwargs)
            hash = joblib.hash(function_data)

            with open(SLURMLIB_DIR/f"{hash}.joblib", "wb") as file:
                joblib.dump(function_data, file)

            with open(SLURMLIB_DIR / f"{hash}.joblib", "rb") as file:
                fn, args, kwargs = joblib.load(file)

            self.result = fn(*args, **kwargs)

            self._state = _RunState.FINISHED
        except RuntimeError:
            self._state = _RunState.FAILED

    def get(self, blocking: bool = False, timeout: int = -1) -> Any:
        if self._state == _RunState.INITIALIZED:
            raise RuntimeError("Job was not stated.")

        runtime = 0.0
        while self._state != _RunState.FINISHED and blocking:
            if self._state == _RunState.FAILED:
                raise RuntimeError("Job was cancelled. No result available.")

            time.sleep(0.1)
            runtime += 0.1

            if 0 < timeout < runtime:
                raise RuntimeError("Result not ready. Timeout reached.")

        if self._state != _RunState.FINISHED and not blocking:
            raise RuntimeError("Job not finished. Result not ready.")

        return self.result

    def __repr__(self):
        fn_name = _get_function_name(self.function)
        pargs, pkwargs = _get_partial_arguments(self.function)
        a = [str(arg) for arg in list(pargs) + list(self.args)]
        kwa = [f"{str(k)}={str(v)}" for k, v in {**pkwargs, **self.kwargs}.items()]
        return f"{fn_name}({", ".join(a)}, {", ".join(kwa)})"
