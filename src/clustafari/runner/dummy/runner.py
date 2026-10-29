"""Strategy for executing dumped JobLib files in the current process."""

import logging
from io import StringIO
from typing import override

from clustafari.runner import BaseRunner, RunInformation, Runnable
from clustafari.runner.state import RunState
from clustafari.utils import redirect_io

__all__ = ["DummyRunner"]

logger = logging.getLogger(__name__)


class DummyRunner(BaseRunner):
    """Runs a JobLib file in the current Python process."""

    @override
    def _run(self, runobj: Runnable) -> RunInformation:
        logger.info("Execute Runner '%s'", self.__class__.__name__)
        runobj.execute()
        if runobj.state == RunState.FAILED:
            return RunInformation()

        info = RunInformation()
        out = StringIO()
        err = StringIO()
        runobj.info = info
        with redirect_io(err=err, out=out):
            try:
                result = runobj.function(*runobj.args, **runobj.kwargs)
            except BaseException as e:  # noqa: BLE001
                runobj.fail(str(e))
                return info

        info.output = out.getvalue()
        info.error += err.getvalue()

        if runobj.return_object:
            runobj.finish(getattr(runobj.function, "__self__", None), result)
        else:
            runobj.finish(None, result)
        return info
