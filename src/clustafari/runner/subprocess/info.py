"""Information about an executed subprocess run."""

import subprocess
from typing import override

from clustafari.runner.info import RunInformation

__all__ = ["SubprocessInformation"]


class SubprocessInformation(RunInformation):
    """Provides information about an executed subprocess worker."""

    # Seconds to wait after terminate() before escalating to kill().
    _GRACE_SECONDS: float = 0.5

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

    @override
    def cancel(self) -> None:
        """Terminate the worker process and reap it.

        The worker is asked to terminate first; if it is still alive after a
        short grace period it is killed. Either way the process is reaped so
        no zombie remains.
        """
        if self.proc.poll() is not None:
            return

        self.proc.terminate()
        try:
            self.proc.wait(timeout=self._GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()

    def termination_error_message(self) -> str:
        """Build the failure message for a dead worker, including its exit code."""
        exit_code = self.proc.poll()
        err = self.error.strip()
        msg = f"Worker process terminated without writing a state file. Exit code: {exit_code}."
        if err:
            msg += f"\nStandard error:\n{err}"
        return msg
