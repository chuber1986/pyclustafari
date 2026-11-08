# Proposal

## Why

There is no way to stop a dispatched run. A hanging function or wrong parameters leave a Slurm job holding its allocation until walltime expires or a subprocess worker running indefinitely; `run.get(blocking=True)` can only be aborted by killing the whole Python session. Issue #12. The README targets interactive sessions and Jupyter notebooks, where this is routine.

## What Changes

- Add `RunState.CANCELLED` as a caller-side terminal state and a new `CancelledError(StateError)`.
- Add `Runnable.cancel()`: `INITIALIZED` transitions directly to `CANCELLED`; `READY` asks the run's information object to kill the backing execution (best-effort) and transitions to `CANCELLED`; other states are idempotent no-ops.
- Add a `cancel()` hook on the information objects mirroring `terminated()`: base no-op, `SubprocessInformation` terminates/kills/reaps the worker, `SlurmInformation` cancels the Slurm job via `pyslurm.Job(jobid).cancel()`.
- A cancelled run stays cancelled: `SlurmInformation.terminated()` returns `False` once the run was cancelled by the user (a self-cancelled job is not a dead worker), and cancelled runs short-circuit `is_finished()`/`get()` before any artifact read. `get()` on a cancelled run raises `CancelledError`; temp artifacts are cleaned up.
- `ctx.cancel_all()` for map batches is explicitly out of scope (follow-up named in the issue).

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runner-backends`: every backend gains a cancellation path on its information object; subprocess workers are terminated and reaped, Slurm jobs are cancelled through the cluster interface, in-process runs transition without an external kill.
- `cluster-context-api`: run handles expose `cancel()`; retrieval from a cancelled run raises a dedicated cancellation error instead of returning a result or a generic failure.
- `slurm-job-monitoring`: a job cancelled by the user through the run handle is not misreported as a dead (abnormally terminated) job.
