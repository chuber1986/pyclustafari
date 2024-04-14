#!/usr/bin/env python
"""Tests for `pyclustafari` package."""

import pytest
from resources import (
    CPUPerGPUResource,
    CPUPerTaskResource,
    ExcludedNodesResource,
    GenericResource,
    GPUsPerTaskResource,
    GPUsResource,
    MemoryPerCPUResource,
    MemoryPerGPUResource,
    MemoryPerNodeResource,
    NTasksPerGPUResource,
    NTasksPerNodeResource,
    NTasksResource,
    PartitionResource,
    RequiredNodesResource,
    Resources,
)


@pytest.mark.parametrize(
    "res, name",
    [
        (MemoryPerNodeResource, "memory_per_node"),
        (MemoryPerCPUResource, "memory_per_cpu"),
        (MemoryPerGPUResource, "memory_per_gpu"),
    ],
)
@pytest.mark.parametrize(
    "value, result",
    [(123, "123"), ("123", "123"), ("123k", "123K"), ("123G", "123G")],
)
def test_memory_resources(res, name, value, result):
    resource = res(value)
    assert resource.name == name
    assert str(resource.value) == result


@pytest.mark.parametrize(
    "res",
    [MemoryPerNodeResource, MemoryPerCPUResource, MemoryPerGPUResource],
)
@pytest.mark.parametrize(
    "value, error",
    [
        (-123, ValueError),
        ("-123", ValueError),
        (12.3, ValueError),
        ("12.3", ValueError),
        (-12.3, ValueError),
        ("-12.3", ValueError),
        (None, ValueError),
        ("str", ValueError),
    ],
)
def test_memory_resource_errors(res, value, error):
    try:
        res(value)
    except error:
        return

    assert False


@pytest.mark.parametrize(
    "res, name",
    [
        (CPUPerTaskResource, "cpus_per_task"),
        (CPUPerGPUResource, "cpus_per_gpu"),
        (NTasksResource, "ntasks"),
        (NTasksPerNodeResource, "ntasks_per_node"),
        (NTasksPerGPUResource, "ntasks_per_gpu"),
        (GPUsResource, "gpus"),
        (GPUsPerTaskResource, "gpus_per_task"),
    ],
)
@pytest.mark.parametrize(
    "value, result",
    [(123, "123"), ("123", "123")],
)
def test_cpu_resources(res, name, value, result):
    resource = res(value)
    assert resource.name == name
    assert str(resource.value) == result


@pytest.mark.parametrize(
    "res",
    [
        CPUPerTaskResource,
        CPUPerGPUResource,
        NTasksResource,
        NTasksPerNodeResource,
        NTasksPerGPUResource,
        GPUsResource,
        GPUsPerTaskResource,
    ],
)
@pytest.mark.parametrize(
    "value, error",
    [
        (-123, ValueError),
        ("-123", ValueError),
        (12.3, ValueError),
        ("12.3", ValueError),
        ("123K", ValueError),
        ("123M", ValueError),
        ("123G", ValueError),
        ("123T", ValueError),
        ("str", ValueError),
        (None, ValueError),
    ],
)
def test_cpu_resource_errors(res, value, error):
    try:
        res(value)
    except error:
        return

    assert False


@pytest.mark.parametrize(
    "res, name",
    [
        (RequiredNodesResource, "required_nodes"),
        (ExcludedNodesResource, "excluded_nodes"),
        (PartitionResource, "partitions"),
    ],
)
@pytest.mark.parametrize(
    "value, result",
    [("qwe,asd", "qwe,asd"), (["qwe", "asd"], "qwe,asd")],
)
def test_str_resources(res, name, value, result):
    resource = res(value)
    assert resource.name == name
    assert str(resource.value) == result


@pytest.mark.parametrize(
    "res",
    [RequiredNodesResource, ExcludedNodesResource, PartitionResource],
)
@pytest.mark.parametrize(
    "value, error",
    [
        ("123G", ValueError),
        (123, ValueError),
        (None, ValueError),
        ("123", ValueError),
        (["qwe", 123], ValueError),
        (["qwe", None], ValueError),
        (["qwe", "123"], ValueError),
    ],
)
def test_str_resource_errors(res, value, error):
    try:
        res(value)
    except error:
        return

    assert False


@pytest.mark.parametrize(
    "res, name",
    [(GenericResource, "gres_per_node")],
)
@pytest.mark.parametrize(
    "value, result",
    [
        ("shard:1", "shard:1"),
        ("shard:tesla:1,shard:volta:2", "shard:tesla:1,shard:volta:2"),
        ({"shard": 1}, "shard:1"),
        ({"shard:tesla": 1, "shard:volta": 2}, "shard:tesla:1,shard:volta:2"),
    ],
)
def test_dict_resources(res, name, value, result):
    resource = res(value)
    assert resource.name == name
    assert str(resource.value) == result


@pytest.mark.parametrize(
    "res",
    [GenericResource],
)
@pytest.mark.parametrize(
    "value, error",
    [
        ("123G", ValueError),
        (123, ValueError),
        (None, ValueError),
        ("123", ValueError),
        (["qwe", 123], ValueError),
        (["qwe", None], ValueError),
        (["qwe", "123"], ValueError),
    ],
)
def test_dict_resource_error(res, value, error):
    try:
        res(value)
    except error:
        return

    assert False


def test_resources():
    resources = Resources(
        [
            MemoryPerNodeResource(2342),
            MemoryPerCPUResource("2342"),
            MemoryPerGPUResource("2342g"),
            CPUPerTaskResource(312),
            CPUPerGPUResource(234),
            RequiredNodesResource("asdf,asdf"),
            ExcludedNodesResource(["asfd", "qwer"]),
            PartitionResource(["asfd", "qwer"]),
        ]
    )
    results = resources.to_dict()
    expect = {
        "memory_per_node": "2342",
        "memory_per_cpu": "2342",
        "memory_per_gpu": "2342G",
        "cpus_per_task": "312",
        "cpus_per_gpu": "234",
        "required_nodes": "asdf,asdf",
        "excluded_nodes": "asfd,qwer",
        "partitions": "asfd,qwer",
    }

    assert len(results) == len(expect)
    for k, v in expect.items():
        assert k in results
        assert results[k] == v
