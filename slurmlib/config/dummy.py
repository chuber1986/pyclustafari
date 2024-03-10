"""Cluster configuration basics."""

from . import NodeConfig

__all__ = ["DummyConfig"]


class DummyConfig(NodeConfig):
    def __init__(self) -> None:
        super().__init__(None)
