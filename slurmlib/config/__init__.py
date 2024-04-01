"""Run configurations package."""

import abc
import importlib
from dataclasses import dataclass
from pathlib import Path

import yaml

from slurmlib import JOB_FILE, WORKERSTUB


def _get_target(definition):
    return definition.get("_target_")


def _get_args(definition):
    return definition.get("_args_", [])


def _get_class(definition):
    splits = _get_target(definition).split(".")
    package = ".".join(splits[:-2])
    module = splits[-2]
    clazz = splits[-1]

    module = importlib.import_module(module, package)
    return getattr(module, clazz)


def _parse_resource(resource):
    args = _get_args(resource)
    clazz = _get_class(resource)
    return clazz(**args)


def _parse_resources(resources):
    return [_parse_resource(res) for res in resources]


@dataclass
class NodeConfig(abc.ABC):
    """Node configuration class."""

    def __init__(
        self, jobfile: Path | str = JOB_FILE, workerstub: Path | str = WORKERSTUB
    ) -> None:
        self.job_file = jobfile
        self.workerstub = workerstub

    @staticmethod
    def load_defaults(config_file: Path):
        if not config_file.exists() or not config_file.is_file():
            return {}

        with config_file.open("r") as file:
            defs = yaml.safe_load(file)

        defaults = {}
        for name, definition in defs.items():
            cfg = _parse_resources(definition)
            defaults[name] = cfg

        return defaults
