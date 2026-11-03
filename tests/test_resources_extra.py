#!/usr/bin/env python
"""Additional tests for `clustafari.resources` corner and error cases."""

import pytest

from clustafari.resources import (
    CPUPerTaskResource,
    GenericResource,
    MemoryPerNodeResource,
    PartitionResource,
    RequiredNodesResource,
    TimeResource,
    Unit,
)
from clustafari.resources.resources import (
    ResourceValue,
    check_no_unit,
    check_numeric_value,
    check_positive,
    check_str_or_dict,
    check_str_or_list_str,
)


# --- Unit ---------------------------------------------------------------
def test_unit_missing_defaults_to_default():
    assert Unit("XX") is Unit.DEFAULT


# --- ResourceValue.from_value -------------------------------------------
def test_from_value_passes_through_resource_value():
    rv = ResourceValue(123)
    assert ResourceValue.from_value(rv) is rv


def test_from_value_float_rounds_to_int():
    assert str(ResourceValue.from_value("4.0")) == "4"


def test_from_value_scientific_notation():
    assert str(ResourceValue.from_value("1e3")) == "1000"


def test_from_value_extracts_unit_from_string():
    rv = ResourceValue.from_value("12G")
    assert rv.value == "12"
    assert rv.unit == Unit.GIGA
    assert str(rv) == "12G"


def test_from_value_non_numeric_string_kept_as_value():
    rv = ResourceValue.from_value("shard:1")
    assert rv.value == "shard:1"


def test_resource_value_none_unit_defaults():
    rv = ResourceValue(5, None)
    assert rv.unit == Unit.DEFAULT


def test_resource_value_string_unit_uppercased():
    rv = ResourceValue(5, "g")
    assert rv.unit == Unit.GIGA


def test_resource_value_collection_str():
    assert str(ResourceValue({"a": 1, "b": 2})) == "a:1,b:2"
    assert str(ResourceValue(["a", "b", "c"])) == "a,b,c"
    assert str(ResourceValue({})) == ""
    assert str(ResourceValue([])) == ""


# --- check functions ----------------------------------------------------
def test_check_numeric_value_accepts_numeric():
    check_numeric_value(ResourceValue("12.5"))
    check_numeric_value(ResourceValue(3))


def test_check_numeric_value_rejects_non_numeric():
    with pytest.raises(ValueError, match="numeric"):
        check_numeric_value(ResourceValue("abc"))


def test_check_positive_rejects_negative():
    with pytest.raises(ValueError, match="positive"):
        check_positive(ResourceValue("-3"))


def test_check_positive_accepts_zero():
    check_positive(ResourceValue(0))


def test_check_no_unit_rejects_unit():
    with pytest.raises(ValueError, match="unit"):
        check_no_unit(ResourceValue(3, Unit.GIGA))


def test_check_str_or_list_str_rejects_numeric_string():
    with pytest.raises(ValueError, match="not be numeric"):
        check_str_or_list_str(ResourceValue("123"))


def test_check_str_or_list_str_rejects_numeric_list_element():
    with pytest.raises(ValueError, match="must not be numeric"):
        check_str_or_list_str(ResourceValue(["a", "123"]))


def test_check_str_or_dict_rejects_numeric_string():
    with pytest.raises(ValueError, match="not be numeric"):
        check_str_or_dict(ResourceValue("123"))


# --- Resource classes ---------------------------------------------------
def test_time_resource_accepts_hms_string():
    assert str(TimeResource("00:30:00").value) == "00:30:00"


def test_generic_resource_rejects_numeric_string():
    # "123" parses to an int, so it is rejected as the wrong type.
    with pytest.raises(ValueError, match="string or dictionary"):
        GenericResource("123")
    # "123G" stays a (numeric) string and is rejected as numeric.
    with pytest.raises(ValueError, match="not be numeric"):
        GenericResource("123G")


def test_generic_resource_accepts_dict():
    assert str(GenericResource({"shard:tesla": 1, "shard:volta": 2}).value) == "shard:tesla:1,shard:volta:2"


def test_memory_resource_float_not_integer():
    with pytest.raises(ValueError):
        MemoryPerNodeResource(12.5)


def test_partition_rejects_numeric_list_element():
    with pytest.raises(ValueError):
        PartitionResource(["a", "123"])


def test_required_nodes_accepts_list():
    assert str(RequiredNodesResource(["n1", "n2"]).value) == "n1,n2"


def test_cpu_resource_rejects_unit():
    with pytest.raises(ValueError, match="unit"):
        CPUPerTaskResource("123G")
