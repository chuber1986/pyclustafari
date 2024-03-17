"""Cluster configuration for SlurmRunner."""

from runner.slurm import SlurmRunner

from slurmlib import JOB_FILE, WORKERSTUB

from . import NodeConfig

__all__ = ["SlurmConfig"]


class SlurmConfig(NodeConfig):
    def __init__(self, jobfile=JOB_FILE, workerstub=WORKERSTUB) -> None:
        super().__init__(runner=SlurmRunner(jobfile, workerstub))
