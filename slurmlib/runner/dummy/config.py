"""Cluster configuration basics."""

from slurmlib.config import NodeConfig


class _DummyConfig(NodeConfig):
    def __init__(self, runner_cls: type) -> None:
        super().__init__(runner=runner_cls(), resources={}, jobfile="", workerstub="")

    def __str__(self):
        return f"{self.__class__.__name__[1:]}({self.resources})"

    def __repr__(self):
        return str(self)
