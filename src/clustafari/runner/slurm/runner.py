"""Strategy for executing dumped JobLib files using slurm."""

import logging
import os
import sys
from pathlib import Path
from typing import override

from clustafari.runner import BaseRunner, RunInformation, Runnable
from clustafari.runner.state import RunState
from clustafari.utils import get_error_file, get_output_file

from .config import _SlurmConfig
from .info import SlurmInformation

__all__ = ["SlurmRunner"]

logger = logging.getLogger(__name__)


class SlurmRunner(BaseRunner):
    """Runs a JobLib file on a Slurm cluster."""

    def __init__(self, config: _SlurmConfig) -> None:
        """Initialize Slurm Runner with configuration."""
        super().__init__()
        self.config = config
        self.job_id: int | None = None

    @override
    def _run(self, runobj: Runnable) -> RunInformation:
        logger.info("Execute Runner '%s'", self.__class__.__name__)
        runobj.execute()
        if runobj.state == RunState.FAILED:
            return RunInformation()

        file = runobj.tempfile
        assert file is not None, "execute() must have created the job file."

        from pyslurm import JobSubmitDescription

        outfile = get_output_file(file)
        errfile = get_error_file(file)

        # TODO(Christian): make Python interpreter configurable #0001  # noqa: FIX002
        desc = JobSubmitDescription(
            name=runobj.get_function_name(),
            standard_output=str(outfile),
            standard_error=str(errfile),
            script=str(self.config.job_file),
            script_args=f"3 {sys.executable} {self.config.workerstub!s} {file!s}",
            # Mirror the caller's working directory so functions defined in
            # project-local modules (e.g. tests) are importable in the worker.
            environment={
                "PYTHONPATH": Path.cwd().as_posix() + os.pathsep + os.environ.get("PYTHONPATH", ""),
            },
            **self.config.resources,
        )

        try:
            jobid = desc.submit()
        except Exception as e:  # noqa: BLE001
            runobj.fail(str(e))
            return RunInformation()

        runobj.info = SlurmInformation(jobid)
        return runobj.info
