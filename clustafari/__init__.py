"""Top-level package for PyClustafari."""

from joblib import wrap_non_picklable_objects
from pyprojroot import here

from clustafari.annotations import delayed
from clustafari.manager import ClusterContext
from clustafari.runner.dummy import DummyConfig, DummyRunner
from clustafari.runner.slurm import SlurmConfig, SlurmRunner
from clustafari.runner.subprocess import SubprocessConfig, SubprocessRunner

here()

__exports__ = {
    DummyConfig.func.__name__: DummyConfig,
    SlurmConfig.func.__name__: SlurmConfig,
    SubprocessConfig.func.__name__: SubprocessConfig,
    **{
        item.__name__: item
        for item in [
            ClusterContext,
            DummyRunner,
            SlurmRunner,
            SubprocessRunner,
            wrap_non_picklable_objects,
            delayed,
        ]
    },
}


def _set_attributes(attributes: dict):
    for key, value in attributes.items():
        globals()[key] = value


_set_attributes(__exports__)

__author__ = """Christian Huber"""
__email__ = "hiddenaddress@gmail.com"
__version__ = "0.1.0"
__license__ = "MIT"
__copyright__ = f"Copyright © 2024, {__author__}. All rights reserved."
