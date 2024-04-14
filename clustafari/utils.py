""""Utility functions for PyClustafari."""

import sys
from contextlib import contextmanager
from enum import StrEnum, auto
from pathlib import Path


@contextmanager
def redirect_io(out=sys.stdout, err=sys.stderr, inp=sys.stdin):
    tmp_out = sys.stdout
    tmp_err = sys.stderr
    tmp_in = sys.stdin

    sys.stdout = out
    sys.stderr = err
    sys.stdin = inp
    try:
        yield
    finally:
        sys.stdout = tmp_out
        sys.stderr = tmp_err
        sys.stdin = tmp_in


class State(StrEnum):
    """State of workerstub."""

    IDLE = auto()
    STARTED = auto()
    LOAD_FILE = auto()
    RUNNING = auto()
    FAILED = auto()
    DUMP_RESULT = auto()
    FINISHED = auto()

    @classmethod
    def _missing_(cls, value):
        return cls.IDLE


def get_result_file(file: Path) -> Path:
    return file.with_suffix(".res")


def get_output_file(file: Path) -> Path:
    return file.with_suffix(".out")


def get_error_file(file: Path) -> Path:
    return file.with_suffix(".err")


def get_log_file(file: Path) -> Path:
    return file.with_suffix(".log")


def get_state_file(file: Path) -> Path:
    return file.with_suffix(".state")
