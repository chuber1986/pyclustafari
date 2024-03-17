"""Strategy for executing dumped JobLib files using slurm."""

import logging
from pathlib import Path

import pyslurm
from runnable import RunInformation, Runnable

COMMAND_TEMPLATE = r"python {} {}"

__all__ = ["SlurmRunner"]


class SlurmInformation(RunInformation):
    pass


class SlurmRunner:
    """Runs a JobLib file on a Slurm cluster."""

    def __init__(self, jobfile: Path, workerstub: Path):
        self.workerstub = workerstub
        self.jobfile = jobfile

    def run(self, function: Runnable) -> RunInformation:
        logging.info("Execute Runner '%s'", self.__class__.__name__)
        info = SlurmInformation()

        file = function.tempfile
        desc = pyslurm.JobSubmitDescription(
            name="slurmlib-job",
            script=f"{str(self.jobfile)} {str(self.workerstub)} {file}",
        )

        desc.submit()

        return info
