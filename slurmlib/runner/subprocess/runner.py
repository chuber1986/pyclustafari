"""Strategy for executing dumped JobLib files using subprocess."""

import logging
import subprocess

from slurmlib.runnable import RunInformation, Runnable

from .config import _SubprocessConfig

COMMAND_TEMPLATE = r"python {} {}"

__all__ = ["SubprocessRunner"]


class SubprocessRunner:
    """Runs a JobLib file in a new Python instance."""

    def __init__(self, config: _SubprocessConfig):
        self.config = config

    def run(self, runnable: Runnable) -> RunInformation:
        logging.info("Execute Runner '%s'", self.__class__.__name__)
        runnable.execute()
        info = RunInformation()

        file = runnable.tempfile
        command = COMMAND_TEMPLATE.format(
            str(self.config.workerstub), str(file)
        ).split()
        info.output = subprocess.run(command, capture_output=True, check=True)

        return info
