"""Cluster configuration basics."""

from clustafari.config import NodeConfig


class _DummyConfig(NodeConfig):
    def __init__(self, runner_cls: type) -> None:
        super().__init__(runner=runner_cls(), resources={}, jobfile="", workerstub="")

    def __str__(self) -> str:
        return f"{self.__class__.__name__[1:]}({self.resources})"

    def __repr__(self) -> str:
        return str(self)
