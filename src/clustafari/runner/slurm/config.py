"""Cluster configuration for SlurmRunner."""

from pathlib import Path

from clustafari.config import NodeConfig
from clustafari.resources.resources import Resource, Resources


class _SlurmConfig(NodeConfig):
    """Cluster configuration for SLURM."""

    def __init__(
        self,
        *resources: Resource,
        runner_cls: type,
        jobfile: Path | str | None = None,
        workerstub: Path | str | None = None,
    ) -> None:
        res = Resources(resources=resources)
        super().__init__(
            runner=runner_cls(self),
            resources=res.to_dict(),
            jobfile=jobfile,
            workerstub=workerstub,
        )
