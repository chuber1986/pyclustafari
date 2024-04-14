"""Strategy for executing dumped JobLib files using slurm."""

from pathlib import Path

from pyslurm import Job

from slurmlib.runner import RunInformation

COMMAND_TEMPLATE = r"python {} {}"


class SlurmInformation(RunInformation):
    """Provides information about executed slurm jobs."""

    def __init__(self, jobid: int):
        super().__init__()
        self.jobid: int = jobid

    def debug_info(self):
        job = Job.load(self.jobid)
        return job.to_dict()

    @RunInformation.output.getter  # type: ignore[attr-defined]
    def output_(self):
        job = Job.load(self.jobid)
        out_file = Path(job.standard_output)

        if out_file.exists():
            with out_file.open("r", encoding="utf-8") as f:
                self._output = f.read()

        return super().output()

    @RunInformation.error.getter  # type: ignore[attr-defined]
    def error_(self):
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


if __name__ == "__main__":
    SlurmInformation(123)
