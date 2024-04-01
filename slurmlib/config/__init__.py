"""Run configurations package."""

import abc
from dataclasses import dataclass
from pathlib import Path

from slurmlib import JOB_FILE, WORKERSTUB


@dataclass
class NodeConfig(abc.ABC):
    """Node configuration class."""

    def __init__(
        self, jobfile: Path | str = JOB_FILE, workerstub: Path | str = WORKERSTUB
    ) -> None:
        self.job_file = jobfile
        self.workerstub = workerstub
