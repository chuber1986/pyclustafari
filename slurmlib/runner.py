import logging
import subprocess
from pathlib import Path

from runnable import Runnable, RunInformation

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

COMMAND_TEMPLATE = r"python {} {}"


class SubprocessRunner:

    def __init__(self, workerstub: Path):
        self.workerstub = workerstub

    def run(self, function: Runnable) -> RunInformation:
        logging.info(f"Execute Runner '{self.__class__.__name__}'")
        info = RunInformation()

        file = function.tempfile
        command = COMMAND_TEMPLATE.format(str(self.workerstub), str(file)).split()
        info.output = subprocess.run(command, capture_output=True)

        return info


class SlurmRunner:

    def __init__(self, workerstub: Path):
        self.workerstub = workerstub

    def run(self, function: Runnable) -> RunInformation:
        logging.info(f"Execute Runner '{self.__class__.__name__}'")
        info = RunInformation()

        file = function.tempfile
        command = COMMAND_TEMPLATE.format(str(self.workerstub), str(file)).split()

        raise NotImplementedError
        return info
