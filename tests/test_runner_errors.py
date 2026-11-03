#!/usr/bin/env python
"""Tests for runner error paths that do not require a Slurm cluster."""

import pytest

from clustafari import ClusterContext, SlurmConfig
from clustafari.exceptions import StateError
from clustafari.runner import RunInformation
from clustafari.runner.runnable import Runnable
from clustafari.runner.slurm import SlurmRunner
from clustafari.runner.subprocess import SubprocessRunner
from clustafari.runner.subprocess.config import _SubprocessConfig
from clustafari.runner.state import RunState
from clustafari.utils import State


def fn0():
    return 1


class _FakeInfo(RunInformation):
    def __init__(self, terminated: bool):
        super().__init__()
        self._terminated = terminated

    def terminated(self):
        return self._terminated


def _ready_run_with_fake_info(tmp_path, info, err_content=""):
    r = Runnable(fn0)
    r.execute()
    jobfile = tmp_path / "fn0.pyjob"
    r.tempdir = tmp_path
    r.tempfile = jobfile
    r.resultfile = jobfile.with_suffix(".res")
    r.outputfile = jobfile.with_suffix(".out")
    r.errorfile = jobfile.with_suffix(".err")
    r.logfile = jobfile.with_suffix(".log")
    r.statefile = jobfile.with_suffix(".state")
    r.info = info
    if err_content:
        r.errorfile.write_text(err_content)
    return r


def test_is_finished_true_when_job_terminated_without_state_file(tmp_path):
    r = _ready_run_with_fake_info(tmp_path, _FakeInfo(terminated=True), err_content="oom kill")
    assert r.is_finished() is True
    assert r.state == RunState.FAILED
    assert "terminated" in r.info.error
    assert "oom kill" in r.info.error


def test_is_finished_terminated_without_stderr_uses_generic_message(tmp_path):
    r = _ready_run_with_fake_info(tmp_path, _FakeInfo(terminated=True))
    assert r.is_finished() is True
    assert "worker died before reporting its state" in r.info.error


def test_is_finished_false_when_state_file_says_running(tmp_path):
    # The state file says the worker is still running, so a non-terminated
    # backing job keeps the run unfinished.
    r = _ready_run_with_fake_info(tmp_path, _FakeInfo(terminated=False))
    r.statefile.write_text(str(State.RUNNING))
    assert r.is_finished() is False


def test_is_finished_true_when_state_file_says_failed(tmp_path):
    r = _ready_run_with_fake_info(tmp_path, _FakeInfo(terminated=False))
    r.statefile.write_text(str(State.FAILED))
    assert r.is_finished() is True


def test_is_finished_true_when_state_file_says_finished(tmp_path):
    r = _ready_run_with_fake_info(tmp_path, _FakeInfo(terminated=False))
    r.statefile.write_text(str(State.FINISHED))
    assert r.is_finished() is True


def test_slurm_submit_failure_fails_run(monkeypatch):
    class _FakeJobSubmitDescription:
        def __init__(self, *args, **kwargs):
            pass

        def submit(self):
            raise RuntimeError("submit exploded")

    import pyslurm as _pyslurm

    # SlurmRunner._run does `from pyslurm import JobSubmitDescription` at call
    # time, so patching the module attribute takes effect.
    monkeypatch.setattr(_pyslurm, "JobSubmitDescription", _FakeJobSubmitDescription)

    with ClusterContext(SlurmConfig()) as ctx:
        run = ctx.apply_async(fn0)
        assert run.state == RunState.FAILED
        with pytest.raises(StateError, match="submit exploded"):
            run.get(blocking=True)
        assert run.tempdir is None or not run.tempdir.exists()


def test_subprocess_runner_popen_failure_fails_run(monkeypatch):
    import clustafari.runner.subprocess.runner as runner_mod

    def _popen(*args, **kwargs):
        raise OSError("fork failed")

    monkeypatch.setattr(runner_mod.subprocess, "Popen", _popen)

    cfg = _SubprocessConfig(SubprocessRunner, workerstub="ignored")
    runner = SubprocessRunner(cfg)
    run = runner.apply_async(fn0)
    assert run.state == RunState.FAILED
    with pytest.raises(StateError, match="fork failed"):
        run.get(blocking=True)
    assert run.tempdir is None or not run.tempdir.exists()
