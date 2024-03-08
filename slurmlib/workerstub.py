import argparse
from pathlib import Path

import joblib

from utils import get_result_file


def execute(args):
    file = Path(args.filename)

    fn, args, kwargs = joblib.load(file)
    result = fn(*args, **kwargs)

    joblib.dump(result, get_result_file(file))


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help="Path to the joblib file.")

    return parser.parse_args()


if __name__ == '__main__':
    execute(parse_arguments())
