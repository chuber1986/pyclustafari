"Cluster configuration classes."
import abc
from dataclasses import dataclass

from runnable import Runner
from runner import SlurmRunner, SubprocessRunner

from slurmlib import WORKERSTUB


@dataclass
class NodeConfig(abc.ABC):
    """Node configuration class."""

    def __init__(self, runner: Runner | None = None) -> None:
        self.runner: Runner = runner


class DummyConfig(NodeConfig):
    def __init__(self) -> None:
        super().__init__(None)


class SubprocessConfig(NodeConfig):
    def __init__(self, workerstub=WORKERSTUB) -> None:
        super().__init__(runner=SubprocessRunner(workerstub))


class SlurmConfig(NodeConfig):
    def __init__(self, workerstub=WORKERSTUB) -> None:
        super().__init__(runner=SlurmRunner(workerstub))
