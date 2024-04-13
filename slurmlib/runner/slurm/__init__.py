"""Export SlurmRunner"""

from functools import partial

from .config import _SlurmConfig
from .runner import SlurmRunner

SlurmConfig = partial(_SlurmConfig, runner_cls=SlurmRunner)
setattr(
    SlurmConfig, "get_default_configurations", _SlurmConfig.get_default_configurations
)
