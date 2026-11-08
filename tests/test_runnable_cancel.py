#!/usr/bin/env python
"""Tests for `Runnable.cancel()` and cancelled-run semantics."""

import pytest
from clustafari.exceptions import CancelledError, RunnableStateError
from clustafari.runner import Runnable
from clustafari.runner.state import RunState


def fn1(a):
    return a + 1


def test_cancel_from_initialized_transitions_directly():
    r = Runnable(fn1, 1)
    r.cancel()
    assert r.state == RunState.CANCELLED
    assert r.is_finished() is True


def test_cancel_from_ready_transitions_to_cancelled():
    r = Runnable(fn1, 1)
    r.execute()
    assert r.state == RunState.READY
    r.cancel()
    assert r.state == RunState.CANCELLED
    assert r.is_finished() is True


def test_cancel_is_idempotent():
    r = Runnable(fn1, 1)
    r.cancel()
    r.cancel()
    assert r.state == RunState.CANCELLED


def test_cancel_from_finished_is_noop():
    r = Runnable(fn1, 1)
    r.execute()
    r.finish(None, 2)
    r.cancel()
    assert r.state == RunState.FINISHED


def test_cancel_from_failed_is_noop():
    r = Runnable(fn1, 1)
    r.execute()
    r.fail("boom")
    r.cancel()
    assert r.state == RunState.FAILED


def test_cancelled_run_get_raises_cancelled_error():
    r = Runnable(fn1, 1)
    r.execute()
    r.cancel()
    with pytest.raises(CancelledError):
        r.get(blocking=True)


def test_cancelled_run_get_nonblocking_raises_cancelled_error():
    r = Runnable(fn1, 1)
    r.execute()
    r.cancel()
    with pytest.raises(CancelledError):
        r.get()


def test_execute_after_cancel_raises():
    r = Runnable(fn1, 1)
    r.cancel()
    with pytest.raises(RunnableStateError):
        r.execute()


def test_cancelled_run_cleans_temp_files():
    r = Runnable(fn1, 1)
    r.execute()
    tempdir = r.tempdir
    assert tempdir is not None and tempdir.exists()
    r.cancel()
    with pytest.raises(CancelledError):
        r.get(blocking=True)
    assert not tempdir.exists()


def test_cancel_asks_info_to_stop_backing_execution():
    r = Runnable(fn1, 1)
    r.execute()
    stopped = []
    r.info = type("SpyInfo", (), {"cancel": staticmethod(lambda: stopped.append(1))})()
    r.cancel()
    assert stopped == [1]
    assert r.state == RunState.CANCELLED
