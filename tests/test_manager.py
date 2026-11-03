#!/usr/bin/env python
"""Tests for `ClusterContext` and `BaseRunner.map_async` argument handling."""

import pytest

from clustafari import ClusterContext, DummyConfig
from clustafari.config import NodeConfig
from clustafari.runner import BaseRunner, RunInformation
from clustafari.runner.runnable import Runnable
from clustafari.runner.state import RunState


class _SpyRunner(BaseRunner):
    def __init__(self):
        super().__init__()
        self.calls: list[Runnable] = []

    def _run(self, runobj: Runnable) -> RunInformation:
        self.calls.append(runobj)
        return RunInformation()


class _SpyConfig(NodeConfig):
    def __init__(self, runner: _SpyRunner):
        super().__init__(runner=runner, resources={}, jobfile="", workerstub="")


def fn0():
    return 0


def fn1(a):
    return a + 1


def fn2(a, b, c=10):
    return a + b + c


def test_context_enter_returns_context():
    cfg = DummyConfig()
    ctx = ClusterContext(cfg)
    assert ctx.__enter__() is ctx


def test_apply_async_delegates_to_runner():
    runner = _SpyRunner()
    cfg = _SpyConfig(runner)
    with ClusterContext(cfg) as ctx:
        run = ctx.apply_async(fn1, 1)
    assert len(runner.calls) == 1
    assert run is runner.calls[0]


def test_map_async_delegates_to_runner():
    runner = _SpyRunner()
    cfg = _SpyConfig(runner)
    with ClusterContext(cfg) as ctx:
        runs = ctx.map_async(fn1, [(1,), (2,)], [{}, {}])
    assert len(runs) == 2
    assert len(runner.calls) == 2


def test_map_async_args_only_fills_empty_kwargs():
    from clustafari.runner.runnable import _get_partial_arguments

    runner = _SpyRunner()
    cfg = _SpyConfig(runner)
    with ClusterContext(cfg) as ctx:
        runs = ctx.map_async(fn2, [(1,), (2,)], None, b=10)
    assert [r.kwargs for r in runs] == [{}, {}]
    assert [r.args for r in runs] == [(1,), (2,)]
    # The fixed kwargs are bound into the partial function; per-run args are
    # stored on the run object.
    assert [_get_partial_arguments(r.function)[1] for r in runs] == [{"b": 10}, {"b": 10}]
    assert [_get_partial_arguments(r.function)[0] for r in runs] == [(), ()]


def test_map_async_kwargs_only_fills_empty_args():
    runner = _SpyRunner()
    cfg = _SpyConfig(runner)
    with ClusterContext(cfg) as ctx:
        runs = ctx.map_async(fn2, None, [dict(b=1, c=2), dict(b=3, c=4)])
    assert [r.args for r in runs] == [(), ()]
    assert [r.kwargs for r in runs] == [{"b": 1, "c": 2}, {"b": 3, "c": 4}]


def test_map_async_args_and_kwargs_length_mismatch_raises():
    with ClusterContext(DummyConfig()) as ctx:
        with pytest.raises(ValueError, match="same length"):
            ctx.map_async(fn1, [(1,), (2,)], [dict()])


def test_map_async_both_none_yields_no_runs():
    runner = _SpyRunner()
    cfg = _SpyConfig(runner)
    with ClusterContext(cfg) as ctx:
        assert ctx.map_async(fn0) == []
    assert runner.calls == []


def test_apply_kwargs_forwarded_to_function():
    with ClusterContext(DummyConfig()) as ctx:
        assert ctx.apply(fn2, 1, b=2, c=5) == 8


def slow(a):
    import time

    time.sleep(a)
    return a


def test_nonblocking_get_on_running_job_raises():
    from clustafari import SubprocessConfig
    from clustafari.exceptions import RunnableStateError

    with ClusterContext(SubprocessConfig()) as ctx:
        run = ctx.apply_async(slow, 2)
        with pytest.raises(RunnableStateError, match="not finished"):
            run.get()
        # The job is still running, not failed.
        assert run.state != RunState.FAILED
        assert run.get(blocking=True) == 2
