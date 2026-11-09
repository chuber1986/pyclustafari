# Design

## Status resolution

`RunStatus` (StrEnum in `clustafari/runner/state.py`) is the caller-facing vocabulary; a single mapping table translates worker `State` values to it so the enum and the protocol stay decoupled.

`Runnable.status` resolution order:

1. Caller terminal states short-circuit (`FINISHED/FAILED/CANCELLED` → same-named status). This keeps the status stable after `get()` deleted the artifacts.
2. `INITIALIZED` → `NOT_STARTED`.
3. `READY`: read the state file through the existing `_read_state_file()` (silent for the empty fresh file since issue #10). Worker `IDLE` maps to `PENDING` (the job is queued/submitted but the worker has not started), `STARTED→STARTED`, `LOAD_FILE→LOADING`, `RUNNING→RUNNING`, `DUMP_RESULT→DUMPING`, `FINISHED→FINISHED`, `FAILED→FAILED`.
4. `READY` with a non-terminal state file and `self._info.terminated()` → `FAILED`: no worker will ever report again and `get()` will fail this run.

## String representation

`__repr__` stays the argument-echoing `fn(x)` (pinned by existing tests and log messages). `__str__` returns `"fn1(1) [RUNNING]"` plus `", job 12345"` when the run's information carries a job ID; `print(run)` picks this up.

## Job ID

The base `RunInformation` gains a documented `jobid: int | None = None`; `SlurmInformation` already sets `self.jobid` in `__init__`. Subprocess/Dummy backends leave it `None`.
