"""Important Paths collection"""

from pathlib import Path

SLURMLIB_DIR = Path.home() / ".slurmlib"
SLURMLIB_DIR.mkdir(exist_ok=True)

ROOT = Path(__file__).parent.parent
WORKERSTUB = ROOT / "slurmlib" / "workerstub.py"
JOB_FILE = ROOT / "scripts" / "slurmlib.job"
