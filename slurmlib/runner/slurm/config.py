"""Cluster configuration for SlurmRunner."""

from pathlib import Path

from resources.resources import Resource, Resources

from slurmlib.config import NodeConfig
from slurmlib.paths import JOB_FILE, SLURMLIB_DIR, WORKERSTUB

_defaults = NodeConfig.load_defaults(SLURMLIB_DIR / "slurm_defaults.yaml")


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

    @staticmethod
    def get_default_configurations() -> dict:
        return dict(_defaults)


for key, value in _defaults.items():
    setattr(_SlurmConfig, key, value)
    globals()[key] = value
