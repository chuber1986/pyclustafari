"""Cluster configuration for SlurmRunner."""

from slurmlib import WORKERSTUB

from ..runner import SlurmRunner
from .config import NodeConfig


class SlurmConfig(NodeConfig):
    def __init__(self, workerstub=WORKERSTUB) -> None:
        super().__init__(runner=SlurmRunner(workerstub))
