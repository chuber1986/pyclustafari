"""Strategy for executing dumped JobLib files using slurm."""

import time
from pathlib import Path
from typing import ClassVar, override

from clustafari.runner import RunInformation

__all__ = ["SlurmInformation"]


class SlurmInformation(RunInformation):
    """Provides information about executed slurm jobs."""

    # Terminal job states as reported by `Job.state` (slurm_job_state_string).
    # Any state not listed here — including one this version of slurm does not
    # know — keeps the run waiting instead of failing it prematurely.
    _TERMINAL_STATES: ClassVar[frozenset[str]] = frozenset(
        {
            "COMPLETED",
            "CANCELLED",
            "FAILED",
            "TIMEOUT",
            "NODE_FAIL",
            "PREEMPTED",
            "BOOT_FAIL",
            "DEADLINE",
            "OUT_OF_MEMORY",
            "REVOKED",
        }
    )

    # ESLURM_INVALID_JOB_ID: the job is no longer tracked by slurmctld.
    _ESLURM_INVALID_JOB_ID: ClassVar[int] = 2017

    # Minimum interval between termination checks, in seconds. The check is an
    # RPC to slurmctld and is polled from `Runnable.is_finished()` ~10x/s.
    _CHECK_INTERVAL: ClassVar[float] = 5.0

    def __init__(self, jobid: int) -> None:
        """Initialize Slurm Information with job ID."""
        super().__init__()
        self.jobid: int = jobid
        self._terminated: bool = False
        self._terminated_checked_at: float | None = None

        from pyslurm import Job

        job = Job.load(self.jobid)
        self.out_file = Path(job.standard_output)
        self.err_file = Path(job.standard_error)

    @override
    def terminated(self) -> bool:
        """Return True when the worker ended without writing a state file.

        A healthy worker always records a terminal state (``FINISHED`` or
        ``FAILED``) before it exits, so a *clean* job exit means the state
        file exists — the parent may simply not see it yet (e.g. NFS
        negative-dentry caching), and the run must keep waiting for it.
        Only a job that reached a terminal state with an *abnormal* exit
        (non-zero code or signal, e.g. an OOM ``Killed``) can have ended
        before the worker wrote its state file.

        After slurmctld's retention window ``Job.load()`` fails with
        ``ESLURM_INVALID_JOB_ID``; by then the state file is long visible if
        it was ever written, so a still-missing file means the worker died.
        Other load errors (e.g. a transient controller problem) are not
        treated as termination.
        """
        now = time.monotonic()
        if self._terminated_checked_at is not None and now - self._terminated_checked_at < self._CHECK_INTERVAL:
            return self._terminated
        self._terminated_checked_at = now

        from pyslurm import Job, RPCError

        try:
            job = Job.load(self.jobid)
            abnormal_exit = job.exit_code != 0 or job.exit_code_signal != 0
            self._terminated = job.state in self._TERMINAL_STATES and abnormal_exit
        except RPCError as e:
            self._terminated = e.errno == self._ESLURM_INVALID_JOB_ID
        except Exception:  # noqa: BLE001
            self._terminated = False

        return self._terminated

    def debug_info(self) -> dict:
        """Get debug information of the job."""
        from pyslurm import Job

        job = Job.load(self.jobid)
        return job.to_dict()

    def __del__(self) -> None:
        """Clean up output and error files on deletion."""
        out_file = getattr(self, "out_file", None)
        err_file = getattr(self, "err_file", None)

        if out_file is not None:
            out_file.unlink(missing_ok=True)

        if err_file is not None:
            err_file.unlink(missing_ok=True)
