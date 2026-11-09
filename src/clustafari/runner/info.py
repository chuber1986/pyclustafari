"""Runnable information classes."""


class RunInformation:
    """Information about an executed run."""

    #: Identifier of the backing cluster job, when the backend submitted one
    #: (set by e.g. `SlurmInformation`); `None` for local backends.
    jobid: int | None = None

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

    def cancel(self) -> None:
        """Stop the backing execution (best-effort).

        The base information has no external execution to stop; backends
        with one (subprocess worker, Slurm job) override this. Failures of
        the stop mechanism are logged by `Runnable.cancel()` and do not
        prevent the run's transition to cancelled.
        """
