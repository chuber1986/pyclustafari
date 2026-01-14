"""Datastructures for SLURM recourse configurations."""

import logging
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

__all__ = [
    "CPUPerGPUResource",
    "CPUPerTaskResource",
    "ExcludedNodesResource",
    "GPUsPerNodeResource",
    "GPUsPerTaskResource",
    "GPUsResource",
    "GenericResource",
    "MemoryPerCPUResource",
    "MemoryPerGPUResource",
    "MemoryPerNodeResource",
    "NTasksPerGPUResource",
    "NTasksPerNodeResource",
    "NTasksResource",
    "PartitionResource",
    "RequiredNodesResource",
    "Resource",
    "Resources",
    "Unit",
]

logger = logging.getLogger(__name__)


class Unit(StrEnum):
    """Units for resource values."""

    KILO = "K"
    MEGA = "M"
    GIGA = "G"
    TERA = "T"
    DEFAULT = ""

    @classmethod
    def _missing_(cls, value: object) -> "Unit":
        """Return default unit if missing."""
        logger.warning("Unknown unit '%s', defaulting to DEFAULT.", value)
        return Unit.DEFAULT


def _isnumeric(value: str) -> bool:
    pattern = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
    return pattern.match(value) is not None


def _isinteger(value: str) -> bool:
    pattern = re.compile(r"^[+-]?(\d+)?$")
    return pattern.match(value) is not None


@dataclass
class ResourceValue:
    """Resource value."""

    value: Any
    unit: Unit | str | None = Unit.DEFAULT

    def __post_init__(self) -> None:
        if self.unit is None:
            self.unit = Unit.DEFAULT
        elif isinstance(self.unit, str):
            self.unit = Unit(self.unit.upper())

    @classmethod
    def from_value(cls, value: Any) -> "ResourceValue":
        if isinstance(value, ResourceValue):
            return value

        # String of form "<values><unit>", e.g. "234M"
        if isinstance(value, str):
            val = "".join(value.split())
            if _isnumeric(val):
                v = float(val)
                if v % 1 == 0:
                    v = int(v)

                return ResourceValue(v)
            if not _isnumeric(val) and _isnumeric(val[:-1]):
                return ResourceValue(val[:-1], val[-1])

        return ResourceValue(value)

    def __str__(self) -> str:
        val = self.value
        if isinstance(self.value, list):
            val = ",".join(self.value) if self.value else ""

        if isinstance(self.value, dict):
            if self.value:
                val = [f"{k}:{v}" for k, v in self.value.items()]
                val = ",".join(val)
            else:
                val = ""

        assert self.unit is not None
        return str(val) + self.unit


def check_numeric_value(val: ResourceValue):
    if not _isnumeric(str(val.value)):
        msg = f"Resource requires numeric value, got '{val.value}'."
        raise ValueError(msg)


def check_integer(val: ResourceValue):
    if not _isinteger(str(val.value)):
        msg = f"Resource requires integer value, got '{val.value}'."
        raise ValueError(msg)


def check_positive(val: ResourceValue):
    if str(val.value)[0] == "-":
        msg = f"Resource requires positive value, got '{val.value}'."
        raise ValueError(msg)


def check_no_unit(val: ResourceValue):
    if val.unit != Unit.DEFAULT:
        msg = f"Resource must not specify a unit, got '{val.unit}'."
        raise ValueError(msg)


def check_str_or_dict(val: ResourceValue):
    if isinstance(val.value, str):
        if _isnumeric(val.value):
            msg = f"Resource must not be numeric, got '{val.value}'."
            raise ValueError(msg)
        return

    if not isinstance(val.value, dict):
        msg = f"Resource nust be a string or dictionary, got '{type(val.value)}'."
        raise TypeError(msg)


def check_str_or_list_str(val: ResourceValue):
    if val.unit != Unit.DEFAULT:
        msg = f"Resource must not specify a unit, got '{val.unit}'."
        raise ValueError(msg)

    if isinstance(val.value, str):
        if _isnumeric(val.value):
            msg = f"Resource must not be numeric, got '{val.value}'."
            raise ValueError(msg)
        return

    if not isinstance(val.value, Iterable):
        msg = f"Resource must be of type str or list of strings, got '{type(val.value)}'."
        raise TypeError(msg)

    for v in val.value:
        if not isinstance(v, str):
            msg = f"Resource must be of type str or list of strings, got list value of type '{type(v)}'."
            raise TypeError(msg)

        if _isnumeric(v):
            msg = f"Resource element values must not be numeric, got '{type(v)}'."
            raise ValueError(msg)


@dataclass
class Resource:
    """Base class for SLURM resources."""

    value: ResourceValue | Any
    name: str = field(init=False)

    type_check: Callable[["Resource"], None] = lambda _: None

    def check_value(self) -> None:
        """Check if value is valid. To be implemented by subclasses."""
        return self.type_check(self)

    def __post_init__(self) -> None:
        self.value = ResourceValue.from_value(self.value)
        self.check_value()

    def to_string_tuple(self) -> tuple[str, str]:
        """Return resource as (name, value) tuple."""
        return self.name, str(self.value)


def positive_integer_resource(cls: type[Resource]) -> type[Resource]:
    def type_check(obj: Resource) -> None:
        check_integer(obj.value)
        check_positive(obj.value)

    cls.type_check = type_check
    return cls


def count_resource(cls: type[Resource]):
    def type_check(obj: Resource) -> None:
        check_integer(obj.value)
        check_positive(obj.value)
        check_no_unit(obj.value)

    cls.type_check = type_check
    return cls


def string_resource(cls: type[Resource]):
    def type_check(obj: Resource) -> None:
        check_str_or_list_str(obj.value)

    cls.type_check = type_check
    return cls


@positive_integer_resource
class MemoryPerNodeResource(Resource):
    """Amount of memory per compute node."""

    name: str = "memory_per_node"


@positive_integer_resource
class MemoryPerCPUResource(Resource):
    """Amount of memory per CPU."""

    name: str = "memory_per_cpu"


@positive_integer_resource
class MemoryPerGPUResource(Resource):
    """Amount of memory per GPU."""

    name: str = "memory_per_gpu"


@count_resource
class CPUPerTaskResource(Resource):
    """Number of CPUs per task."""

    name: str = "cpus_per_task"


@count_resource
class CPUPerGPUResource(Resource):
    """Number of CPUs per GPU."""

    name: str = "cpus_per_gpu"


@count_resource
class NTasksResource(Resource):
    """Number of tasks."""

    name: str = "ntasks"


@count_resource
class NTasksPerNodeResource(Resource):
    """Number of tasks per compute node."""

    name: str = "ntasks_per_node"


@count_resource
class NTasksPerGPUResource(Resource):
    """Number of tasks per GPU."""

    name: str = "ntasks_per_gpu"


@count_resource
class GPUsResource(Resource):
    """Number of GPUs."""

    name: str = "gpus"


@count_resource
class GPUsPerTaskResource(Resource):
    """Number of GPUs per task."""

    name: str = "gpus_per_task"


@count_resource
class GPUsPerNodeResource(Resource):
    """Number of GPUs per compute node."""

    name: str = "gpus_per_node"


@string_resource
class RequiredNodesResource(Resource):
    """Reqired compute nodes."""

    name: str = "required_nodes"


@string_resource
class ExcludedNodesResource(Resource):
    """Excluded compute nodes."""

    name: str = "excluded_nodes"


class PartitionResource(Resource):
    """Cluster partition."""

    name: str = "partitions"

    def check_value(self) -> None:
        """Raise error if value is not string or dictionary."""
        check_str_or_list_str(self.value)


class GenericResource(Resource):
    """Generic cluster resource (like GPU shards)."""

    name: str = "gres_per_node"

    def check_value(self) -> None:
        """Raise error if value is not string or dictionary."""
        check_str_or_dict(self.value)


@dataclass
class Resources:
    """Collection of cluster resources."""

    resources: Iterable[Resource]

    def to_dict(self) -> dict[str, str]:
        """Return dictionary reperesentation of resources."""
        return dict([res.to_string_tuple() for res in self.resources])
