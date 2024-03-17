"""Stub for loading JobLib files and executing them."""

import argparse
import sys
from pathlib import Path

import joblib
from utils import get_result_file


def execute(args):
    file = Path(args.filename)
    result = None

    try:
        fn, args, kwargs = joblib.load(file)
        result = fn(*args, **kwargs)
    except Exception as e:  # pylint: disable=broad-except
        print(str(e), file=sys.stderr)
    finally:
        joblib.dump(result, get_result_file(file))


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="Path to the joblib file.")

    return parser.parse_args()


if __name__ == "__main__":
    execute(parse_arguments())
