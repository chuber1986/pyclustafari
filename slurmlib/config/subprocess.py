"""Cluster configuration for SubprocessRunner."""

from slurmlib import WORKERSTUB

from ..runner import SubprocessRunner
from .config import NodeConfig


class SubprocessConfig(NodeConfig):
    def __init__(self, workerstub=WORKERSTUB) -> None:
        super().__init__(runner=SubprocessRunner(workerstub))
