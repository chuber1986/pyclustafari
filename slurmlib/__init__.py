"""Top-level package for SlurmLib."""

from pathlib import Path

from pyprojroot import here

SLURMLIB_DIR = Path.home() / ".slurmlib"
SLURMLIB_DIR.mkdir(exist_ok=True)

ROOT = Path(__file__).parent.parent
WORKERSTUB = ROOT / "slurmlib" / "workerstub.py"

here()

__author__ = """Christian Huber"""
__email__ = "hiddenaddress@gmail.com"
__version__ = "0.1.0"
__license__ = "MIT"
__copyright__ = f"Copyright © 2024, {__author__}. All rights reserved."
