# Tasks

## 1. Implement

- [ ] 1.1 Add `RunStatus` StrEnum and worker-`State` → caller-status mapping in `clustafari/runner/state.py`; `jobid: int | None` on `RunInformation`
- [ ] 1.2 Add `Runnable.status` (terminal short-circuit, `INITIALIZED` → not-started, state-file mapping, dead-worker → failed) and `Runnable.__str__` with status + optional job ID

## 2. Test

- [ ] 2.1 Unit `tests/test_runnable_status.py`: every state-file value maps to the intended status; `INITIALIZED` → not-started; terminal/cancelled stable after artifact removal; dead worker → failed; `__repr__` unchanged; `__str__` contains status and job ID (fake info)
- [ ] 2.2 Integration: subprocess run observed `RUNNING` mid-flight then `FINISHED`; Slurm `str(run)` contains the job ID (skipif no `srun`)

## 3. Validate

- [ ] 3.1 Run `openspec validate expose-run-progress` and fix any reported issues

## 4. Land

- [ ] 4.1 Full lint + test suite green; README snippet; CHANGELOG entry; commit
- [ ] 4.2 Sync delta into `openspec/specs/cluster-context-api/spec.md`, archive change, push branch
