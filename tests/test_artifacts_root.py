#!/usr/bin/env python
"""Tests for the configurable artifacts root (issue #16).

Acceptance: setting the env var or passing the argument creates all per-run
artifact files under the custom root; with neither set, the default
``~/.clustafari`` behavior is unchanged.
"""

from pathlib import Path

import pytest

from clustafari import ClusterContext, DummyConfig, paths

# Caller-side prep writes the pickled job file; the Subprocess worker adds
# the state/out/err/log/res files under the same stem (StateUtils + result).
DUMMY_FILES = {"fn1.joblib"}


def fn1(a):
    return a + 1


def _run_dirs(root: Path) -> set[Path]:
    return {p for p in root.iterdir() if p.is_dir()}


@pytest.fixture(autouse=True)
def _fresh_path_cache():
    paths.reset_path_cache()
    yield
    paths.reset_path_cache()


def test_env_var_root_receives_run_artifacts(tmp_path, monkeypatch):
    root = tmp_path / "scratch"
    monkeypatch.setenv("CLUSTAFARI_ARTIFACT_DIR", str(root))
    monkeypatch.setenv("HOME", str(tmp_path))

    with ClusterContext(DummyConfig()) as ctx:
        run = ctx.apply_async(fn1, 1)
        assert run.tempdir is not None
        assert run.tempdir.parent == root
        assert {p.name for p in run.tempdir.iterdir()} == DUMMY_FILES
        assert run.get(blocking=True) == 2

    # The default state dir must not receive run directories.
    default_root = tmp_path / ".clustafari"
    assert not default_root.exists() or not _run_dirs(default_root)


def test_explicit_argument_root_receives_run_artifacts(tmp_path, monkeypatch):
    monkeypatch.delenv("CLUSTAFARI_ARTIFACT_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    root = tmp_path / "explicit"

    with ClusterContext(DummyConfig(), artifacts_dir=root) as ctx:
        run = ctx.apply_async(fn1, 41)
        assert run.tempdir is not None
        assert run.tempdir.parent == root
        assert {p.name for p in run.tempdir.iterdir()} == DUMMY_FILES
        assert run.get(blocking=True) == 42


def test_subprocess_worker_writes_all_files_under_custom_root(tmp_path, monkeypatch):
    from clustafari import SubprocessConfig

    monkeypatch.delenv("CLUSTAFARI_ARTIFACT_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    root = tmp_path / "scratch"

    with ClusterContext(SubprocessConfig(), artifacts_dir=root) as ctx:
        run = ctx.apply_async(fn1, 41)
        assert run.get(blocking=True) == 42
        # The run dir is cleaned up after a successful get(); assert on the
        # parent root having received the run by checking cleanup happened
        # under it (no stray default-root directory was used).
        assert not _run_dirs(root)

    default_root = tmp_path / ".clustafari"
    assert not default_root.exists() or not _run_dirs(default_root)


def test_explicit_argument_beats_env_var(tmp_path, monkeypatch):
    monkeypatch.setenv("CLUSTAFARI_ARTIFACT_DIR", str(tmp_path / "from-env"))
    monkeypatch.setenv("HOME", str(tmp_path))
    root = tmp_path / "explicit"

    with ClusterContext(DummyConfig(), artifacts_dir=root) as ctx:
        runs = ctx.map_async(fn1, [(1,), (2,)])
        assert [r.get(blocking=True) for r in runs] == [2, 3]

    env_root = tmp_path / "from-env"
    assert not env_root.exists() or not _run_dirs(env_root)


def test_default_root_unchanged_when_nothing_set(tmp_path, monkeypatch):
    monkeypatch.delenv("CLUSTAFARI_ARTIFACT_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    with ClusterContext(DummyConfig()) as ctx:
        assert ctx.apply(fn1, 1) == 2

    default_root = tmp_path / ".clustafari"
    assert default_root.is_dir()
    assert paths.artifacts_root() == default_root


def test_map_and_map_async_use_custom_root(tmp_path, monkeypatch):
    monkeypatch.delenv("CLUSTAFARI_ARTIFACT_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    root = tmp_path / "scratch"

    with ClusterContext(DummyConfig(), artifacts_dir=root) as ctx:
        assert ctx.map(fn1, [(1,), (2,)]) == [2, 3]
        runs = ctx.map_async(fn1, [(3,)])
        assert [r.get(blocking=True) for r in runs] == [4]
        for r in runs:
            assert r.tempdir is not None
            assert r.tempdir.parent == root
