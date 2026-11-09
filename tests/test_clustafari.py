#!/usr/bin/env python
"""Tests for `pyclustafari` package."""

import os
import time

import pytest

from clustafari import ClusterContext, DummyConfig, SlurmConfig, SubprocessConfig
from clustafari.resources import CPUPerTaskResource, MemoryPerNodeResource
from clustafari.runner.state import RunState


def fn0():
    return 1


def fn1(a):
    return a + 1


def fn2(a, b):
    return a + b


def fn3(a, b, c):
    return a + b + c


@pytest.mark.parametrize(
    "fn, args, kwargs",
    [
        (fn0, tuple(), {}),
        (fn1, (1,), {}),
        (fn2, tuple(), dict(a=1, b=2)),
        (fn2, (1,), dict(b=2)),
    ],
)
def test_apply(fn, args, kwargs):
    with ClusterContext(DummyConfig()) as ctx:
        assert ctx.apply(fn, *args, **kwargs) == fn(*args, **kwargs)


@pytest.mark.parametrize(
    "fn, args, kwargs",
    [
        (fn0, [tuple(), tuple()], [{}, {}]),
        (fn1, [(1,), (2,)], [{}, {}]),
        (fn2, [tuple(), tuple()], [dict(a=1, b=2), dict(a=2, b=3)]),
        (fn2, [(1,), (2,)], [dict(b=2), dict(b=3)]),
    ],
)
def test_map(fn, args, kwargs):
    with ClusterContext(DummyConfig()) as ctx:
        res = ctx.map(fn, args, kwargs)
        for res, a, kwa in zip(res, args, kwargs):
            assert res == fn(*a, **kwa)


@pytest.mark.parametrize(
    "fn, args, kwargs, kwfixed",
    [
        (fn3, [(1,), (2,)], [dict(c=2), dict(c=3)], dict(b=3)),
        (fn3, [(1,), (2,)], [{}, {}], dict(b=3, c=4)),
        (fn3, [tuple(), tuple()], [dict(c=2), dict(c=2)], dict(a=3, b=4)),
    ],
)
def test_map_fixed_kwargs(fn, args, kwargs, kwfixed):
    with ClusterContext(DummyConfig()) as ctx:
        res = ctx.map(fn, args, kwargs, **kwfixed)
        for res, a, kwa in zip(res, args, kwargs):
            assert res == fn(*a, **{**kwfixed, **kwa})


@pytest.mark.parametrize(
    "fn, kwargs",
    [
        (fn0, [{}, {}]),
        (fn1, [dict(a=1), dict(a=2)]),
        (fn2, [dict(a=1, b=2), dict(a=2, b=3)]),
    ],
)
def test_map_noargs(fn, kwargs):
    with ClusterContext(DummyConfig()) as ctx:
        res = ctx.map(fn, None, kwargs)
        for res, kwa in zip(res, kwargs):
            assert res == fn(**kwa)


@pytest.mark.parametrize(
    "fn, args",
    [(fn0, [tuple(), tuple()]), (fn1, [(1,), (2,)]), (fn2, [(1, 2), (2, 3)])],
)
def test_map_nokwargs(fn, args):
    with ClusterContext(DummyConfig()) as ctx:
        res = ctx.map(fn, args, None)
        for res, a in zip(res, args):
            assert res == fn(*a)


@pytest.mark.parametrize(
    "fn, args, kwargs",
    [
        (fn0, tuple(), {}),
        (fn1, (1,), {}),
        (fn2, tuple(), dict(a=1, b=2)),
        (fn2, (1,), dict(b=2)),
    ],
)
def test_subprocess_runner(fn, args, kwargs):
    with ClusterContext(SubprocessConfig()) as ctx:
        assert ctx.apply(fn, *args, **kwargs) == fn(*args, **kwargs)


@pytest.mark.skipif(condition=os.system("srun -V") != 0, reason="slurm not available")
@pytest.mark.parametrize(
    "fn, args, kwargs",
    [
        (fn0, tuple(), {}),
        (fn1, (1,), {}),
        (fn2, tuple(), dict(a=1, b=2)),
        (fn2, (1,), dict(b=2)),
    ],
)
def test_slurm_runner(fn, args, kwargs):
    with ClusterContext(SlurmConfig()) as ctx:
        assert ctx.apply(fn, *args, **kwargs) == fn(*args, **kwargs)


@pytest.mark.skipif(condition=os.system("srun -V") != 0, reason="slurm not available")
def test_slurm_runner_config():
    with ClusterContext(SlurmConfig(MemoryPerNodeResource(value="1G"), CPUPerTaskResource(value=1))) as ctx:
        assert ctx.apply(fn0) == 1


@pytest.mark.skipif(condition=os.system("srun -V") != 0, reason="slurm not available")
def test_slurm_runner_killed_worker_reports_failure():
    from clustafari.exceptions import StateError

    # A 10 MB memory limit cannot run the Python interpreter, so Slurm OOM-kills
    # the worker before it can write its state file. `get` must then report the
    # failure instead of waiting for a state file that will never appear.
    with ClusterContext(SlurmConfig(MemoryPerNodeResource(value="10"), CPUPerTaskResource(value=1))) as ctx:
        run = ctx.apply_async(fn0)
        with pytest.raises(StateError, match="terminated"):
            run.get(blocking=True, timeout=60)


def boom():
    raise ValueError("kaboom")


def slow(a):
    time.sleep(a)
    return a + 1


class Acc:
    def __init__(self):
        self.x = 10

    def add(self, n):
        self.x += n
        return self.x


def test_dummy_runner_failure_raises_state_error():
    from clustafari.exceptions import StateError

    with ClusterContext(DummyConfig()) as ctx:
        run = ctx.apply_async(boom)
        with pytest.raises(StateError, match="kaboom"):
            run.get(blocking=True)


def test_dummy_runner_failure_async_get_raises():
    from clustafari.exceptions import StateError

    with ClusterContext(DummyConfig()) as ctx:
        run = ctx.apply_async(boom)
        with pytest.raises(StateError):
            run.get()


def test_subprocess_runner_failure_raises_state_error():
    from clustafari.exceptions import StateError

    with ClusterContext(SubprocessConfig()) as ctx:
        run = ctx.apply_async(boom)
        with pytest.raises(StateError, match="kaboom"):
            run.get(blocking=True)


def test_subprocess_runner_is_async():
    from clustafari.exceptions import TimeoutException

    with ClusterContext(SubprocessConfig()) as ctx:
        run = ctx.apply_async(slow, 0.4)
        with pytest.raises(TimeoutException):
            run.get(blocking=True, timeout=0.1)
        assert run.get(blocking=True) == 1.4


def test_subprocess_runner_dead_worker_reports_failure(monkeypatch, tmp_path):
    """A worker killed before writing its state file fails the run promptly.

    The packaged workerstub is replaced by a stub that exits 137 immediately,
    so the process dies before any state file can appear. get() must raise a
    StateError (embedding the exit code) instead of hanging forever (issue
    #13) — exactly the Slurm backend's dead-job behavior.
    """
    from clustafari.exceptions import StateError

    stub = tmp_path / "dying_stub.py"
    stub.write_text("import sys; sys.exit(137)\n")

    with ClusterContext(SubprocessConfig(workerstub=stub)) as ctx:
        run = ctx.apply_async(fn0)
        start = time.monotonic()
        with pytest.raises(StateError, match="137"):
            run.get(blocking=True, timeout=60)
        assert time.monotonic() - start < 60


def test_subprocess_runner_cancel_midflight_reaps_worker():
    """Cancelling a running subprocess run kills and reaps the worker (issue #12)."""
    from clustafari.exceptions import CancelledError

    with ClusterContext(SubprocessConfig()) as ctx:
        run = ctx.apply_async(slow, 30)
        assert run.state == RunState.READY

        # Wait until the worker is actually alive and running.
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and run.info.proc.poll() is not None:
            time.sleep(0.05)
        assert run.info.proc.poll() is None

        run.cancel()

        assert run.state == RunState.CANCELLED
        # The worker was terminated and reaped, not left behind.
        assert run.info.proc.poll() is not None
        with pytest.raises(CancelledError):
            run.get(blocking=True)


def test_dummy_runner_cancel_after_inline_finish_is_noop():
    """Dummy runs execute inline, so apply_async returns them FINISHED.

    Cancelling such a run must be a no-op: the result stays retrievable and
    the state stays FINISHED. (Cancelling before dispatch — INITIALIZED →
    CANCELLED — is covered by the Runnable unit tests; a dummy run cannot be
    observed in that state through the public API.)
    """
    with ClusterContext(DummyConfig()) as ctx:
        run = ctx.apply_async(fn0)
        assert run.state == RunState.FINISHED
        run.cancel()
        assert run.state == RunState.FINISHED
        assert run.get(blocking=True) == 1


def test_return_object_dummy():
    with ClusterContext(DummyConfig()) as ctx:
        acc = Acc()
        obj, x = ctx.apply(acc.add, 5, return_object=True)
        assert obj.x == 15
        assert x == 15


def test_return_object_subprocess():
    with ClusterContext(SubprocessConfig()) as ctx:
        acc = Acc()
        obj, x = ctx.apply(acc.add, 5, return_object=True)
        assert obj.x == 15
        assert x == 15


class Unpicklable:
    def __reduce__(self):
        import pickle

        raise pickle.PicklingError("cannot pickle Unpicklable")


def unpicklable_fn(arg):
    return arg


def test_unpicklable_argument_fails_run_dummy():
    from clustafari.exceptions import StateError

    with ClusterContext(DummyConfig()) as ctx:
        run = ctx.apply_async(unpicklable_fn, Unpicklable())
        assert run.state == RunState.FAILED
        with pytest.raises(StateError, match="pickle"):
            run.get(blocking=True)


def test_unpicklable_argument_fails_run_subprocess():
    from clustafari.exceptions import StateError

    with ClusterContext(SubprocessConfig()) as ctx:
        run = ctx.apply_async(unpicklable_fn, Unpicklable())
        assert run.state == RunState.FAILED
        with pytest.raises(StateError, match="pickle"):
            run.get(blocking=True)


@pytest.mark.skipif(condition=os.system("srun -V") != 0, reason="slurm not available")
def test_unpicklable_argument_fails_run_slurm():
    from clustafari.exceptions import StateError

    # A prepare failure must not submit a job to the cluster.
    with ClusterContext(SlurmConfig()) as ctx:
        run = ctx.apply_async(unpicklable_fn, Unpicklable())
        assert run.state == RunState.FAILED
        with pytest.raises(StateError, match="pickle"):
            run.get(blocking=True)


def test_subprocess_runner_status_reports_progress():
    """A live subprocess run is RUNNING mid-flight and FINISHED after get()."""
    from clustafari.runner.state import RunStatus

    with ClusterContext(SubprocessConfig()) as ctx:
        run = ctx.apply_async(slow, 2)

        # Poll until the worker reported RUNNING (worker startup takes a
        # moment; 30 s is generous for interpreter start + joblib load).
        deadline = time.monotonic() + 30
        statuses = []
        while time.monotonic() < deadline and run.status != RunStatus.RUNNING:
            statuses.append(run.status)
            time.sleep(0.05)
        assert run.status == RunStatus.RUNNING

        assert run.get(blocking=True, timeout=30) == 3
        assert run.status == RunStatus.FINISHED


def test_subprocess_runner_status_pending_before_worker_starts():
    from clustafari.runner.state import RunStatus

    with ClusterContext(SubprocessConfig()) as ctx:
        run = ctx.apply_async(slow, 30)
        # Dispatched (READY) but the worker has not reported yet.
        assert run.state == RunState.READY
        assert run.status in (RunStatus.PENDING, RunStatus.STARTED, RunStatus.RUNNING)
        run.cancel()
        assert run.status == RunStatus.CANCELLED


@pytest.mark.skipif(condition=os.system("srun -V") != 0, reason="slurm not available")
def test_slurm_runner_str_contains_jobid():
    from clustafari.runner.state import RunStatus

    with ClusterContext(SlurmConfig()) as ctx:
        run = ctx.apply_async(fn1, 1)
        text = str(run)
        assert str(run.info.jobid) in text
        assert "job" in text
        # The status vocabulary is exposed on the handle as well.
        assert isinstance(run.status, RunStatus)
        run.cancel()
        assert run.status == RunStatus.CANCELLED
