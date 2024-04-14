"""Strategy for executing dumped JobLib files using subprocess."""

import logging
import subprocess

from typing_extensions import override

from clustafari.runner import BaseRunner, RunInformation, Runnable

from .config import _SubprocessConfig

COMMAND_TEMPLATE = r"python {} {}"

__all__ = ["SubprocessRunner"]


class SubprocessRunner(BaseRunner):
    """Runs a JobLib file in a new Python instance."""

    def __init__(self, config: _SubprocessConfig):
        super().__init__()
        self.config = config

    @override
    def _run(self, runobj: Runnable) -> RunInformation:
        logging.info("Execute Runner '%s'", self.__class__.__name__)
        runobj.execute()
        info = RunInformation()

        file = runobj.tempfile
        command = COMMAND_TEMPLATE.format(
            str(self.config.workerstub), str(file)
        ).split()
        info.output = subprocess.run(command, capture_output=True, check=True)

        return info
