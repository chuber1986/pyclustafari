#!/usr/bin/env python
"""Tests that all artifacts created in the clustafari directory are deleted.

Issue #7: Ensure all artefacts generated in the .clustafari folder are
deleted after the context object no longer exists (and, more strictly,
after each run's result has been retrieved or the run handle is gone).
"""

import gc
import os

import pytest

from clustafari import ClusterContext, DummyConfig, SubprocessConfig
from clustafari.exceptions import StateError
from clustafari import paths


def fn1(a):
    return a + 1


def boom():
    raise ValueError("kaboom")


def _temp_dirs():
    """Return the set of run tempdirs currently in the clustafari directory."""
    return {p.name for p in paths.clustafari_dir().iterdir() if p.is_dir()}


def test_failed_apply_cleans_tempdir_on_context_exit():
    """A failed synchronous apply must not leave artifacts behind the context."""
    before = _temp_dirs()
    with pytest.raises(StateError, match="kaboom"):
        with ClusterContext(DummyConfig()) as ctx:
            ctx.apply(boom)
    gc.collect()
    assert _temp_dirs() - before == set()


def test_failed_dummy_run_cleans_tempdir_after_get():
    """A failed async run must drop its tempdir once get() reports the failure."""
    before = _temp_dirs()
    with ClusterContext(DummyConfig()) as ctx:
        run = ctx.apply_async(boom)
        assert run.tempdir is not None
        with pytest.raises(StateError, match="kaboom"):
            run.get(blocking=True)
        assert not run.tempdir.exists()
    assert _temp_dirs() - before == set()


def test_failed_subprocess_run_cleans_tempdir_after_get():
    before = _temp_dirs()
    with ClusterContext(SubprocessConfig()) as ctx:
        run = ctx.apply_async(boom)
        with pytest.raises(StateError, match="kaboom"):
            run.get(blocking=True)
        assert run.tempdir is None or not run.tempdir.exists()
    assert _temp_dirs() - before == set()


@pytest.mark.skipif(condition=os.system("srun -V") != 0, reason="slurm not available")
def test_failed_slurm_run_cleans_tempdir_after_get():
    from clustafari import SlurmConfig

    before = _temp_dirs()
    with ClusterContext(SlurmConfig()) as ctx:
        run = ctx.apply_async(boom)
        with pytest.raises(StateError, match="kaboom"):
            run.get(blocking=True, timeout=120)
        assert run.tempdir is None or not run.tempdir.exists()
    assert _temp_dirs() - before == set()


def test_unreferenced_failed_run_cleaned_on_garbage_collection():
    """A run whose handle is dropped is cleaned up when it is garbage collected."""
    before = _temp_dirs()

    def spawn():
        with ClusterContext(DummyConfig()) as ctx:
            ctx.apply_async(boom)

    spawn()
    gc.collect()
    assert _temp_dirs() - before == set()


def test_unreferenced_finished_run_cleaned_on_garbage_collection():
    before = _temp_dirs()

    def spawn():
        with ClusterContext(DummyConfig()) as ctx:
            ctx.apply_async(fn1, 1).get(blocking=True)

    spawn()
    gc.collect()
    assert _temp_dirs() - before == set()


def test_successful_runs_leave_no_new_directories():
    before = _temp_dirs()
    with ClusterContext(DummyConfig()) as ctx:
        assert ctx.apply(fn1, 1) == 2
        assert ctx.map(fn1, [(1,), (2,)], None) == [2, 3]
    with ClusterContext(SubprocessConfig()) as ctx:
        assert ctx.apply(fn1, 1) == 2
    gc.collect()
    assert _temp_dirs() - before == set()
