"""Strategy for executing dumped JobLib files using slurm."""

import logging

from pyslurm import JobSubmitDescription
from typing_extensions import override

from slurmlib import StateError
from slurmlib.runner import BaseRunner, RunInformation, Runnable
from slurmlib.utils import get_error_file, get_output_file

from .config import _SlurmConfig
from .info import SlurmInformation

COMMAND_TEMPLATE = r"python {} {}"

__all__ = ["SlurmRunner"]


class SlurmRunner(BaseRunner):
    """Runs a JobLib file on a Slurm cluster."""

    def __init__(self, config: _SlurmConfig):
        super().__init__()
        self.config = config
        self.job_id: int | None = None

    @override
    def _run(self, runobj: Runnable) -> RunInformation:
        logging.info("Execute Runner '%s'", self.__class__.__name__)
        runobj.execute()

        file = runobj.tempfile
        if file is None:
            raise StateError

        outfile = get_output_file(file)
        errfile = get_error_file(file)

        # TODO: make Python interpreter configurable
        desc = JobSubmitDescription(
            name="slurmlib-job",
            standard_output=str(outfile),
            standard_error=str(errfile),
            script=str(self.config.job_file),
            script_args=f"1 python {str(self.config.workerstub)} {str(file)}",
            **self.config.resources,
        )

        jobid = desc.submit()
        info = SlurmInformation(jobid)

        return info
