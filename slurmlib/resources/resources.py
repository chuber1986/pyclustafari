"""Datastructures for SLURM recourse configurations."""

import abc
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

__all__ = [
    "Resources",
    "Unit",
    "MemoryPerNodeResource",
    "MemoryPerCPUResource",
    "MemoryPerGPUResource",
    "CPUPerTaskResource",
    "CPUPerGPUResource",
    "RequiredNodesResource",
    "ExcludedNodesResource",
    "PartitionResource",
    "GenericResource",
    "NTasksResource",
    "NTasksPerNodeResource",
    "NTasksPerGPUResource",
    "GPUsResource",
    "GPUsPerTaskResource",
]


class Unit(StrEnum):
    KILO = "K"
    MEGA = "M"
    GIGA = "G"
    TERA = "T"
    DEFAULT = ""

    @classmethod
    def _missing_(cls, _):
        return Unit.DEFAULT


def _isnumeric(value):
    pattern = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
    return pattern.match(value) is not None


def _isinteger(value):
    pattern = re.compile(r"^[+-]?(\d+)?$")
    return pattern.match(value) is not None


@dataclass
class ResourceValue:
    """ "SLURM resource value."""

    value: Any
    unit: Unit | str | None = Unit.DEFAULT

    def __post_init__(self):
        if self.unit is None:
            self.unit = Unit.DEFAULT
        elif isinstance(self.unit, str):
            self.unit = Unit(self.unit.upper())

    @classmethod
    def from_value(cls, value):
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

    def __str__(self):
        val = self.value
        if isinstance(self.value, list):
            if self.value:
                val = ",".join(self.value)
            else:
                val = ""

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
        raise ValueError(f"Resource requires numeric value, got '{val.value}'.")


def check_integer(val: ResourceValue):
    if not _isinteger(str(val.value)):
        raise ValueError(f"Resource requires integer value, got '{val.value}'.")


def check_positive(val: ResourceValue):
    if str(val.value)[0] == "-":
        raise ValueError(f"Resource requires positive value, got '{val.value}'.")


def check_no_unit(val: ResourceValue):
    if val.unit != Unit.DEFAULT:
        raise ValueError(f"Resource must not specify a unit, got '{val.unit}'.")


def check_str_or_dict(val: ResourceValue):
    if isinstance(val.value, str):
        if _isnumeric(val.value):
            raise ValueError(f"Resource must not be numeric, got '{val.value}'.")
        return

    if not isinstance(val.value, dict):
        raise ValueError(
            f"Resource nust be a string or dictionary, got '{type(val.value)}'."
        )


def check_str_or_list_str(val: ResourceValue):
    if val.unit != Unit.DEFAULT:
        raise ValueError(f"Resource must not specify a unit, got '{val.unit}'.")

    if isinstance(val.value, str):
        if _isnumeric(val.value):
            raise ValueError(f"Resource must not be numeric, got '{val.value}'.")
        return

    if not isinstance(val.value, Iterable):
        raise ValueError(
            f"Resource must be of type str or list of strings, got '{type(val.value)}'."
        )

    for v in val.value:
        if not isinstance(v, str):
            raise ValueError(
                f"Resource must be of type str or list of strings, got list value of type '{type(v)}'."
            )

        if _isnumeric(v):
            raise ValueError(
                f"Resource element values must not be numeric, got '{type(v)}'."
            )


@dataclass
class Resource(abc.ABC):
    """Base class for SLURM resources."""

    value: ResourceValue | Any
    name: str = field(init=False)

    def check_value(self):
        pass

    def __post_init__(self):
        self.value = ResourceValue.from_value(self.value)
        self.check_value()

    def to_string_tuple(self):
        return self.name, str(self.value)


def positive_integer_resource(cls):
    def check_value(self):
        check_integer(self.value)
        check_positive(self.value)

    cls.check_value = check_value
    return cls


def count_resource(cls):
    def check_value(self):
        check_integer(self.value)
        check_positive(self.value)
        check_no_unit(self.value)

    cls.check_value = check_value
    return cls


def string_resource(cls):
    def check_value(self):
        check_str_or_list_str(self.value)

    cls.check_value = check_value
    return cls


@positive_integer_resource
class MemoryPerNodeResource(Resource):
    name: str = "memory_per_node"


@positive_integer_resource
class MemoryPerCPUResource(Resource):
    name: str = "memory_per_cpu"


@positive_integer_resource
class MemoryPerGPUResource(Resource):
    name: str = "memory_per_gpu"


@count_resource
class CPUPerTaskResource(Resource):
    name: str = "cpus_per_task"


@count_resource
class CPUPerGPUResource(Resource):
    name: str = "cpus_per_gpu"


@count_resource
class NTasksResource(Resource):
    name: str = "ntasks"


@count_resource
class NTasksPerNodeResource(Resource):
    name: str = "ntasks_per_node"


@count_resource
class NTasksPerGPUResource(Resource):
    name: str = "ntasks_per_gpu"


@count_resource
class GPUsResource(Resource):
    name: str = "gpus"


@count_resource
class GPUsPerTaskResource(Resource):
    name: str = "gpus_per_task"


@count_resource
class GPUsPerNodeResource(Resource):
    name: str = "gres_per_node"


@string_resource
class RequiredNodesResource(Resource):
    name: str = "required_nodes"


@string_resource
class ExcludedNodesResource(Resource):
    name: str = "excluded_nodes"


@string_resource
class PartitionResource(Resource):
    name: str = "partitions"


class GenericResource(Resource):
    name: str = "gres_per_node"

    def check_value(self):
        check_str_or_dict(self.value)


@dataclass
class Resources:
    resources: list[Resource]

    def to_dict(self) -> dict[str, str]:
        return dict([res.to_string_tuple() for res in self.resources])


def main():
    resources = Resources([])

    print(resources.to_dict())


if __name__ == "__main__":
    main()
