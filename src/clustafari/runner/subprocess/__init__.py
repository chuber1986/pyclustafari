"""Export SubprocessRunner."""

from typing import Any

from .config import _SubprocessConfig
from .runner import SubprocessRunner


class SubprocessConfig(_SubprocessConfig):
    """Configuration for SubprocessRunner."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize SubprocessConfig with SubprocessRunner."""
        super().__init__(runner_cls=SubprocessRunner, **kwargs)
