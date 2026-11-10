#!/usr/bin/env python
"""Tests for the dispatch-time metadata file and the attach reconstruction path (issue #18)."""

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from clustafari import ClusterContext, DummyConfig, attach, gc, list_runs, paths
from clustafari.runner import RunInformation, Runnable
from clustafari.runner.state import RunState
from clustafari.utils import State, get_log_file, get_state_file

# Caller-side prep writes the job file + advisory meta.json (this module's
# subject); the subprocess/dummy worker adds state/out/err/log/res.
DUMMY_FILES = {"fn1.joblib", "meta.json"}


def fn1(a):
    return a + 1


def boom():
    raise ValueError("kaboom")


@pytest.fixture(autouse=True)
def _fresh_path_cache():
    paths.reset_path_cache()
    yield
    paths.reset_path_cache()


@pytest.fixture
def root(tmp_path, monkeypatch):
    """Isolated artifacts root + HOME so tests never touch ~/.clustafari."""
    monkeypatch.delenv("CLUSTAFARI_ARTIFACT_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path / "scratch"


def _dispatch_dummy(ctx) -> Runnable:
    run = ctx.apply_async(fn1, 1)
    assert run.tempfile is not None
    return run


# --- metadata file (task 1.1/1.2/1.3) ---


def test_meta_json_written_at_dispatch(root):
    with ClusterContext(DummyConfig(), artifacts_dir=root) as ctx:
        run = _dispatch_dummy(ctx)
        assert {p.name for p in run.tempdir.iterdir()} == DUMMY_FILES
        meta = json.loads((run.tempdir / "meta.json").read_text())
        assert meta["function"] == "fn1"
        assert meta["backend"] == "dummy"
        assert meta["dispatched_at"].endswith("+00:00")  # UTC ISO-8601


def test_meta_json_survives_across_backends(root, monkeypatch):
    from clustafari import SubprocessConfig

    with ClusterContext(SubprocessConfig(), artifacts_dir=root) as ctx:
        run = _dispatch_dummy(ctx)
        assert run.get(blocking=True) == 2
        # After a successful get() the run dir is gone; re-dispatch to assert
        # the subprocess backend records its kind before the worker runs.
        run2 = _dispatch_dummy(ctx)
        meta = json.loads((run2.tempdir / "meta.json").read_text())
        assert meta["backend"] == "subprocess"
        assert run2.get(blocking=True) == 2


def test_meta_json_absent_leaves_run_unaffected(root):
    """Advisory rule: without meta.json dispatch and retrieval work unchanged."""
    with ClusterContext(DummyConfig(), artifacts_dir=root) as ctx:
        run = _dispatch_dummy(ctx)
        (run.tempdir / "meta.json").unlink()
        # The dummy backend executes inline: the run is already terminal.
        assert run.state == RunState.FINISHED
        run2 = ctx.apply_async(fn1, 41)
        assert run2.get(blocking=True) == 42


def test_meta_json_corrupt_leaves_retrieval_unaffected(root):
    with ClusterContext(DummyConfig(), artifacts_dir=root) as ctx:
        run = _dispatch_dummy(ctx)
        (run.tempdir / "meta.json").write_text("{not json")
        # Reconstruction + retrieval (dummy worker never wrote a state file;
        # state file missing reads as IDLE → not finished → get() raises the
        # state error, not a JSON/parse error).
        attached = Runnable.from_run_dir(run.tempdir)
        with pytest.raises(Exception, match="not finished"):
            attached.get(blocking=False)


def test_meta_write_failure_does_not_break_dispatch(root):
    with ClusterContext(DummyConfig(), artifacts_dir=root) as ctx:
        run = _dispatch_dummy(ctx)
        # Simulate an unwritable meta.json: a directory at that path.
        (run.tempdir / "meta.json").unlink()
        (run.tempdir / "meta.json").mkdir()
        run2 = ctx.apply_async(fn1, 41)
        assert run2.state == RunState.FINISHED
        assert run2.get(blocking=True) == 42


# --- reconstruction / attach (task 2.1/2.2/2.3) ---


def _make_artifacts(root: Path, state: State, result=None, backend="slurm", jobid=None, dispatched_at=None):
    """Hand-roll a run directory exactly as dispatch + worker would leave it."""
    rundir = root / f"fn1-{uuid4().hex}"
    rundir.mkdir(parents=True)
    jobfile = rundir / "fn1.joblib"
    jobfile.write_bytes(b"stub")  # never unpickled on the attach path
    get_state_file(jobfile).write_text(str(state))
    meta = {
        "function": "fn1",
        "dispatched_at": dispatched_at or datetime.now(UTC).isoformat(),
        "backend": backend,
    }
    if jobid is not None:
        meta["jobid"] = jobid
    (rundir / "meta.json").write_text(json.dumps(meta))
    if result is not None:
        import joblib

        joblib.dump((None, result), jobfile.with_suffix(".res"))
        jobfile.with_suffix(".out").write_text("out text\n")
        jobfile.with_suffix(".err").write_text("")
        get_log_file(jobfile).write_text("log line\n")
    return rundir, jobfile


def test_from_run_dir_rebuilds_retrieval_ready_state(root):
    rundir, _ = _make_artifacts(root, State.FINISHED, result=7)
    attached = Runnable.from_run_dir(rundir)
    assert attached.state == RunState.READY
    assert attached.backend == "slurm"
    assert attached.name == "fn1"
    assert attached.get_function_name() == "fn1"
    assert attached.tempdir == rundir
    assert attached.statefile == get_state_file(rundir / "fn1.joblib")


def test_from_run_dir_get_returns_result_and_cleans(root):
    rundir, _ = _make_artifacts(root, State.FINISHED, result=7)
    attached = Runnable.from_run_dir(rundir)
    assert attached.get(blocking=True) == 7
    assert not rundir.exists()


def test_from_run_dir_get_raises_with_diagnostics(root):
    rundir, jobfile = _make_artifacts(root, State.FAILED)
    get_log_file(jobfile).write_text("the log line\n")
    jobfile.with_suffix(".err").write_text("the error line\n")
    attached = Runnable.from_run_dir(rundir)
    with pytest.raises(Exception, match="the log line"):
        attached.get(blocking=True)
    assert not rundir.exists()


def test_from_run_dir_name_without_meta(root):
    rundir, _ = _make_artifacts(root, State.FINISHED, result=7)
    (rundir / "meta.json").unlink()
    attached = Runnable.from_run_dir(rundir)
    # No metadata and no pickled function: identified by the run dir name.
    assert attached.name == rundir.name
    assert repr(attached).startswith(rundir.name)


def test_from_run_dir_repr_and_str(root, monkeypatch):
    import pyslurm

    class FakeJob:
        def __init__(self):
            self.state = "RUNNING"
            self.exit_code = 0
            self.exit_code_signal = 0
            self.standard_output = "/tmp/o.out"
            self.standard_error = "/tmp/e.err"

    class FakeJobNS:
        def load(self, job_id):
            return FakeJob()

    monkeypatch.setattr(pyslurm, "Job", FakeJobNS)

    rundir, _ = _make_artifacts(root, State.RUNNING, backend="slurm", jobid=4711)
    attached = Runnable.from_run_dir(rundir)
    assert "fn1" in repr(attached)
    s = str(attached)
    assert "running" in s
    assert "4711" in s  # recorded job id surfaces in the status line


def test_from_run_dir_missing_jobfile_raises(root):
    rundir = root / "fn1-deadbeef"
    rundir.mkdir(parents=True)
    with pytest.raises(ValueError, match="job file"):
        Runnable.from_run_dir(rundir)


def test_attached_del_keeps_artifacts(root):
    """Dropping an attached handle must not destroy recovered artifacts."""
    import gc

    rundir, _ = _make_artifacts(root, State.RUNNING, backend="slurm", jobid=5)
    attached = Runnable.from_run_dir(rundir)
    assert rundir.exists()
    del attached
    gc.collect()
    assert rundir.exists()


def test_attached_cancel_removes_directory_on_retrieval(root, monkeypatch):
    from clustafari.exceptions import CancelledError
    from clustafari.runner.slurm.info import AttachedSlurmInformation

    rundir, _ = _make_artifacts(root, State.RUNNING, backend="slurm", jobid=6)
    attached = Runnable.from_run_dir(rundir)
    assert isinstance(attached.info, AttachedSlurmInformation)
    monkeypatch.setattr(
        type(attached.info),
        "cancel",
        lambda self: setattr(self, "_cancelled", True),
    )
    attached.cancel()
    assert attached.state == RunState.CANCELLED
    # cancel() itself leaves the artifacts; retrieval from the cancelled run
    # raises the dedicated error and cleans the directory up (same semantics
    # as the dispatch path).
    with pytest.raises(CancelledError):
        attached.get(blocking=False)
    assert not rundir.exists()


def test_attached_plain_info_without_jobid(root):
    rundir, _ = _make_artifacts(root, State.RUNNING, backend="subprocess")
    attached = Runnable.from_run_dir(rundir)
    assert isinstance(attached.info, RunInformation)
    assert not isinstance(attached.info, __import__("clustafari.runner.slurm.info", fromlist=["SlurmInformation"]).SlurmInformation)
    assert attached.info.terminated() is False


# --- acceptance (tasks 4.1/4.2) ---


def test_cross_session_attach_and_get(tmp_path, monkeypatch):
    """Issue #18 acceptance: dispatch in session A, retrieve in session B."""
    import os
    import subprocess
    import sys
    import time

    monkeypatch.delenv("CLUSTAFARI_ARTIFACT_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    artifacts_root = tmp_path / "scratch"
    artifacts_root.mkdir()

    repo_root = Path(__file__).parent.parent
    tests_path = Path(__file__).parent
    tests_dir = str(tests_path)
    env = dict(
        os.environ,
        HOME=str(tmp_path),
        PYTHONPATH=f"{repo_root / 'src'}{os.pathsep}{tests_dir}{os.pathsep}{os.environ.get('PYTHONPATH', '')}",
    )

    # Session A: dispatch, drop the handle, exit (os._exit, like a dead
    # kernel — no cleanup handlers run).
    proc = subprocess.run(
        [sys.executable, str(tests_path / "recovery_session_a.py"), str(artifacts_root)],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=repo_root,
        env=env,
    )
    run_id = proc.stdout.strip().splitlines()[-1]
    assert run_id

    # Wait until session A's worker finished (its subprocess outlives A).
    statefile = artifacts_root / run_id / "compute.state"
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if statefile.exists() and statefile.read_text().strip() == str(State.FINISHED):
            break
        time.sleep(0.1)
    else:
        pytest.fail("worker never reported FINISHED")

    # Session B: fresh discovery + attach + blocking retrieval.
    runs = list_runs(artifacts_root)
    assert [r.run_id for r in runs] == [run_id]
    desc = runs[0]
    assert desc.function == "compute"
    assert desc.backend == "subprocess"
    assert desc.state == State.FINISHED

    handle = attach(run_id, artifacts_root)
    assert handle.get(blocking=True) == 42
    assert not (artifacts_root / run_id).exists()


def test_cross_session_attach_unknown_id_raises(root):
    with pytest.raises(FileNotFoundError, match="no-such-run"):
        attach("no-such-run", root)


def test_gc_zero_removes_terminal_spares_live(root, monkeypatch):
    import pyslurm

    class FakeJob:
        def __init__(self, state):
            self.state = state
            self.exit_code = 0
            self.exit_code_signal = 0
            self.standard_output = "/tmp/o.out"
            self.standard_error = "/tmp/e.err"

    class FakeJobNS:
        states = {}

        @classmethod
        def load(cls, job_id):
            return cls.states[job_id]

    monkeypatch.setattr(pyslurm, "Job", FakeJobNS)
    FakeJobNS.states = {99: FakeJob("RUNNING"), 100: FakeJob("COMPLETED")}

    finished = _make_artifacts(root, State.FINISHED, result=1)[0]
    failed = _make_artifacts(root, State.FAILED)[0]
    live = _make_artifacts(root, State.RUNNING, backend="slurm", jobid=99)[0]
    dead_worker_terminal_job = _make_artifacts(root, State.RUNNING, backend="slurm", jobid=100)[0]
    not_a_run = root / "slurm-presets-copy"
    not_a_run.mkdir()
    (not_a_run / "defaults.yaml").write_text("x")

    result = gc(0, root)
    assert result.removed == 3  # finished, failed, dead-worker-with-terminal-job
    assert not finished.exists()
    assert not failed.exists()
    assert not dead_worker_terminal_job.exists()
    # Non-terminal live run (job RUNNING, no terminal state file) survives.
    assert live.exists()
    # Non-run directories are never touched.
    assert not_a_run.exists()
    assert result.remaining == 1  # the live run


def test_gc_positive_max_age_spares_old_live_run(root):
    old_time_iso = datetime.fromtimestamp(time.time() - 10_000, UTC).isoformat()
    old_terminal = _make_artifacts(root, State.FINISHED, result=1, dispatched_at=old_time_iso)[0]
    old_live = _make_artifacts(root, State.RUNNING, backend="subprocess", dispatched_at=old_time_iso)[0]

    result = gc(60, root)
    assert result.removed == 1
    assert not old_terminal.exists()
    assert old_live.exists()


def test_gc_uses_dispatched_at_over_mtime(root):
    """A recent dispatch time protects a run even when its dir mtime is old."""
    import os

    old_dir_new_run = _make_artifacts(root, State.FINISHED, result=1)[0]
    old_time = time.time() - 10_000
    os.utime(old_dir_new_run, (old_time, old_time))
    # meta.json says dispatched 60s ago → younger than max_age.
    meta_path = old_dir_new_run / "meta.json"
    meta = json.loads(meta_path.read_text())
    meta["dispatched_at"] = datetime.now(UTC).isoformat()
    meta_path.write_text(json.dumps(meta))

    result = gc(3600, root)
    assert result.removed == 0
    assert old_dir_new_run.exists()


def test_gc_concurrent_removal_tolerated(root):
    rundir, _ = _make_artifacts(root, State.FINISHED, result=1)
    # gc removes the dir; a second concurrent party removing the same dir
    # must not raise (rmtree with ignore_errors tolerates the race).
    result = gc(0, root)
    assert result.removed == 1
    assert not rundir.exists()
    # A second gc pass over the now-empty root is a no-op, not an error.
    result2 = gc(0, root)
    assert result2.removed == 0
    assert result2.remaining == 0
