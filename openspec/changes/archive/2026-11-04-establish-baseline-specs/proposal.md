# Proposal

## Why

The repository has no OpenSpec specs: `openspec/specs/` is empty while `src/clustafari/` already implements a complete v0.1.0 feature set (context-manager execution API, three runner backends, a pickle-over-shared-filesystem artifact protocol, Slurm job monitoring). Without a baseline, future changes have no spec-level source of truth to modify, and reviews cannot tell intended behavior from accidental behavior.

## What Changes

- Establish six durable capability specs documenting the **current, observed** behavior of `src/clustafari/` as of v0.1.0, each grounded in existing code and tests.
- No source code, tests, or docs are modified by this change — it is a documentation-only capture (spec deltas are all ADDED requirements; `specs/` starts empty).
- Known behavioral wrinkles are recorded as current behavior, not ideals: `ClusterContext.__exit__` is a no-op (async runs survive context exit); there is no cancellation API; readiness is detected only by filesystem/Slurm polling.

## Capabilities

### New Capabilities

- `cluster-context-api`: `ClusterContext` context manager and its apply/map execution methods (blocking and async variants), delegation to the runner, argument handling, and context-exit semantics.
- `configuration-and-resources`: `NodeConfig`, the resource type system and its validation, `SlurmConfig` construction (explicit, `create_config`, named `CFG_*` presets from packaged YAML defaults), and resource-attribute access.
- `runner-backends`: the three execution backends — `DummyRunner` (in-process), `SubprocessRunner` (fire-and-forget `Popen`), `SlurmRunner` (pyslurm `JobSubmitDescription` submission) — including their failure paths.
- `runnable-artifact-protocol`: per-run artifact lifecycle — joblib-serialized job files under `~/.clustafari/`, the six-file layout, the `Runnable` state machine, `get()` blocking/timeout semantics, corrupt-file tolerance, and artifact cleanup (including the GC backstop).
- `slurm-job-monitoring`: `SlurmInformation` pyslurm polling — terminal/abnormal-exit detection, RPC throttling, and error handling (including job-ID-expired RPCError).
- `serialization-support`: `delayed` and the `wrap_non_picklable_objects` re-export that make un-picklable functions and bound methods transportable.

### Modified Capabilities

- None. `openspec/specs/` is empty; this change only adds capabilities.
