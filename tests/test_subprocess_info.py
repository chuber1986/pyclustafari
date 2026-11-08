#!/usr/bin/env python
"""Tests for `SubprocessInformation` (worker process handle and dead-worker detection)."""

import subprocess
import time

import pytest
from clustafari.runner.subprocess.info import SubprocessInformation


def spawn(*, exit_code: int | None = None, sleep: float | None = None) -> subprocess.Popen:
    """Spawn a tiny worker: either exits immediately with `exit_code` or sleeps."""
    if exit_code is not None:
        return subprocess.Popen(["sh", "-c", f"exit {exit_code}"])
    return subprocess.Popen(["sh", "-c", f"sleep {sleep}"])


def test_terminated_false_while_worker_alive():
    info = SubprocessInformation(spawn(sleep=30))
    try:
        assert info.terminated() is False
    finally:
        info.proc.kill()
        info.proc.wait()


def test_terminated_true_once_worker_exited():
    info = SubprocessInformation(spawn(exit_code=0))
    info.proc.wait(timeout=10)
    assert info.terminated() is True


def test_proc_exposes_handle():
    proc = spawn(exit_code=0)
    info = SubprocessInformation(proc)
    info.proc.wait(timeout=10)
    assert info.proc is proc


def test_termination_error_message_includes_exit_code():
    info = SubprocessInformation(spawn(exit_code=137))
    info.proc.wait(timeout=10)
    message = info.termination_error_message()
    assert "137" in message


def test_termination_error_message_includes_stderr():
    info = SubprocessInformation(spawn(exit_code=1))
    info.proc.wait(timeout=10)
    info.error = "worker crashed\n"
    message = info.termination_error_message()
    assert "worker crashed" in message


@pytest.mark.parametrize("n", [1])
def test_wait_reaps_worker(n):
    info = SubprocessInformation(spawn(exit_code=0))
    time.sleep(0.2)
    assert info.proc.poll() is not None
    info.proc.wait(timeout=10)
