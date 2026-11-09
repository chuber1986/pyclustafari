#!/usr/bin/env python
"""Tests for `Runnable.status` and the status-aware string representation.

Issue #11: expose the worker-side progress (the state file's State values)
on the run handle as a caller-facing `RunStatus`, and include the Slurm job
ID in the string form.
"""

from collections.abc import Callable

import pytest
from clustafari.runner import Runnable
from clustafari.runner.state import RunState, RunStatus
from clustafari.utils import State


def fn1(a, b=2):
    return a + b


def make_ready(fn: Callable = fn1, *args, **kwargs) -> Runnable:
    """Return a Runnable prepared for dispatch (READY, artifact files exist)."""
    r = Runnable(fn, *args, **kwargs)
    r.execute()
    assert r.state == RunState.READY
    return r


def write_state(r: Runnable, state: State) -> None:
    assert r.statefile is not None
    r.statefile.write_text(str(state))


# --- status on a not-yet-dispatched run -------------------------------------


def test_status_initialized_reports_not_started():
    r = Runnable(fn1, 1)
    assert r.status == RunStatus.NOT_STARTED


# --- status mirrors every worker state-file value ---------------------------


@pytest.mark.parametrize(
    ("worker_state", "expected"),
    [
        (State.IDLE, RunStatus.PENDING),
        (State.STARTED, RunStatus.STARTED),
        (State.LOAD_FILE, RunStatus.LOADING),
        (State.RUNNING, RunStatus.RUNNING),
        (State.DUMP_RESULT, RunStatus.DUMPING),
        (State.FINISHED, RunStatus.FINISHED),
        (State.FAILED, RunStatus.FAILED),
    ],
)
def test_status_maps_worker_states(worker_state: State, expected: RunStatus):
    r = make_ready()
    write_state(r, worker_state)
    assert r.status == expected


def test_status_ready_without_state_file_reports_pending():
    # Slurm job submitted, worker not started yet: no/touched-empty state file.
    r = make_ready()
    assert r.status == RunStatus.PENDING


# --- caller terminal states take precedence ---------------------------------


def test_status_after_finish_stays_finished_without_artifacts():
    r = make_ready()
    r.finish(None, 3)
    r._delete_temp_files()
    assert r.state == RunState.FINISHED
    assert r.status == RunStatus.FINISHED


def test_status_after_failure_stays_failed_without_artifacts():
    r = make_ready()
    r.fail("boom")
    r._delete_temp_files()
    assert r.state == RunState.FAILED
    assert r.status == RunStatus.FAILED


def test_status_after_cancel_is_cancelled_despite_state_file():
    r = make_ready()
    write_state(r, State.RUNNING)
    r.cancel()
    r._delete_temp_files()
    assert r.status == RunStatus.CANCELLED


# --- dead backing execution reports failed ----------------------------------


def test_status_dead_worker_reports_failed():
    r = make_ready()
    write_state(r, State.RUNNING)
    r.info = type("DeadInfo", (), {"terminated": staticmethod(lambda: True)})()
    assert r.status == RunStatus.FAILED


def test_status_alive_worker_keeps_reported_state():
    r = make_ready()
    write_state(r, State.RUNNING)
    r.info = type("AliveInfo", (), {"terminated": staticmethod(lambda: False)})()
    assert r.status == RunStatus.RUNNING


# --- string representation ---------------------------------------------------


def test_repr_stays_argument_echo():
    r = make_ready(fn1, 1)
    assert repr(r) == "fn1(1, )"


def test_str_contains_status_without_jobid():
    r = make_ready(fn1, 1)
    write_state(r, State.RUNNING)
    s = str(r)
    assert "fn1" in s and "1" in s
    assert RunStatus.RUNNING.value in s
    assert "job" not in s


def test_str_contains_status_and_jobid():
    r = make_ready(fn1, 1)
    write_state(r, State.RUNNING)
    r.info = type("JobInfo", (), {"terminated": staticmethod(lambda: False), "jobid": 12345})()
    s = str(r)
    assert RunStatus.RUNNING.value in s
    assert "12345" in s
    assert "job" in s
