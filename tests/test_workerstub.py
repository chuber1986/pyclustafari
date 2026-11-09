#!/usr/bin/env python
"""Tests for `clustafari.workerstub` run directly (no subprocess)."""

import argparse
from pathlib import Path

import joblib

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


def test_set_state_never_leaves_temp_file_behind(tmp_path):
    file = tmp_path / "job.pyjob"
    utils = StateUtils(file)

    for state in (State.STARTED, State.RUNNING, State.FINISHED):
        utils.set_state(state)
        assert file.with_suffix(".state").read_text().strip() == str(state)
        assert not file.with_suffix(".state.tmp").exists()


payload = list(range(200_000))


def worker_fn_large():
    return payload


class _BoomAfterArgs:
    def __getstate__(self):
        msg = "disk full mid-dump"
        raise TypeError(msg)


def worker_fn_unpicklable_result():
    return _BoomAfterArgs()


def test_execute_atomic_publication_final_paths_never_partial(tmp_path):
    """Final artifact paths never expose partial content (issue #14).

    A reader thread polls the .res/.state/.log final paths continuously while
    the worker dumps a large result. Every observed content must be either
    absent or fully valid; a torn in-place write would surface here as a
    half-readable pickle, an unknown state value, or a truncated log line.
    """
    import threading

    file = tmp_path / "job.pyjob"
    joblib.dump((worker_fn_large, (), {}), file)

    errors: list[str] = []
    observations = {"res": 0, "state": 0, "log": 0}
    stop = threading.Event()

    def poll():
        while not stop.is_set():
            try:
                res = get_result_file(file)
                if res.exists():
                    _, result = joblib.load(res)  # raises on a torn pickle
                    assert result is None or len(result) == 200_000
                    observations["res"] += 1
                state = get_state_file(file)
                if state.exists():
                    content = state.read_text()
                    # The state file is touched empty up front; any non-empty
                    # content must be a complete known state name.
                    if content.strip():
                        State(content.strip().lower())
                    observations["state"] += 1
                log = get_log_file(file)
                if log.exists():
                    for line in log.read_text().splitlines():
                        assert line, "Torn append: empty line in log"
                    observations["log"] += 1
            except Exception as e:  # noqa: BLE001
                errors.append(repr(e))
                return

    reader = threading.Thread(target=poll)
    reader.start()
    try:
        execute(FakeArgs(file))
    finally:
        stop.set()
        reader.join()

    assert not errors, f"Torn reads observed: {errors}"
    assert observations["res"] > 0
    assert observations["state"] > 0
    assert observations["log"] > 0
    assert not file.with_suffix(".res.tmp").exists()
    assert not file.with_suffix(".state.tmp").exists()
    assert not file.with_suffix(".log.tmp").exists()


def test_execute_failed_dump_leaves_no_partial_result(tmp_path):
    """A mid-dump crash never corrupts or replaces the final result path."""
    file = make_jobfile(tmp_path, worker_fn_unpicklable_result)
    result_file = get_result_file(file)

    # The worker runs fn(), which returns a _BoomAfterArgs instance; pickling
    # it inside joblib.dump fails after the temp file is opened, so the final
    # path is never touched and the failure is recorded.
    execute(FakeArgs(file))

    assert not result_file.exists()
    assert not (result_file.parent / (result_file.name + ".tmp")).exists()
    assert get_state_file(file).read_text().strip() == str(State.FAILED)


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
