"""Strategy for executing dumped JobLib files using subprocess."""

import logging
import subprocess
from pathlib import Path

from runnable import RunInformation, Runnable

COMMAND_TEMPLATE = r"python {} {}"

__all__ = ["SubprocessRunner"]


class SubprocessRunner:
    """Runs a JobLib file in a new Python instance."""

    def __init__(self, workerstub: Path):
        self.workerstub = workerstub

    def run(self, function: Runnable) -> RunInformation:
        logging.info("Execute Runner '%s'", self.__class__.__name__)
        info = RunInformation()

        file = function.tempfile
        command = COMMAND_TEMPLATE.format(str(self.workerstub), str(file)).split()
        info.output = subprocess.run(command, capture_output=True, check=True)

        return info
