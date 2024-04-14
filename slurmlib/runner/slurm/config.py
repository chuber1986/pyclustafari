"""Cluster configuration for SlurmRunner."""

from pathlib import Path

from resources.resources import Resource, Resources

from slurmlib.config import NodeConfig
from slurmlib.paths import JOB_FILE, WORKERSTUB


class _SlurmConfig(NodeConfig):
    """Cluster configuration for SLURM"""

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

    def __str__(self):
        return f"{self.__class__.__name__[1:]}({self.resources})"

    def __repr__(self):
        return str(self)
