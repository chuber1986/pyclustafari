"""Stub for loading JobLib files and executing them."""

import argparse
import pathlib
from pathlib import Path

import joblib
from utils import (
    State,
    get_error_file,
    get_log_file,
    get_output_file,
    get_result_file,
    get_state_file,
    redirect_io,
)


class StateUtils:
    """Manage execution state and logs."""

    def __init__(self, file):
        self.file = file

        self.statefile = get_state_file(file)
        self.statefile.touch(exist_ok=True)

        self.outfile = get_output_file(file)
        self.outfile.touch(exist_ok=True)

        self.errfile = get_error_file(file)
        self.errfile.touch(exist_ok=True)

        self.logfile = get_log_file(file)
        self.logfile.touch(exist_ok=True)

    def set_state(self, state: State):
        with self.statefile.open("w") as f:
            f.write(str(state))

    def log(self, msg: str):
        with self.logfile.open("a") as f:
            f.write(msg)
            f.write("\n")


def execute(args):
    file = Path(args.filename).expanduser().resolve()
    result = None
    fnobj = None

    utils = StateUtils(file)
    utils.set_state(State.STARTED)

    try:
        utils.log("Load job file")
        utils.set_state(State.LOAD_FILE)
        fn, args, kwargs = joblib.load(file)
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
    except Exception as e:  # pylint: disable=broad-except
        utils.log(str(e))
        utils.set_state(State.FAILED)
    finally:
        utils.log("Write output")
        utils.set_state(State.DUMP_RESULT)
        joblib.dump((fnobj, result), get_result_file(file))
        utils.log("Execution finished")
        utils.set_state(State.FINISHED)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filename",
        type=pathlib.Path,
        help="Path to the joblib file.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    execute(parse_arguments())
