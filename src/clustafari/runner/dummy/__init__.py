"""Export DummyRunner."""

from .config import _DummyConfig
from .runner import DummyRunner


class DummyConfig(_DummyConfig):
    """Configuration for DummyRunners."""

    def __init__(self) -> None:
        """Initialize DummyConfig with DummyRunner."""
        super().__init__(DummyRunner)
