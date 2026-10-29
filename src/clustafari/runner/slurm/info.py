"""Strategy for executing dumped JobLib files using slurm."""

from pathlib import Path

from clustafari.runner import RunInformation


class SlurmInformation(RunInformation):
    """Provides information about executed slurm jobs."""

    def __init__(self, jobid: int) -> None:
        """Initialize Slurm Information with job ID."""
        super().__init__()
        self.jobid: int = jobid

        from pyslurm import Job

        job = Job.load(self.jobid)
        self.out_file = Path(job.standard_output)
        self.err_file = Path(job.standard_error)

    def debug_info(self) -> dict:
        """Get debug information of the job."""
        from pyslurm import Job

        job = Job.load(self.jobid)
        return job.to_dict()

    def __del__(self) -> None:
        """Clean up output and error files on deletion."""
        out_file = getattr(self, "out_file", None)
        err_file = getattr(self, "err_file", None)

        if out_file is not None:
            out_file.unlink(missing_ok=True)

        if err_file is not None:
            err_file.unlink(missing_ok=True)
