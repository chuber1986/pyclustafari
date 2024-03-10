"""Strategy for executing dumped JobLib files using slurm."""

from pathlib import Path

from runnable import RunInformation, Runnable

COMMAND_TEMPLATE = r"python {} {}"

__all__ = ["SlurmRunner"]


class SlurmRunner:
    """Runs a JobLib file on a Slurm cluster."""

    def __init__(self, workerstub: Path):
        self.workerstub = workerstub

    def run(self, function: Runnable) -> RunInformation:
        raise NotImplementedError
        # logging.info(f"Execute Runner '{self.__class__.__name__}'")
        # info = RunInformation()
        #
        # file = function.tempfile
        # command = COMMAND_TEMPLATE.format(str(self.workerstub), str(file)).split()
        #
        # return info
