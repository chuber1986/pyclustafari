"""Regression tests for by-value callable dispatch (issue #31).

Lambdas, nested defs, `functools.partial` of either, and module-level defs
defined in a `__main__` driver script are all unpicklable under stdlib
pickle's by-reference rules; the dill-based artifact serializer transports
them by value. The `__main__` case runs a driver script as a real subprocess
(see tests/main_def_driver.py).
"""

import subprocess
import sys
from functools import partial
from pathlib import Path

import pytest

from clustafari import ClusterContext, DummyConfig, SubprocessConfig

REPO_ROOT = Path(__file__).parent.parent

#: Script-level global captured by reference in the recursion test below.
_GLOBAL_SCALE = 10


class _Point:
    def __init__(self, x):
        self.x = x

    def __eq__(self, other):
        return isinstance(other, _Point) and self.x == other.x


def make_adder(n):
    """Module-level factory returning a nested def (unpicklable by reference)."""

    def add(x):
        return x + n

    return add


def test_lambda_dispatch_dummy():
    with ClusterContext(DummyConfig()) as ctx:
        assert ctx.apply(lambda x: x * 3, 5) == 15


def test_lambda_dispatch_subprocess():
    with ClusterContext(SubprocessConfig()) as ctx:
        assert ctx.apply(lambda x: x * 3, 5) == 15


def test_lambda_dispatch_subprocess_async_with_kwargs():
    with ClusterContext(SubprocessConfig()) as ctx:
        run = ctx.apply_async(lambda a, b: a - b, 10, b=4)
        assert run.get(blocking=True) == 6


def test_lambda_returning_lambda_subprocess():
    # The result itself is a lambda: exercises the parent-side result load
    # of a by-value function (worker result dump -> parent load).
    with ClusterContext(SubprocessConfig()) as ctx:
        inner = ctx.apply(lambda: (lambda x: x + 1))
        assert inner(41) == 42


def test_nested_def_dispatch_subprocess():
    def inner(x):
        return x + 1

    with ClusterContext(SubprocessConfig()) as ctx:
        assert ctx.apply(inner, 41) == 42


def test_nested_def_as_result_subprocess():
    with ClusterContext(SubprocessConfig()) as ctx:
        add = ctx.apply(make_adder, 2)
        assert add(40) == 42


def test_partial_of_lambda_subprocess():
    p = partial(lambda a, b: a + b, 40)
    with ClusterContext(SubprocessConfig()) as ctx:
        assert ctx.apply(p, 2) == 42


def test_lambda_capturing_script_globals_subprocess():
    # recurse=True: dill captures the referenced module-level values
    # (a constant and a __main__-style class) into the artifact.
    with ClusterContext(SubprocessConfig()) as ctx:
        assert ctx.apply(lambda x: x + _GLOBAL_SCALE, 5) == 15
        assert ctx.apply(lambda x: _Point(x), 3) == _Point(3)


def test_lambda_capturing_script_globals_dummy():
    with ClusterContext(DummyConfig()) as ctx:
        assert ctx.apply(lambda x: x + _GLOBAL_SCALE, 5) == 15


def test_main_module_def_subprocess(tmp_path):
    """A module-level def in the user's __main__ script dispatches on Subprocess.

    Runs tests/main_def_driver.py as a real subprocess so the dispatched
    function's home module is genuinely `__main__` (the pre-dill failure
    mode: the worker's `__main__` has no attribute 'g').
    """
    proc = subprocess.run(  # noqa: S603
        [sys.executable, str(REPO_ROOT / "tests" / "main_def_driver.py"), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, f"driver failed:\nstdout:{proc.stdout}\nstderr:{proc.stderr}"
    assert "ok" in proc.stdout


def test_wrap_non_picklable_objects_smoke_subprocess():
    # The documented workaround (docs/usage.md) had no direct test before
    # issue #31; it must keep working under the dill serializer.
    joblib = pytest.importorskip("joblib")
    wrapped = joblib.wrap_non_picklable_objects(make_adder)
    with ClusterContext(SubprocessConfig()) as ctx:
        add = ctx.apply(wrapped, 2)
        assert add(40) == 42
