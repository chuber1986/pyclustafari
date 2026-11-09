# Tasks

## 1. Implement

- [x] 1.1 Add `RunState.CANCELLED` and `CancelledError(StateError)`
- [x] 1.2 Add `RunInformation.cancel()` base no-op; `SubprocessInformation.cancel()` (terminate → wait → kill → wait) ; `SlurmInformation.cancel()` (`pyslurm.Job(jobid).cancel()` + `_cancelled` flag)
- [x] 1.3 Add `Runnable.cancel()` with state-machine transitions and cancelled-state early returns in `is_finished()`/`get()` (temp files cleaned, `CancelledError` raised)
- [x] 1.4 Guard `SlurmInformation.terminated()` against self-cancellation

## 2. Test

- [x] 2.1 Unit: cancel transitions (`INITIALIZED`→`CANCELLED`, `READY`→`CANCELLED`, idempotent, no-op from `FAILED`/`FINISHED`); `get()` raises `CancelledError` on cancelled run; base `cancel()` is a no-op
- [x] 2.2 Unit (fake pyslurm): `SlurmInformation.cancel()` calls `Job.cancel`, sets `_cancelled`; `terminated()` returns `False` after self-cancel even for `CANCELLED`+signal job state; `cancel()` propagates `RPCError`
- [x] 2.3 Integration: subprocess run cancelled mid-flight → worker reaped, `get()` raises `CancelledError`; dummy run cancelled after inline finish is a no-op

## 3. Validate

- [x] 3.1 Run `openspec validate add-run-cancellation` and fix any reported issues

## 4. Land

- [x] 4.1 Full lint + test suite green; README snippet; commit
