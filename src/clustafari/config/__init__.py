"""Run configurations package."""

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from clustafari.paths import JOB_FILE, WORKERSTUB
from clustafari.resources import Resource
from clustafari.runner import BaseRunner


def _get_target(definition: dict[str, str]) -> str:
    return definition.get("_target_", "")


def _get_args(definition: dict[str, dict]) -> dict[str, str]:
    return definition.get("_args_", {})


def _get_class(definition: dict[str, str]) -> type:
    splits = _get_target(definition).split(".")
    package = ".".join(splits[:-1])
    clazz = splits[-1]

    module = importlib.import_module(package)
    return getattr(module, clazz)


def _parse_resource(resource: dict) -> Resource:
    args = _get_args(resource)
    clazz = _get_class(resource)
    return clazz(**args)


def _parse_resources(resources: list[dict[str, str]]) -> list[Resource]:
    return [_parse_resource(res) for res in resources]


@dataclass
class NodeConfig:
    """Node configuration class."""

    def __init__(
        self,
        runner: BaseRunner,
        resources: dict | None = None,
        jobfile: Path | str = JOB_FILE,
        workerstub: Path | str = WORKERSTUB,
    ) -> None:
        """Initialize NodeConfig with runner, resources, jobfile and workerstub."""
        self.job_file = jobfile
        self.workerstub = workerstub
        self.runner = runner

        if resources is None:
            resources = {}

        self._resources = resources

    @property
    def resources(self) -> dict[str, Resource]:
        """Return resource configurations."""
        return self._resources

    @resources.setter
    def resources(self, resources: dict[str, Resource]) -> None:
        """Set resource configurations."""
        self._resources = resources

    def __hasattr__(self, name: str) -> bool:
        """Check if attribute exists, including resources."""
        try:
            super().__getattribute__(name)
        except AttributeError:
            return name in self.resources
        return True

    def __getattribute__(self, name: str) -> Any:
        """Get attribute by name, including resources."""
        try:
            return super().__getattribute__(name)
        except AttributeError:
            resources = super().__getattribute__("_resources")
            if name in resources:
                return resources[name]
            raise

    @staticmethod
    def load_defaults(config_file: Path) -> dict:
        """Load default resource contigurations from a YAML file."""
        if not config_file.exists() or not config_file.is_file():
            return {}

        with config_file.open("r") as file:
            defs = yaml.safe_load(file)

        defaults = {}
        for name, definition in defs.items():
            cfg = _parse_resources(definition)
            defaults[name] = cfg

        return defaults
