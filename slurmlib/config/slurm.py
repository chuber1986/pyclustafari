"""Cluster configuration for SlurmRunner."""

from runner.slurm import SlurmRunner

from slurmlib import WORKERSTUB

from .config import NodeConfig

__all__ = ["SlurmConfig"]


class SlurmConfig(NodeConfig):
    def __init__(self, workerstub=WORKERSTUB) -> None:
        super().__init__(runner=SlurmRunner(workerstub))
