"""Run configurations package."""

import abc
from dataclasses import dataclass

from runnable import Runner


@dataclass
class NodeConfig(abc.ABC):
    """Node configuration class."""

    def __init__(self, runner: Runner | None = None) -> None:
        self.runner: Runner = runner
