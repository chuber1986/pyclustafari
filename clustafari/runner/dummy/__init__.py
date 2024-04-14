"""Export DummyRunner"""

from functools import partial

from .config import _DummyConfig
from .runner import DummyRunner

DummyConfig = partial(_DummyConfig, runner_cls=DummyRunner)
