#!/usr/bin/env python
"""Tests for `clustafari.runner` internals (Runnable, state machine, helpers)."""

import pickle
from functools import partial

import joblib
import pytest

from clustafari.exceptions import RunnableStateError
from clustafari.runner import Runnable
from clustafari.runner.runnable import _get_function_name, _get_partial_arguments
from clustafari.runner.state import RunState
from clustafari.utils import State


def fn1(a, b=2):
    return a + b


def test_get_function_name_plain_and_partial():
    assert _get_function_name(fn1) == "fn1"
    assert _get_function_name(partial(fn1, 1)) == "fn1"


def test_get_partial_arguments():
    assert _get_partial_arguments(fn1) == ((), {})
    assert _get_partial_arguments(partial(fn1, 1, b=3)) == ((1,), {"b": 3})


def test_runnable_state_initial():
    r = Runnable(fn1, 1)
    assert r.state == RunState.INITIALIZED
    assert r.is_finished() is False


def test_runnable_execute_twice_raises():
    r = Runnable(fn1, 1)
    r.execute()
    with pytest.raises(RunnableStateError, match="initialized"):
        r.execute()


def test_runnable_finish_from_initialized_raises():
    r = Runnable(fn1, 1)
    with pytest.raises(RunnableStateError, match="READY"):
        r.finish(None, 1)


def test_runnable_finish_ready_to_finished():
    r = Runnable(fn1, 1)
    r.execute()
    assert r.state == RunState.READY
    r.finish(None, 3)
    assert r.state == RunState.FINISHED
    assert r.result == 3
    assert r.is_finished() is True


def test_runnable_get_before_start_raises():
    r = Runnable(fn1, 1)
    with pytest.raises(RunnableStateError, match="not started"):
        r.get(blocking=True)


def test_runnable_repr_merges_partial_arguments():
    p = partial(fn1, 1, b=5)
    r = Runnable(p, 2, c=7)
    assert "fn1(" in repr(r)
    assert "1" in repr(r) and "2" in repr(r)
    assert "b=5" in repr(r) and "c=7" in repr(r)


def test_runnable_get_hash_changes_with_timestamp():
    r = Runnable(fn1, 1)
    h1 = r._get_hash()
    r._timestamp = 123456789
    assert r._get_hash() != h1


def test_read_result_files_handles_corrupt_result_file(tmp_path):
    """A corrupt/missing .res file yields a (None, None) result, not an exception."""
    r = Runnable(fn1, 1)
    r.execute()

    jobfile = tmp_path / "fn1.pyjob"
    jobfile.touch()
    r.tempdir = tmp_path
    r.tempfile = jobfile
    r.resultfile = jobfile.with_suffix(".res")
    r.outputfile = jobfile.with_suffix(".out")
    r.errorfile = jobfile.with_suffix(".err")
    r.logfile = jobfile.with_suffix(".log")
    r.statefile = jobfile.with_suffix(".state")

    # Corrupt result file: a truncated pickle (valid header, cut-off body)
    # raises EOFError on load, which _read_job_file treats as no result.
    data = pickle.dumps((None, 1))
    r.resultfile.write_bytes(data[: len(data) // 2])
    r.statefile.write_text(str(State.FAILED))

    r._read_result_files()
    assert r._result is None
    assert r._object is None
    # State file missing -> run reported as failed.
    assert r.state == RunState.FAILED


def test_read_result_files_finished_state_sets_finished(tmp_path):
    r = Runnable(fn1, 1)
    r.execute()

    jobfile = tmp_path / "fn1.pyjob"
    r.tempdir = tmp_path
    r.tempfile = jobfile
    r.resultfile = jobfile.with_suffix(".res")
    r.outputfile = jobfile.with_suffix(".out")
    r.errorfile = jobfile.with_suffix(".err")
    r.logfile = jobfile.with_suffix(".log")
    r.statefile = jobfile.with_suffix(".state")

    joblib.dump((None, 42), r.resultfile)
    r.statefile.write_text(str(State.FINISHED))
    r.outputfile.write_text("out\n")
    r.logfile.write_text("log line\n")

    r._read_result_files()
    assert r._result == 42
    assert r.state == RunState.FINISHED
    assert r.info.output == "out\n"
    assert r.info.log == "log line\n"
    # Success path cleaned up the temp files.
    assert not r.tempdir.exists()


def test_delete_temp_files_noop_without_tempdir():
    r = Runnable(fn1, 1)
    r._delete_temp_files()  # must not raise


def test_fail_from_initialized_records_error():
    r = Runnable(fn1, 1)
    r.fail("boom")
    assert r.state == RunState.FAILED
    assert r.info.error == "boom"
    assert r.is_finished() is True
