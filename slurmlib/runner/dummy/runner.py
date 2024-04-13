"""Strategy for executing dumped JobLib files using subprocess."""

import logging
from io import StringIO

from slurmlib.runnable import RunInformation, Runnable
from slurmlib.utils import redirect_io

from .config import _DummyConfig

COMMAND_TEMPLATE = r"python {} {}"

__all__ = ["DummyRunner"]


class DummyRunner:
    """Runs a JobLib file in a new Python instance."""

    def __init__(self, config: _DummyConfig):
        self.config = config

    def run(self, runnable: Runnable) -> RunInformation:
        logging.info("Execute Runner '%s'", self.__class__.__name__)
        runnable.execute()

        info = RunInformation()
        fn = runnable.function
        args = runnable.args
        kwargs = runnable.kwargs

        out = StringIO()
        err = StringIO()
        with redirect_io(err=err, out=out):
            try:
                info.result = fn(*args, **kwargs)
            except BaseException as e:
                info.error = str(e)
                raise e

        info.output = str(out)
        info.error += str(err)

        runnable.result = info.result
        return info
