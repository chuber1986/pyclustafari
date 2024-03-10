"""Cluster configuration for SubprocessRunner."""

from runner.subprocess import SubprocessRunner

from slurmlib import WORKERSTUB

from .config import NodeConfig

__all__ = ["SubprocessConfig"]


class SubprocessConfig(NodeConfig):
    def __init__(self, workerstub=WORKERSTUB) -> None:
        super().__init__(runner=SubprocessRunner(workerstub))
