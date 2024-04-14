"""Important Paths collection"""

from pathlib import Path

CLUSTAFARI_DIR = Path.home() / ".clustafari"
CLUSTAFARI_DIR.mkdir(exist_ok=True)

ROOT = Path(__file__).parent.parent
WORKERSTUB = ROOT / "clustafari" / "workerstub.py"
JOB_FILE = ROOT / "scripts" / "clustafari.job"
