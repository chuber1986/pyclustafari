#!/usr/bin/env python
"""Tests for `clustafari.paths` lazy resolution."""

import importlib.resources
import os
import subprocess
import sys
from pathlib import Path

import pytest

from clustafari import paths


@pytest.fixture(autouse=True)
def _fresh_path_cache():
    """Isolate path-resolution caches between tests."""
    paths.reset_path_cache()
    yield
    paths.reset_path_cache()


def test_import_has_no_side_effects(tmp_path):
    """Importing clustafari creates no ~/.clustafari and raises nothing."""
    code = (
        "import clustafari, os; "
        "raise SystemExit(0 if not os.path.isdir(os.path.join(os.environ['HOME'], '.clustafari')) else 1)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        env={**os.environ, "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, f"import side effects detected: {proc.stderr}"
    assert not (tmp_path / ".clustafari").exists()


def test_clean_import_survives_missing_job_file(tmp_path):
    """Import succeeds with no job script on PATH and a foreign cwd.

    Runs the import in a subprocess whose cwd is outside the repo and whose
    PATH carries no clustafari.job; the packaged copy (inside the package
    directory) satisfies resolution lazily. Issue-#15 acceptance scenario.
    """
    code = "import clustafari; raise SystemExit(0)"
    env = {
        **os.environ,
        "HOME": str(tmp_path),
        "PATH": str(tmp_path),  # no clustafari.job anywhere on PATH
    }
    proc = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr


def test_clustafari_dir_created_on_first_use(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    d = paths.clustafari_dir()
    assert d == tmp_path / ".clustafari"
    assert d.is_dir()
    # Second call returns the same directory.
    assert paths.clustafari_dir() == d


def test_clustafari_dir_cached_until_reset(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    first = paths.clustafari_dir()
    monkeypatch.setenv("HOME", str(tmp_path / "elsewhere"))
    assert paths.clustafari_dir() == first  # cached
    paths.reset_path_cache()
    assert paths.clustafari_dir() == tmp_path / "elsewhere" / ".clustafari"


def test_job_file_resolves_packaged_copy():
    jf = paths.job_file()
    with importlib.resources.as_file(importlib.resources.files("clustafari")) as pkg:
        expected = pkg / "job" / "clustafari.job"
    assert jf == expected
    assert jf.is_file()
    # Cached: second call returns identical path.
    assert paths.job_file() == jf


def test_job_file_checkout_fallback(tmp_path, monkeypatch):
    fake_checkout = tmp_path / "scripts" / "clustafari.job"
    fake_checkout.parent.mkdir()
    fake_checkout.write_text("#!/bin/sh\n")
    monkeypatch.setattr(paths, "_CHECKOUT_JOB_FILE", fake_checkout)
    # Simulate no packaged copy.
    monkeypatch.setattr(paths, "_packaged_job_file", lambda: None)

    jf = paths.job_file()
    assert jf == fake_checkout


def test_job_file_path_fallback(tmp_path, monkeypatch):
    prog = tmp_path / "clustafari.job"
    prog.write_text("#!/bin/sh\n")
    prog.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setattr(paths, "_packaged_job_file", lambda: None)
    monkeypatch.setattr(paths, "_CHECKOUT_JOB_FILE", tmp_path / "nope" / "clustafari.job")

    jf = paths.job_file()
    assert jf == prog


def test_job_file_missing_everywhere_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))  # empty dir, nothing matching
    monkeypatch.setattr(paths, "_packaged_job_file", lambda: None)
    monkeypatch.setattr(paths, "_CHECKOUT_JOB_FILE", tmp_path / "nope" / "clustafari.job")

    with pytest.raises(FileNotFoundError, match="searched"):
        paths.job_file()


def test_config_construction_without_checkout_or_path_copy(tmp_path, monkeypatch):
    """Config defaults resolve the packaged copy with no checkout/PATH script.

    Simulates the installed-wheel layout: the checkout fallback is pointed at
    a nonexistent location and PATH carries no clustafari.job. Construction
    must still succeed, resolving the packaged copy.
    """
    monkeypatch.setenv("PATH", str(tmp_path))  # nothing matching on PATH
    monkeypatch.setattr(paths, "_CHECKOUT_JOB_FILE", tmp_path / "nope" / "clustafari.job")

    from clustafari.config import NodeConfig
    from clustafari.runner.dummy import DummyRunner

    cfg = NodeConfig(runner=DummyRunner())
    job = Path(cfg.job_file)
    stub = Path(cfg.workerstub)
    assert job.is_file()
    assert job.name == "clustafari.job"
    assert stub.is_file()

    from clustafari import SlurmConfig

    scfg = SlurmConfig.create_config(mem_per_node="4G")
    sjob = Path(scfg.job_file)
    assert sjob.is_file()
    assert sjob.name == "clustafari.job"


def test_workerstub_resolves_package_module():
    from clustafari import workerstub as workerstub_mod

    w = paths.workerstub()
    wf = workerstub_mod.__file__
    assert wf is not None
    assert w == Path(wf)
    assert w.is_file()


def test_reset_path_cache_clears_all(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    paths.clustafari_dir()
    paths.workerstub()
    assert paths._CACHE  # populated
    paths.reset_path_cache()
    assert paths._CACHE == {}
