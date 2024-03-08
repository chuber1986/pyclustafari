from pathlib import Path


def get_result_file(file: Path):
    return file.with_stem(file.stem + "_result")
