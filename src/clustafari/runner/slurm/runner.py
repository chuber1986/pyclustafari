"""Strategy for executing dumped JobLib files using slurm."""

import logging
import os
from typing import override

from pyslurm import JobSubmitDescription

from clustafari.exceptions import StateError
from clustafari.runner import BaseRunner, RunInformation, Runnable
from clustafari.utils import get_error_file, get_output_file

from .config import _SlurmConfig
from .info import SlurmInformation

COMMAND_TEMPLATE = r"python {} {}"

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

        file = runobj.tempfile
        if file is None:
            raise StateError

        outfile = get_output_file(file)
        errfile = get_error_file(file)

        # TODO(Christian): make Python interpreter configurable #0001  # noqa: FIX002
        desc = JobSubmitDescription(
            name=runobj.get_function_name(),
            standard_output=str(outfile),
            standard_error=str(errfile),
            script=str(self.config.job_file),
            script_args=f"3 {os.environ['_']} {self.config.workerstub!s} {file!s}",
            **self.config.resources,
        )

        jobid = desc.submit()
        runobj.info = SlurmInformation(jobid)
        return runobj.info
