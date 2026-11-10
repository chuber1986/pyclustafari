# Proposal: Re-attach to orphaned runs + artifact GC (issue #18)

## Why

When the owning session dies (kernel restart, closed notebook), `Runnable` handles are lost but dispatched work keeps running on the cluster — its artifacts stay in the artifacts root forever and successful results become unrecoverable. There is also no tooling at all to inspect or clean the artifacts root, so orphaned directories accumulate.

## What Changes

- New module-level API on `clustafari` (no backend config required; artifacts root resolves via the existing explicit-arg → `CLUSTAFARI_ARTIFACT_DIR` → `~/.clustafari` chain):
  - `list_runs(root=None)` — scan the artifacts root for run directories, return lightweight descriptors (function name, run id, dispatch time, backend, job id if any, worker state).
  - `attach(run_id, root=None)` — rebuild a retrieval-capable `Runnable` handle from the surviving artifact files; `attach(...).get(blocking=True)` then retrieves a result computed in a previous session, reusing the existing retrieval semantics (poll state file, load result, harvest output, remove directory).
  - `gc(max_age, root=None)` — remove run directories older than `max_age` whose run is terminal: terminal state file, or (Slurm) job id from metadata showing a terminal/unknown-to-slurmctld job.
- Protocol extension: a small metadata file (JSON: function name, dispatch time, backend kind, job id) is written into each run directory at dispatch; the Slurm backend records the job id right after submission. This is the one-scenario delta on `runnable-artifact-protocol`.
- Assumption (recorded): module-level functions, not `ClusterContext` methods — cleanup/attach must not require constructing a backend config. Matches the `paths.artifacts_root` precedent.
- Non-goals: re-dispatching or re-queueing lost jobs (attach only retrieves already-dispatched runs); attaching to runs under roots the caller cannot read; changing retrieval semantics themselves.

## Capabilities

### New Capabilities

- `orphaned-run-recovery`: cross-session discovery and recovery of dispatched runs (`list_runs`/`attach`) and artifact garbage collection (`gc`) over the artifacts root.

### Modified Capabilities

- `runnable-artifact-protocol`: the per-run file set gains a dispatch-time metadata file (backend kind, function name, dispatch time, job id), written by the caller/backend side; the Slurm backend SHALL record the submitted job id in it.

## Impact

- Code: new module `src/clustafari/registry.py` (or similar) with `list_runs`/`attach`/`gc`; `Runnable` gains a reconstruction path from an existing run directory; `SlurmRunner._run` records the job id at submit; `Runnable.execute` writes the initial metadata; exports in `src/clustafari/__init__.py`.
- Specs: delta on `runnable-artifact-protocol` (metadata file), new `orphaned-run-recovery` spec.
- Tests: session-A → session-B round-trip (dispatch, drop handle, rebuild, `get`), `gc(max_age=0)` removes terminal and spares live runs, metadata content per backend.
- Docs: README section on recovering orphaned runs + cleanup.
