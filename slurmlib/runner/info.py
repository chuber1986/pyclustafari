"""Runnable information classes."""

from typing import Any


class RunInformation:
    """RunInformation class."""

    def __init__(self):
        self.result: Any = None
        self._output: str = ""
        self._error: str = ""
        self._log: str = ""

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

    @property
    def log(self):
        return self._result

    @log.setter
    def log(self, log):
        self._log = log
