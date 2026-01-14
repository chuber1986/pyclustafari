"""Cluster configuration for SlurmRunner."""

from pathlib import Path

from clustafari.config import NodeConfig
from clustafari.paths import JOB_FILE, WORKERSTUB
from clustafari.resources.resources import Resource, Resources


class _SlurmConfig(NodeConfig):
    """Cluster configuration for SLURM."""

    def __init__(
        self,
        *resources: Resource,
        runner_cls: type,
        jobfile: Path | str = JOB_FILE,
        workerstub: Path | str = WORKERSTUB,
    ) -> None:
        res = Resources(resources=resources)
        super().__init__(
            runner=runner_cls(self),
            resources=res.to_dict(),
            jobfile=jobfile,
            workerstub=workerstub,
        )

    def __str__(self) -> str:
        return f"{self.__class__.__name__[1:]}({self.resources})"

    def __repr__(self) -> str:
        return str(self)
