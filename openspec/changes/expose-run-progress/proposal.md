# Proposal

## Why

A dispatched run's worker-side progress is already written to the state file (`STARTED → LOAD_FILE → RUNNING → DUMP_RESULT → FINISHED/FAILED`), but the caller-facing `Runnable` hides it: from a Jupyter session a Slurm run pending for ten minutes is indistinguishable from one executing or hung, and the user cannot tell which Slurm job belongs to which run. Issue #11.

## What Changes

- Add a caller-facing `RunStatus` StrEnum (`NOT_STARTED, PENDING, STARTED, LOADING, RUNNING, DUMPING, FINISHED, FAILED, CANCELLED`) in `clustafari.runner.state`.
- Add `Runnable.status`: a property resolving the worker's state file (same machinery as `_read_state_file()`) to the caller-facing status. Caller terminal states short-circuit; `INITIALIZED` reports `NOT_STARTED`; a dispatched run whose backing worker/job is observed dead reports `FAILED`.
- Add `Runnable.__str__` including the current status and, when the backend has one, the Slurm job ID (from `SlurmInformation.jobid`) so `squeue`/`scancel` copy-paste works; `__repr__` stays the argument-echoing `fn(x)` form.
- Add a documented `jobid: int | None` attribute on the base `RunInformation` (set by `SlurmInformation`, `None` elsewhere).

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `cluster-context-api`: the non-blocking dispatch handle exposes worker-side progress via a `status` property and a string representation that includes the status and the backing job's ID when one exists.
