#!/usr/bin/env python
"""Tests for `clustafari.workerstub` run directly (no subprocess)."""

import argparse
from pathlib import Path

import joblib
import pytest

from clustafari.utils import State, get_error_file, get_log_file, get_output_file, get_result_file, get_state_file
from clustafari.workerstub import StateUtils, execute, parse_arguments


def worker_fn(a, b, c=0):
    print("to out")
    print("to err", file=__import__("sys").stderr)
    return a + b + c


def worker_boom():
    raise ValueError("worker kaboom")


def make_jobfile(tmp_path: Path, fn, args=(), kwargs=None) -> Path:
    file = tmp_path / "job.pyjob"
    joblib.dump((fn, args, kwargs or {}), file)
    return file


class FakeArgs:
    def __init__(self, filename):
        self.filename = str(filename)


def test_execute_writes_result_files(tmp_path):
    file = make_jobfile(tmp_path, worker_fn, args=(1, 2), kwargs={"c": 0})
    execute(FakeArgs(file))

    assert joblib.load(get_result_file(file)) == (None, 3)
    assert get_state_file(file).read_text().strip() == str(State.FINISHED)
    assert get_output_file(file).read_text() == "to out\n"
    assert get_error_file(file).read_text() == "to err\n"
    log = get_log_file(file).read_text().splitlines()
    assert log[0] == "Load job file"
    assert log[-1] == "Workerstub terminated"


class _WorkerAcc:
    def __init__(self):
        self.x = 10

    def add(self, n):
        self.x += n
        return self.x


def test_execute_bound_method_records_owning_object(tmp_path):
    acc = _WorkerAcc()
    file = make_jobfile(tmp_path, acc.add, args=(5,))
    execute(FakeArgs(file))

    fnobj, result = joblib.load(get_result_file(file))
    assert result == 15
    assert fnobj is not None
    assert fnobj.x == 15
    assert get_state_file(file).read_text().strip() == str(State.FINISHED)


def test_execute_failure_records_failed_state(tmp_path):
    file = make_jobfile(tmp_path, worker_boom)
    execute(FakeArgs(file))

    assert get_state_file(file).read_text().strip() == str(State.FAILED)
    assert not get_result_file(file).exists()
    assert "worker kaboom" in get_log_file(file).read_text()


def test_execute_missing_jobfile_records_failed_state(tmp_path):
    file = tmp_path / "absent.pyjob"
    execute(FakeArgs(file))

    assert get_state_file(file).read_text().strip() == str(State.FAILED)
    assert not get_result_file(file).exists()


def test_state_utils_creates_all_files(tmp_path):
    file = tmp_path / "job.pyjob"
    utils = StateUtils(file)
    utils.set_state(State.RUNNING)

    for p in (file.with_suffix(".state"), file.with_suffix(".out"), file.with_suffix(".err"), file.with_suffix(".log")):
        assert p.exists()
    assert file.with_suffix(".state").read_text().strip() == str(State.RUNNING)


def test_parse_arguments_reads_filename():
    import sys

    old_argv = sys.argv
    sys.argv = ["workerstub", "/some/path/job.pyjob"]
    try:
        args = parse_arguments()
    finally:
        sys.argv = old_argv
    assert isinstance(args, argparse.Namespace)
    assert args.filename == Path("/some/path/job.pyjob")
