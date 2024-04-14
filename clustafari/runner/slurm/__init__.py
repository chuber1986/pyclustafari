"""Export SlurmRunner"""

import logging
from functools import partial

from clustafari.config import NodeConfig
from clustafari.paths import CLUSTAFARI_DIR, ROOT
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

SlurmConfig = partial(_SlurmConfig, runner_cls=SlurmRunner)


def create_config(
    mem_per_node=None,
    mem_per_cpu=None,
    mem_per_gpu=None,
    cpu_per_task=None,
    cpu_per_gpu=None,
    required_nodes=None,
    excluded_nodes=None,
    partition=None,
    generic_resource=None,
    n_tasks=None,
    n_tasks_per_node=None,
    n_tasks_per_gpu=None,
    gpus=None,
    gpus_per_task=None,
    gpus_per_node=None,
):
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
    ]
    for res, val in zip(ress, vals):
        if val is not None:
            resources.append(res(val))

    return SlurmConfig(*resources)


def load_default_configurations():
    default_fname = "slurm_defaults.yaml"
    file = CLUSTAFARI_DIR / default_fname
    if not file.exists():
        logging.warning("No default configuration found at '%s'", str(file))
        logging.warning("Restore defaults from project defaults.")

        pdefaults = ROOT / "config" / default_fname
        file.write_bytes(pdefaults.read_bytes())

    defaults = NodeConfig.load_defaults(file)
    defaults = {f"CFG_{k}": SlurmConfig(*v) for k, v in defaults.items()}

    setattr(SlurmConfig, "get_config_names", lambda: list(defaults.keys()))
    setattr(SlurmConfig, "get_config", lambda name: defaults[name])
    setattr(SlurmConfig, "create_config", create_config)

    for k, v in defaults.items():
        setattr(SlurmConfig, k, v)


load_default_configurations()
