#!/usr/bin/env python
"""Tests for `SlurmInformation` (pyslurm Job access mocked at the module boundary)."""

import gc

import pyslurm
import pytest
from clustafari.runner.slurm.info import SlurmInformation


class FakeJob:
    def __init__(self, state="COMPLETED", exit_code=0, exit_code_signal=0, std_out="/tmp/o.out", std_err="/tmp/e.err"):
        self.state = state
        self.exit_code = exit_code
        self.exit_code_signal = exit_code_signal
        self.standard_output = std_out
        self.standard_error = std_err
        self._dict = {"state": state, "exit_code": exit_code}

    def to_dict(self):
        return self._dict


@pytest.fixture
def fake_pyslurm(monkeypatch):
    class FakeJobNS:
        """`pyslurm.Job` stand-in: `set(results)` feeds a sequence of per-call
        results; a single result or exception is repeated for every call."""

        def __init__(self):
            self.results: list = []
            self.calls = 0

        def load(self, job_id):
            self.calls += 1
            if self.results:
                i = min(self.calls - 1, len(self.results) - 1)
                result = self.results[i]
            else:
                result = None
            if isinstance(result, Exception):
                raise result
            return result

        def set(self, result):
            if isinstance(result, (list, tuple)) and result and not isinstance(result[0], Exception):
                self.results = list(result)
            else:
                self.results = [result]

    ns = FakeJobNS()
    monkeypatch.setattr(pyslurm, "Job", ns)
    return ns


def test_terminated_false_for_pending_job(fake_pyslurm):
    fake_pyslurm.set(FakeJob(state="PENDING"))
    info = SlurmInformation(123)
    assert info.terminated() is False


def test_terminated_true_for_failed_job_with_nonzero_exit(fake_pyslurm):
    fake_pyslurm.set(FakeJob(state="FAILED", exit_code=1))
    info = SlurmInformation(123)
    assert info.terminated() is True


def test_terminated_true_for_signal_exit(fake_pyslurm):
    fake_pyslurm.set(FakeJob(state="OUT_OF_MEMORY", exit_code=0, exit_code_signal=9))
    info = SlurmInformation(123)
    assert info.terminated() is True


def test_terminated_false_for_clean_completed_job(fake_pyslurm):
    fake_pyslurm.set(FakeJob(state="COMPLETED", exit_code=0))
    info = SlurmInformation(123)
    assert info.terminated() is False


def test_terminated_true_when_job_id_no_longer_tracked(fake_pyslurm):
    fake_pyslurm.set([FakeJob(state="PENDING"), pyslurm.RPCError(2017, "no such job")])
    info = SlurmInformation(123)
    assert info.terminated() is True


def test_terminated_false_on_transient_rpc_error(fake_pyslurm):
    fake_pyslurm.set([FakeJob(state="PENDING"), pyslurm.RPCError(2000, "slurmctld unreachable")])
    info = SlurmInformation(123)
    assert info.terminated() is False


def test_terminated_ignores_unexpected_errors(fake_pyslurm):
    fake_pyslurm.set([FakeJob(state="PENDING"), RuntimeError("boom")])
    info = SlurmInformation(123)
    assert info.terminated() is False


def test_terminated_result_is_cached_within_check_interval(fake_pyslurm):
    fake_pyslurm.set(FakeJob(state="PENDING"))
    info = SlurmInformation(123)
    assert info.terminated() is False
    calls_after_first_check = fake_pyslurm.calls
    assert info.terminated() is False
    # Second check within the interval must reuse the cached result.
    assert fake_pyslurm.calls == calls_after_first_check


def test_debug_info_returns_job_dict(fake_pyslurm):
    fake_pyslurm.set(FakeJob(state="RUNNING"))
    info = SlurmInformation(123)
    assert info.debug_info() == {"state": "RUNNING", "exit_code": 0}


def test_init_records_files(fake_pyslurm):
    from pathlib import Path

    fake_pyslurm.set(FakeJob(std_out="/tmp/x.out", std_err="/tmp/x.err"))
    info = SlurmInformation(123)
    assert info.out_file == Path("/tmp/x.out")
    assert info.err_file == Path("/tmp/x.err")
    assert info.jobid == 123


def test_del_unlinks_output_and_error_files(tmp_path, fake_pyslurm):
    out = tmp_path / "job.out"
    err = tmp_path / "job.err"
    out.write_text("o")
    err.write_text("e")
    fake_pyslurm.set(FakeJob(std_out=str(out), std_err=str(err)))

    info = SlurmInformation(123)
    assert out.exists() and err.exists()
    del info
    gc.collect()
    assert not out.exists() and not err.exists()
