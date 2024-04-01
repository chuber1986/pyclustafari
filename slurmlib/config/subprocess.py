"""Cluster configuration for SubprocessRunner."""

from pathlib import Path

from slurmlib import WORKERSTUB

from . import NodeConfig

__all__ = ["SubprocessConfig"]


class SubprocessConfig(NodeConfig):
    def __init__(self, workerstub: Path | str = WORKERSTUB) -> None:
        super().__init__(jobfile="", workerstub=workerstub)
