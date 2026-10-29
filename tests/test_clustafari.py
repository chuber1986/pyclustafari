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


def test_slurm_runner_config():
    with ClusterContext(
        SlurmConfig(MemoryPerNodeResource(value="1G"), CPUPerTaskResource(value=1))
    ) as ctx:
        assert ctx.apply(fn0) == 1


@pytest.mark.skipif(condition=os.system("srun -V") != 0, reason="slurm not available")
def test_slurm_runner_killed_worker_reports_failure():
    from clustafari.exceptions import StateError

    # A 10 MB memory limit cannot run the Python interpreter, so Slurm OOM-kills
    # the worker before it can write its state file. `get` must then report the
    # failure instead of waiting for a state file that will never appear.
    with ClusterContext(
        SlurmConfig(MemoryPerNodeResource(value="10"), CPUPerTaskResource(value=1))
    ) as ctx:
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
