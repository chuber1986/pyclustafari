"""Cluster configuration for SubprocessRunner."""

from pathlib import Path

from slurmlib.config import NodeConfig
from slurmlib.paths import WORKERSTUB


class _SubprocessConfig(NodeConfig):
    def __init__(self, runner_cls: type, workerstub: Path | str = WORKERSTUB) -> None:
        super().__init__(
            runner=runner_cls(self), resources={}, jobfile="", workerstub=workerstub
        )
