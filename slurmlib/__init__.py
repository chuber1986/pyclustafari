"""Top-level package for SlurmLib."""

from pyprojroot import here

from slurmlib.exceptions import RunnableStateError, StateError, TimeoutException
from slurmlib.manager import ClusterContext
from slurmlib.runner.dummy import DummyConfig, DummyRunner
from slurmlib.runner.slurm import SlurmConfig, SlurmRunner
from slurmlib.runner.subprocess import SubprocessConfig, SubprocessRunner

here()

__all__ = [
    ClusterContext.__name__,
    DummyConfig.func.__name__,
    DummyRunner.__name__,
    SlurmConfig.func.__name__,
    SlurmRunner.__name__,
    SubprocessConfig.func.__name__,
    SubprocessRunner.__name__,
]

_classes = [
    ClusterContext,
    DummyConfig.func,
    DummyRunner,
    SlurmConfig.func,
    SlurmRunner,
    SubprocessConfig.func,
    SubprocessRunner,
]

_exceptions = [
    StateError,
    TimeoutException,
    RunnableStateError,
]

__author__ = """Christian Huber"""
__email__ = "hiddenaddress@gmail.com"
__version__ = "0.1.0"
__license__ = "MIT"
__copyright__ = f"Copyright © 2024, {__author__}. All rights reserved."
