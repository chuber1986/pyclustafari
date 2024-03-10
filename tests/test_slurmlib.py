#!/usr/bin/env python
"""Tests for `slurmlib` package."""

import pytest
from manager import SlurmLib

from config import DummyConfig, SlurmConfig, SubprocessConfig


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
    with SlurmLib(DummyConfig()) as ctx:
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
    with SlurmLib(DummyConfig()) as ctx:
        res = ctx.map(fn, args, kwargs)
        for res, a, kwa in zip(res, args, kwargs):
            assert res == fn(*a, **kwa)


@pytest.mark.parametrize(
    "fn, args, kwargs, fixed",
    [
        (fn3, [(1,), (2,)], [dict(c=2), dict(c=3)], (3,)),
        (fn3, [(1,), (2,)], [{}, {}], (3, 4)),
        (fn3, [tuple(), tuple()], [dict(c=2), dict(c=2)], (3, 4)),
    ],
)
def test_map_fixed_args(fn, args, kwargs, fixed):
    with SlurmLib(DummyConfig()) as ctx:
        res = ctx.map(fn, args, kwargs, *fixed)
        for res, a, kwa in zip(res, args, kwargs):
            assert res == fn(*(fixed + a), **kwa)


@pytest.mark.parametrize(
    "fn, args, kwargs, kwfixed",
    [
        (fn3, [(1,), (2,)], [dict(c=2), dict(c=3)], dict(b=3)),
        (fn3, [(1,), (2,)], [{}, {}], dict(b=3, c=4)),
        (fn3, [tuple(), tuple()], [dict(c=2), dict(c=2)], dict(a=3, b=4)),
    ],
)
def test_map_fixed_kwargs(fn, args, kwargs, kwfixed):
    with SlurmLib(DummyConfig()) as ctx:
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
    with SlurmLib(DummyConfig()) as ctx:
        res = ctx.map(fn, None, kwargs)
        for res, kwa in zip(res, kwargs):
            assert res == fn(**kwa)


@pytest.mark.parametrize(
    "fn, args",
    [(fn0, [tuple(), tuple()]), (fn1, [(1,), (2,)]), (fn2, [(1, 2), (2, 3)])],
)
def test_map_nokwargs(fn, args):
    with SlurmLib(DummyConfig()) as ctx:
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
    with SlurmLib(SubprocessConfig()) as ctx:
        assert ctx.apply(fn, *args, **kwargs) == fn(*args, **kwargs)


@pytest.mark.skip(reason="not implemented")
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
    with SlurmLib(SlurmConfig()) as ctx:
        assert ctx.apply(fn, *args, **kwargs) == fn(*args, **kwargs)
