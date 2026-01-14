"""Strategy for executing dumped JobLib files using subprocess."""

import logging
import os
import subprocess
from typing import override

from clustafari.runner import BaseRunner, RunInformation, Runnable

from .config import _SubprocessConfig

logger = logging.getLogger(__name__)

COMMAND_TEMPLATE = os.environ["_"] + r" {} {}"

__all__ = ["SubprocessRunner"]


class SubprocessRunner(BaseRunner):
    """Runs a JobLib file in a new Python instance."""

    def __init__(self, config: _SubprocessConfig) -> None:
        """Initialize Subprocess Runner with configuration."""
        super().__init__()
        self.config = config

    @override
    def _run(self, runobj: Runnable) -> RunInformation:
        logger.info("Execute Runner '%s'", self.__class__.__name__)
        runobj.execute()
        info = RunInformation()

        file = runobj.tempfile
        command = COMMAND_TEMPLATE.format(str(self.config.workerstub), str(file)).split()
        info.output = str(subprocess.run(command, capture_output=True, check=True))  # noqa: S603

        return info
