"""Strategy for executing dumped JobLib files in the current process."""

import logging
from io import StringIO
from typing import override

from clustafari.runner import BaseRunner, RunInformation, Runnable
from clustafari.utils import redirect_io

__all__ = ["DummyRunner"]

logger = logging.getLogger(__name__)


class DummyRunner(BaseRunner):
    """Runs a JobLib file in the current Python process."""

    @override
    def _run(self, runobj: Runnable) -> RunInformation:
        logger.info("Execute Runner '%s'", self.__class__.__name__)
        runobj.execute()

        info = RunInformation()
        fn = runobj.function
        args = runobj.args
        kwargs = runobj.kwargs

        out = StringIO()
        err = StringIO()
        runobj.info = info
        with redirect_io(err=err, out=out):
            try:
                info.result = fn(*args, **kwargs)
            except BaseException as e:  # noqa: BLE001
                info.error = str(e)
                runobj.fail(str(e))
                return info

        info.output = str(out)
        info.error += str(err)

        if runobj.return_object:
            runobj.finish(getattr(fn, "__self__", None), info.result)
        else:
            runobj.finish(None, info.result)
        return info
