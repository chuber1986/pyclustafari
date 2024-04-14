"""Strategy for executing dumped JobLib files using subprocess."""

import logging
from io import StringIO

from typing_extensions import override

from slurmlib.runner import BaseRunner, RunInformation, Runnable
from slurmlib.utils import redirect_io

COMMAND_TEMPLATE = r"python {} {}"

__all__ = ["DummyRunner"]


class DummyRunner(BaseRunner):
    """Runs a JobLib file in a new Python instance."""

    @override
    def _run(self, runobj: Runnable) -> RunInformation:
        logging.info("Execute Runner '%s'", self.__class__.__name__)
        runobj.execute()

        info = RunInformation()
        fn = runobj.function
        args = runobj.args
        kwargs = runobj.kwargs

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

        runobj.result = info.result
        return info
