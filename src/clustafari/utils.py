"""Utility functions for PyClustafari."""

import contextlib
import json
import logging
import sys
from collections.abc import Generator
from contextlib import contextmanager
from enum import StrEnum, auto
from pathlib import Path
from typing import Any, TextIO

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
        """Return default state if missing."""
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


def get_meta_file(file: Path) -> Path:
    """Return path to the dispatch-time metadata file for a given job file."""
    return file.parent / "meta.json"


_META_TMP_SUFFIX = ".meta-tmp"


def _read_meta_path(meta_file: Path) -> dict[str, Any]:
    """Read a meta.json path, tolerantly (empty dict on any failure)."""
    try:
        with meta_file.open("r") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def read_meta(file: Path) -> dict[str, Any]:
    """Read the run metadata for a given job file, tolerantly.

    Returns the parsed ``meta.json`` content, or an empty dict when the
    file is absent, unreadable, or corrupt — metadata is advisory for the
    run itself and must never break dispatch or retrieval.
    """
    return _read_meta_path(get_meta_file(file))


def write_meta(file: Path, meta: dict[str, Any]) -> None:
    """Write the run metadata for a given job file, atomically and best-effort.

    Merges ``meta`` into the existing metadata and publishes via a temp-file
    rename in the same directory. Never raises: an unwritable metadata file
    must not prevent dispatch (the protocol treats metadata as advisory).
    """
    merged = {**read_meta(file), **meta}
    tmp = get_meta_file(file).with_suffix(_META_TMP_SUFFIX)
    try:
        with tmp.open("w") as f:
            json.dump(merged, f)
        tmp.replace(get_meta_file(file))
    except OSError:
        logger.warning("Could not write run metadata to %s.", get_meta_file(file), exc_info=True)
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
