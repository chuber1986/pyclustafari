"""Utility functions for PyClustafari."""

import logging
import sys
from collections.abc import Generator
from contextlib import contextmanager
from enum import StrEnum, auto
from pathlib import Path
from typing import TextIO

logger = logging.getLogger(__name__)


@contextmanager
def redirect_io(
    out: TextIO = sys.stdout, err: TextIO = sys.stderr, inp: TextIO = sys.stdin
) -> Generator[None, None, None]:
    """Redirect standard input/output/error streams."""
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
    def _missing_(cls, value: object) -> "State":
        """Retrun default state if missing."""
        logger.warning("Unknown state '%s', defaulting to IDLE.", value)
        return cls.IDLE


def get_result_file(file: Path) -> Path:
    """Return path to result file for a given job file."""
    return file.with_suffix(".res")


def get_output_file(file: Path) -> Path:
    """Return path to output file for a given job file."""
    return file.with_suffix(".out")


def get_error_file(file: Path) -> Path:
    """Return path to error file for a given job file."""
    return file.with_suffix(".err")


def get_log_file(file: Path) -> Path:
    """Return path to log file for a given job file."""
    return file.with_suffix(".log")


def get_state_file(file: Path) -> Path:
    """Return path to state file for a given job file."""
    return file.with_suffix(".state")
