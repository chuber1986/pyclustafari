"""Important Paths collection."""

from pathlib import Path

CLUSTAFARI_DIR = Path.home() / ".clustafari"
CLUSTAFARI_DIR.mkdir(exist_ok=True)

ROOT = Path(__file__).parent.parent.parent
WORKERSTUB = ROOT / "src" / "clustafari" / "workerstub.py"
JOB_FILE = ROOT / "scripts" / "clustafari.job"


JOB_FILE = JOB_FILE if JOB_FILE.exists() else Path("clustafari.job")
