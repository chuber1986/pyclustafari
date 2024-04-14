"""Runnable state classes."""

from enum import StrEnum, auto


class RunState(StrEnum):
    """RunState class."""

    INITIALIZED = auto()
    READY = auto()
    FAILED = auto()
    FINISHED = auto()
