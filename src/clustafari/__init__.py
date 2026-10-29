"""Top-level package for PyClustafari."""

from joblib import wrap_non_picklable_objects

from clustafari.annotations import delayed
from clustafari.manager import ClusterContext
from clustafari.runner.dummy import DummyConfig, DummyRunner
from clustafari.runner.slurm import SlurmConfig, SlurmRunner
from clustafari.runner.subprocess import SubprocessConfig, SubprocessRunner

__all__ = [
    "ClusterContext",
    "DummyConfig",
    "DummyRunner",
    "SlurmConfig",
    "SlurmRunner",
    "SubprocessConfig",
    "SubprocessRunner",
    "delayed",
    "wrap_non_picklable_objects",
]

__author__ = """Christian Huber"""
__email__ = "hiddenaddress@gmail.com"
__version__ = "0.1.0"
__license__ = "MIT"
__copyright__ = f"Copyright © 2024, {__author__}. All rights reserved."
