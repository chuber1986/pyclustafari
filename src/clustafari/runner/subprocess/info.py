"""Information about an executed subprocess run."""

import subprocess
from typing import override

from clustafari.runner.info import RunInformation

__all__ = ["SubprocessInformation"]


class SubprocessInformation(RunInformation):
    """Provides information about an executed subprocess worker."""

    def __init__(self, proc: subprocess.Popen[bytes]) -> None:
        """Initialize Subprocess Information with the worker process handle."""
        super().__init__()
        self.proc: subprocess.Popen[bytes] = proc

    @override
    def terminated(self) -> bool:
        """Return True when the worker process ended without writing a state file.

        A healthy worker always records a terminal state (``FINISHED`` or
        ``FAILED``) before it exits, so an exited process whose state file has
        not (yet) been observed means the worker died (OOM-killed, interpreter
        mismatch, crash during job load). Until the process exits, the run
        must keep waiting.
        """
        return self.proc.poll() is not None

    def termination_error_message(self) -> str:
        """Build the failure message for a dead worker, including its exit code."""
        exit_code = self.proc.poll()
        err = self.error.strip()
        msg = f"Worker process terminated without writing a state file. Exit code: {exit_code}."
        if err:
            msg += f"\nStandard error:\n{err}"
        return msg
