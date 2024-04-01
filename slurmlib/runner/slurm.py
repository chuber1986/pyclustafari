"""Strategy for executing dumped JobLib files using slurm."""

import logging
from pathlib import Path

from pyslurm import Job, JobSubmitDescription
from runnable import RunInformation, Runnable
from typing_extensions import override

import slurmlib
from slurmlib import JOB_FILE, WORKERSTUB

COMMAND_TEMPLATE = r"python {} {}"

__all__ = ["SlurmRunner"]


class SlurmInformation(RunInformation):
    """Provides information about executed slurm jobs."""

    def __init__(self, jobid: int):
        super().__init__()
        self.jobid = jobid

    def debug_info(self):
        job = Job.load(self.jobid)
        return job.to_dict()

    @override
    def output(self):
        job = Job.load(self.jobid)
        out_file = Path(job.standard_output)

        if out_file.exists():
            with out_file.open("r", encoding="utf-8") as f:
                self._output = f.read()

        return super().output()

    @override
    def error(self):
        job = Job.load(self.jobid)
        err_file = Path(job.standard_error)

        if err_file.exists():
            with err_file.open("r", encoding="utf-8") as f:
                self._error = f.read()

        return super().error()

    def __del__(self):
        job = Job.load(self.jobid)
        out_file = Path(job.standard_output)
        err_file = Path(job.standard_error)

        out_file.unlink(missing_ok=True)
        err_file.unlink(missing_ok=True)


class SlurmRunner:
    """Runs a JobLib file on a Slurm cluster."""

    def __init__(
        self,
        jobfile: Path | str = JOB_FILE,
        workerstub: Path | str = WORKERSTUB,
    ):
        self.workerstub = Path(workerstub)
        self.jobfile = Path(jobfile)
        self.job_id: int | None = None

    def run(self, function: Runnable, resources: dict) -> RunInformation:
        logging.info("Execute Runner '%s'", self.__class__.__name__)

        file = function.tempfile
        outfile = slurmlib.SLURMLIB_DIR / (file.stem + ".out")
        errfile = slurmlib.SLURMLIB_DIR / (file.stem + ".err")

        desc = JobSubmitDescription(
            name="slurmlib-job",
            standard_output=str(outfile),
            standard_error=str(errfile),
            script=str(self.jobfile),
            script_args=f"1 python {str(self.workerstub)} {str(file)}",
            **resources,
        )

        jobid = desc.submit()
        info = SlurmInformation(jobid)

        return info
