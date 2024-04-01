"""Cluster configuration for SlurmRunner."""

from pathlib import Path

from resources.resources import Resource, Resources

from slurmlib import JOB_FILE, SLURMLIB_DIR, WORKERSTUB

from . import NodeConfig

__all__ = ["SlurmConfig"]

_defaults = NodeConfig.load_defaults(SLURMLIB_DIR / "slurm_defaults.yaml")


class SlurmConfig(NodeConfig):
    """Cluster configuration for SLURM"""

    def __init__(
        self,
        *resources: Resource,
        jobfile: Path | str = JOB_FILE,
        workerstub: Path | str = WORKERSTUB,
    ) -> None:
        res = Resources(resources=resources)
        super().__init__(
            resources=res.to_dict(), jobfile=jobfile, workerstub=workerstub
        )

    @staticmethod
    def get_default_configurations() -> dict:
        return dict(_defaults)


for key, value in _defaults.items():
    setattr(SlurmConfig, key, value)
    globals()[key] = value
