"""Export SlurmRunner"""

from functools import partial

from clustafari.config import NodeConfig
from clustafari.paths import CLUSTAFARI_DIR

from .config import _SlurmConfig
from .runner import SlurmRunner

SlurmConfig = partial(_SlurmConfig, runner_cls=SlurmRunner)


def load_default_configurations():
    defaults = NodeConfig.load_defaults(CLUSTAFARI_DIR / "slurm_defaults.yaml")
    defaults = {f"CFG_{k}": SlurmConfig(*v) for k, v in defaults.items()}

    setattr(SlurmConfig, "get_config_names", lambda: list(defaults.keys()))
    setattr(SlurmConfig, "get_config", lambda name: defaults[name])

    for k, v in defaults.items():
        setattr(SlurmConfig, k, v)


load_default_configurations()
