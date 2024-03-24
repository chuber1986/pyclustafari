"""Cluster configuration for SlurmRunner."""

from pathlib import Path

from resources import Resources
from runner.slurm import SlurmRunner

from slurmlib import JOB_FILE, WORKERSTUB

from . import NodeConfig

__all__ = ["SlurmConfig"]


class SlurmConfig(NodeConfig):
    def __init__(
        self,
        resources: Resources = Resources([]),
        jobfile: Path = JOB_FILE,
        workerstub: Path = WORKERSTUB,
    ) -> None:
        super().__init__(runner=SlurmRunner(resources, jobfile, workerstub))
