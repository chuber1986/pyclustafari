"""Stub for loading JobLib files and executing them."""

import argparse
import pathlib
from pathlib import Path
from typing import Any

from clustafari import serialization
from clustafari.utils import (
    State,
    get_error_file,
    get_log_file,
    get_output_file,
    get_result_file,
    get_state_file,
    redirect_io,
)


def _atomic_write_text(path: Path, text: str) -> None:
    """Write text to path atomically via a temp file in the same directory.

    The final path only ever holds the complete new content: on NFS a
    concurrent reader can observe a torn in-place write, which would e.g.
    demote a successful run to FAILED when it hits a half-written result.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        f.write(text)
    tmp.replace(path)


def _atomic_dump(obj: Any, path: Path) -> None:
    """Dump a serialized payload to path atomically."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        serialization.dump(obj, tmp)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    tmp.replace(path)


class StateUtils:
    """Manage execution state and logs."""

    def __init__(self, file: Path) -> None:
        """Initialize state utils for a particular job execution."""
        self.file = file

        self.statefile = get_state_file(file)
        self.statefile.touch(exist_ok=True)

        self.outfile = get_output_file(file)
        self.outfile.touch(exist_ok=True)

        self.errfile = get_error_file(file)
        self.errfile.touch(exist_ok=True)

        self.logfile = get_log_file(file)
        self.logfile.touch(exist_ok=True)

    def set_state(self, state: State) -> None:
        """Set current execution state."""
        _atomic_write_text(self.statefile, str(state))

    def log(self, msg: str) -> None:
        """Write log message to logfile."""
        # Rewrite the accumulated log and replace: keeps append semantics
        # ("msg is in the log when this returns") without exposing a torn
        # in-place append to a concurrent reader.
        _atomic_write_text(self.logfile, self.logfile.read_text() + msg + "\n")


def execute(arguments: Any) -> None:
    """Execute serialized functions with provided arguments."""
    file = Path(arguments.filename).expanduser().resolve()
    result = None
    fnobj = None

    utils = StateUtils(file)
    utils.set_state(State.STARTED)

    try:
        utils.log("Load job file")
        utils.set_state(State.LOAD_FILE)
        fn, args, kwargs = serialization.load(file)
        if hasattr(fn, "__self__"):
            fnobj = fn.__self__

        utils.log("Start execution")
        utils.set_state(State.RUNNING)

        with (
            utils.outfile.open("a") as out,
            utils.errfile.open("a") as err,
            redirect_io(out, err),
        ):
            result = fn(*args, **kwargs)
        utils.log("Write output")
        utils.set_state(State.DUMP_RESULT)
        _atomic_dump((fnobj, result), get_result_file(file))
        utils.log("Execution finished")
        utils.set_state(State.FINISHED)
    except Exception as e:  # noqa: BLE001
        utils.log(str(e))
        utils.set_state(State.FAILED)
    finally:
        utils.log("Workerstub terminated")


def parse_arguments() -> argparse.Namespace:
    """Parse commandline arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filename",
        type=pathlib.Path,
        help="Path to the joblib file.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    execute(parse_arguments())
