"""Export SlurmRunner"""

from functools import partial

from slurmlib.config import NodeConfig
from slurmlib.paths import SLURMLIB_DIR

from .config import _SlurmConfig
from .runner import SlurmRunner

SlurmConfig = partial(_SlurmConfig, runner_cls=SlurmRunner)


def load_default_configurations():
    defaults = NodeConfig.load_defaults(SLURMLIB_DIR / "slurm_defaults.yaml")
    defaults = {f"CFG_{k}": SlurmConfig(*v) for k, v in defaults.items()}

    setattr(SlurmConfig, "get_config_names", lambda: list(defaults.keys()))
    setattr(SlurmConfig, "get_config", lambda name: defaults[name])

    for k, v in defaults.items():
        setattr(SlurmConfig, k, v)


load_default_configurations()
