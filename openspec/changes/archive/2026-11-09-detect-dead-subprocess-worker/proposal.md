# Proposal

## Why

`SubprocessRunner._run()` discards the `subprocess.Popen` handle. If the worker process dies before writing its state file (OOM-killed, interpreter mismatch, crash during `joblib.load`), the caller-side run stays `READY` forever and `run.get(blocking=True)` polls every 0.1 s indefinitely. Issue #13. Every other backend already handles this: the dummy backend runs inline, and the Slurm backend detects dead jobs via `SlurmInformation.terminated()`.

## What Changes

- Add `SubprocessInformation(RunInformation)` (`src/clustafari/runner/subprocess/info.py`) that owns the worker's `Popen` handle.
- `SubprocessRunner._run()` stores the handle on the run (`runobj.info = SubprocessInformation(proc)`) instead of discarding it.
- `SubprocessInformation.terminated()` returns `True` when the process has exited (`poll() is not None`) while no state file appeared, so `Runnable.is_finished()` fails the run with the worker's stderr and the process exit code via the existing `_termination_error_message()` path — mirroring the Slurm backend's dead-job handling one-to-one.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runner-backends`: the subprocess backend now keeps the worker process handle and reports a dead worker (exited before writing its state file) as a failed run instead of hanging forever.
