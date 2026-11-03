#!/usr/bin/env python
"""Tests for `clustafari.utils` and path helpers."""

import io
from pathlib import Path

import pytest

from clustafari.utils import State, get_error_file, get_log_file, get_output_file, get_result_file, get_state_file, redirect_io


def test_redirect_io_captures_streams():
    out = io.StringIO()
    err = io.StringIO()
    with redirect_io(out=out, err=err):
        print("to out")
        print("to err", file=__import__("sys").stderr)
    assert out.getvalue() == "to out\n"
    assert err.getvalue() == "to err\n"


def test_redirect_io_restores_streams_after_exception():
    import sys

    real_out = sys.stdout
    with pytest.raises(RuntimeError, match="boom"):
        with redirect_io(out=io.StringIO(), err=io.StringIO()):
            raise RuntimeError("boom")
    assert sys.stdout is real_out


@pytest.mark.parametrize(
    "helper, suffix",
    [
        (get_result_file, ".res"),
        (get_output_file, ".out"),
        (get_error_file, ".err"),
        (get_log_file, ".log"),
        (get_state_file, ".state"),
    ],
)
def test_file_helpers_replace_suffix(helper, suffix):
    assert helper(Path("job.pyjob")) == Path(f"job{suffix}")


def test_state_unknown_value_defaults_to_idle():
    assert State("bogus") is State.IDLE


@pytest.mark.parametrize("name", ["idle", "started", "load_file", "running", "failed", "dump_result", "finished"])
def test_state_parses_lowercase_names(name):
    assert State(name) is State[name.upper()]
