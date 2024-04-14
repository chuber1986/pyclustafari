"""Export SubprocessRunner"""

from functools import partial

from .config import _SubprocessConfig
from .runner import SubprocessRunner

SubprocessConfig = partial(_SubprocessConfig, runner_cls=SubprocessRunner)
