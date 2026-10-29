"""Runnable information classes."""


class RunInformation:
    """Information about an executed run."""

    def __init__(self) -> None:
        """Initialize RunInformation with default values."""
        self.output: str = ""
        self.error: str = ""
        self.log: str = ""

    def terminated(self) -> bool:
        """Return True when the backing execution has ended on the cluster side.

        The base information has no knowledge of an external process or job,
        so it can never report termination; runners with an external
        execution (e.g. Slurm) override this.
        """
        return False
