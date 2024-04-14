"""Cluster configuration for SubprocessRunner."""

from pathlib import Path

from slurmlib.config import NodeConfig
from slurmlib.paths import WORKERSTUB


class _SubprocessConfig(NodeConfig):
    """Configuration for SubprocessRunner."""

    def __init__(self, runner_cls: type, workerstub: Path | str = WORKERSTUB) -> None:
        super().__init__(
            runner=runner_cls(self), resources={}, jobfile="", workerstub=workerstub
        )

    def __str__(self):
        return f"{self.__class__.__name__[1:]}({self.resources})"

    def __repr__(self):
        return str(self)
