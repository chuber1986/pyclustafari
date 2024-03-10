"""Cluster configuration basics."""

import abc
from dataclasses import dataclass

from runnable import Runner

__all__ = ["NodeConfig", "DummyConfig"]


@dataclass
class NodeConfig(abc.ABC):
    """Node configuration class."""

    def __init__(self, runner: Runner | None = None) -> None:
        self.runner: Runner = runner


class DummyConfig(NodeConfig):
    def __init__(self) -> None:
        super().__init__(None)
