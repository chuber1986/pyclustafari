"""Strategy for executing dumped JobLib files using subprocess."""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import override

from clustafari.runner import BaseRunner, RunInformation, Runnable
from clustafari.runner.state import RunState

from .config import _SubprocessConfig

logger = logging.getLogger(__name__)

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
        if runobj.state == RunState.FAILED:
            return RunInformation()

        command = [sys.executable, str(self.config.workerstub), str(runobj.tempfile)]
        env = os.environ.copy()
        env["PYTHONPATH"] = Path.cwd().as_posix() + os.pathsep + env.get("PYTHONPATH", "")

        try:
            subprocess.Popen(command, env=env)  # noqa: S603
        except OSError as e:
            runobj.fail(str(e))

        return RunInformation()
