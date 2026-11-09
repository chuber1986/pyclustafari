#!/usr/bin/env python
"""Tests for `clustafari.config`, `clustafari.annotations`, and `clustafari.paths`."""

from pathlib import Path

import pytest

from clustafari.annotations import delayed
from clustafari.config import NodeConfig
from clustafari.paths import _find_path_to
from clustafari.runner import BaseRunner
from clustafari.resources import CPUPerTaskResource, MemoryPerNodeResource, PartitionResource
from clustafari.runner.dummy import DummyConfig
from clustafari.runner.slurm import SlurmConfig


class _Runner(BaseRunner):
    def _run(self, runobj):
        return None


def test_node_config_attr_access_returns_resource():
    cfg = NodeConfig(runner=_Runner(), resources={"memory": MemoryPerNodeResource("8G")}, jobfile="", workerstub="")
    assert cfg.memory.name == "memory_per_node"
    assert str(cfg.memory.value) == "8G"


def test_node_config_attr_access_missing_raises():
    cfg = NodeConfig(runner=_Runner(), resources={}, jobfile="", workerstub="")
    with pytest.raises(AttributeError, match="no attribute"):
        _ = cfg.nonexistent
    with pytest.raises(AttributeError):
        _ = cfg._private


def test_node_config_str_and_repr():
    cfg = NodeConfig(runner=_Runner(), resources={"cpus": CPUPerTaskResource(2)}, jobfile="", workerstub="")
    assert "NodeConfig" in str(cfg)
    assert repr(cfg) == str(cfg)
    assert "cpus_per_task" in str(cfg)


def test_node_config_load_defaults_missing_file():
    assert NodeConfig.load_defaults(Path("/nonexistent/slurm_defaults.yaml")) == {}


def test_node_config_load_defaults_parses_package_defaults():
    import importlib.resources

    defaults = NodeConfig.load_defaults(
        Path(str(importlib.resources.files("clustafari") / "config" / "slurm_defaults.yaml"))
    )
    assert set(defaults) == {
        "CPU1_MEM8G",
        "CPU4_MEM8G",
        "CPU8_MEM32G",
        "CPU4_MEM8G_GPU1S",
        "CPU4_MEM8G_GPU2S",
        "CPU8_MEM32G_GPU2S",
        "CPU8_MEM32G_GPU1",
        "CPU8_MEM32G_GPU2",
    }
    assert defaults["CPU1_MEM8G"][0].name == "memory_per_node"
    assert defaults["CPU1_MEM8G"][1].name == "cpus_per_task"


def test_slurm_config_create_config_builds_requested_resources():
    cfg = SlurmConfig.create_config(mem_per_node="4G", cpu_per_task=2, partition="interactive")
    # _SlurmConfig stores Resources.to_dict(): name -> value string.
    assert cfg.resources == {"memory_per_node": "4G", "cpus_per_task": "2", "partitions": "interactive"}


def test_slurm_config_create_config_empty():
    cfg = SlurmConfig.create_config()
    assert cfg.resources == {}


def test_slurm_config_load_named_defaults(tmp_path, monkeypatch):
    import clustafari.runner.slurm as slurm_mod

    # Point the loader at an isolated directory and reset the global cache so
    # the package defaults get (re)created there.
    monkeypatch.setattr(slurm_mod, "CLUSTAFARI_DIR", tmp_path)
    monkeypatch.setattr(slurm_mod, "defaults", {})

    cfg = SlurmConfig.get_config("CFG_CPU4_MEM8G")
    assert isinstance(cfg, SlurmConfig)
    assert cfg.resources == {"memory_per_node": "8G", "cpus_per_task": "4"}
    assert (tmp_path / "slurm_defaults.yaml").exists()

    # Reset the shared cache between calls so each accessor runs its own
    # lazy-load path (and subsequent calls hit the warm cache).
    monkeypatch.setattr(slurm_mod, "defaults", {})
    configs = SlurmConfig.get_configs()
    assert "CFG_CPU1_MEM8G" in configs
    assert set(SlurmConfig.get_configs()) == set(configs)  # warm cache hit

    monkeypatch.setattr(slurm_mod, "defaults", {})
    names = SlurmConfig.get_config_names()
    assert set(names) == set(configs)
    assert SlurmConfig.get_config_names() == names  # warm cache hit


def test_delayed_returns_partial_with_captured_args():
    def add(a, b):
        return a + b

    call = delayed(add)(1, b=2)
    assert call.func is not None
    assert call.args == (1,)
    assert call.keywords == {"b": 2}


def test_delayed_wraps_unpicklable_objects():
    class Stateful:
        def __reduce__(self):
            raise Exception("nope")

        def method(self, x):
            return x

    state = Stateful()
    call = delayed(state.method)(5)
    # joblib's wrap_non_picklable_objects turns bound methods into a callable
    # wrapping (unbound fn, self, args, kwargs); calling it must work.
    assert call() == 5


def test_find_path_to_missing_raises(monkeypatch):
    monkeypatch.setenv("PATH", "")
    with pytest.raises(ValueError, match="Can't find"):
        _find_path_to("definitely-not-a-program-xyz")


def test_find_path_to_finds_executable_in_path(tmp_path, monkeypatch):
    prog = tmp_path / "my-tool"
    prog.write_text("#!/bin/sh\n")
    prog.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert _find_path_to("my-tool") == prog
