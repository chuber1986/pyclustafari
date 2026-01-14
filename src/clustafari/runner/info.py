"""Runnable information classes."""

from typing import Any


class RunInformation:
    """RunInformation class."""

    def __init__(self) -> None:
        """Initialize RunInformation with default values."""
        self._result: Any = None
        self._output: str = ""
        self._error: str = ""
        self._log: str = ""

    @property
    def output(self) -> str:
        """Return the output of the execution."""
        return self._output

    @output.setter
    def output(self, output: str) -> None:
        """Set the output of the execution."""
        self._output = output

    @property
    def error(self) -> str:
        """Return the error of the execution."""
        return self._error

    @error.setter
    def error(self, error: str) -> None:
        """Set the error of the execution."""
        self._error = error

    @property
    def result(self) -> Any:
        """Return the result of the execution."""
        return self._result

    @result.setter
    def result(self, result: Any) -> None:
        """Set the result of the execution."""
        self._result = result

    @property
    def log(self) -> str:
        """Return the log of the execution."""
        return self._log

    @log.setter
    def log(self, log: str) -> None:
        """Set the log of the execution."""
        self._log = log
