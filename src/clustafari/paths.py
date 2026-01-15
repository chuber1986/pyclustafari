"""Important Paths collection."""

import os
from pathlib import Path

from clustafari import workerstub

CLUSTAFARI_DIR = Path.home() / ".clustafari"
CLUSTAFARI_DIR.mkdir(exist_ok=True)

ROOT = Path(__file__).parent.parent.parent
JOB_FILE = ROOT / "scripts" / "clustafari.job"
WORKERSTUB = workerstub.__file__


def _find_path_to(prog: str) -> Path:
    for p in os.environ["PATH"].split(":"):
        res = list(Path(p).glob(prog))
        if res:
            return res[0]

    msg = "Can't find '%s' in PATH."
    raise ValueError(msg, prog)


JOB_FILE = JOB_FILE if JOB_FILE.exists() else _find_path_to("clustafari.job")
