"""Cluster configuration basics."""

from clustafari.config import NodeConfig


class _DummyConfig(NodeConfig):
    def __init__(self, runner_cls: type) -> None:
        super().__init__(runner=runner_cls(), resources={}, jobfile="", workerstub="")
