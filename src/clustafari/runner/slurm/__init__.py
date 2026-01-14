"""Export SlurmRunner."""

import logging
from importlib.resources import files
from typing import Any

from clustafari.config import NodeConfig
from clustafari.paths import CLUSTAFARI_DIR
from clustafari.resources import (
    CPUPerGPUResource,
    CPUPerTaskResource,
    ExcludedNodesResource,
    GenericResource,
    GPUsPerNodeResource,
    GPUsPerTaskResource,
    GPUsResource,
    MemoryPerCPUResource,
    MemoryPerGPUResource,
    MemoryPerNodeResource,
    NTasksPerGPUResource,
    NTasksPerNodeResource,
    NTasksResource,
    PartitionResource,
    RequiredNodesResource,
    Resource,
)

from .config import _SlurmConfig
from .runner import SlurmRunner

logger = logging.getLogger(__name__)

defaults = {}


def _load_default_configurations():
    default_fname = "slurm_defaults.yaml"
    file = CLUSTAFARI_DIR / default_fname
    if not file.exists():
        logger.warning("No default configuration found at '%s'", str(file))
        logger.warning("Restore defaults from project defaults.")

        pdefaults = files("clustafari") / "config" / default_fname
        file.write_bytes(pdefaults.read_bytes())

    cfgs = NodeConfig.load_defaults(file)
    cfgs = {f"CFG_{k}": SlurmConfig(*v) for k, v in cfgs.items()}

    defaults.update(cfgs)

    for k, v in defaults.items():
        setattr(SlurmConfig, k, v)

    return defaults


class SlurmConfig(_SlurmConfig):
    """Configuration for SlurmRunner."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize SlurmConfig with SlurmRunner."""
        super().__init__(*args, runner_cls=SlurmRunner, **kwargs)

    @classmethod
    def get_config_names(cls) -> list[str]:
        """Return available configuration names."""
        if not defaults:
            _load_default_configurations()
        return list(defaults.keys())

    @classmethod
    def get_configs(cls) -> dict[str, list[Resource]]:
        """Return all available configurations."""
        if not defaults:
            _load_default_configurations()
        return defaults

    @classmethod
    def get_config(cls, name: str) -> list[Resource]:
        """Return configuration by name."""
        if not defaults:
            _load_default_configurations()
        return defaults[name]

    @classmethod
    def create_config(  # noqa: PLR0913
        cls,
        mem_per_node: int | str | None = None,
        mem_per_cpu: int | str | None = None,
        mem_per_gpu: int | str | None = None,
        cpu_per_task: int | str | None = None,
        cpu_per_gpu: int | str | None = None,
        required_nodes: int | str | None = None,
        excluded_nodes: str | None = None,
        partition: str | None = None,
        generic_resource: str | None = None,
        n_tasks: int | str | None = None,
        n_tasks_per_node: int | str | None = None,
        n_tasks_per_gpu: int | str | None = None,
        gpus: int | str | None = None,
        gpus_per_task: int | str | None = None,
        gpus_per_node: int | str | None = None,
    ) -> "SlurmConfig":
        """Create SlurmConfig from resource specifications."""
        resources: list[Resource] = []

        vals = [
            mem_per_node,
            mem_per_cpu,
            mem_per_gpu,
            cpu_per_task,
            cpu_per_gpu,
            required_nodes,
            excluded_nodes,
            partition,
            generic_resource,
            n_tasks,
            n_tasks_per_node,
            n_tasks_per_gpu,
            gpus,
            gpus_per_task,
            gpus_per_node,
        ]

        ress = [
            MemoryPerNodeResource,
            MemoryPerCPUResource,
            MemoryPerGPUResource,
            CPUPerTaskResource,
            CPUPerGPUResource,
            RequiredNodesResource,
            ExcludedNodesResource,
            PartitionResource,
            GenericResource,
            NTasksResource,
            NTasksPerNodeResource,
            NTasksPerGPUResource,
            GPUsResource,
            GPUsPerTaskResource,
            GPUsPerNodeResource,
        ]

        for res, val in zip(ress, vals, strict=False):
            if val is not None:
                resources.append(res(val))

        return SlurmConfig(*resources)
