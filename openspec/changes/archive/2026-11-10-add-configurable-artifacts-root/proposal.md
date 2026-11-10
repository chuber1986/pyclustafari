# Proposal

## Why

The artifacts root is hardcoded to `~/.clustafari` (`clustafari.paths.clustafari_dir()`). On real clusters home is an NFS share that already caused state-visibility problems (the termination-detection fix) and typically has small quotas: every run pays NFS latency and visibility penalties for its six artifact files (job pickles with potentially GB-sized arrays, results, state, logs) and pollutes a shared, backed-up home directory. The artifacts root should be pointable at node-local or shared scratch.

## What Changes

- Add a configurable artifacts root with precedence (highest first):
  1. explicit `artifacts_dir=` argument at the use site (`ClusterContext(config, artifacts_dir=...)`),
  2. the `CLUSTAFARI_ARTIFACT_DIR` environment variable, read lazily at first use (per the lazy-paths convention, issue #15),
  3. the current default `~/.clustafari` (unchanged behavior).
- Expose the resolution as `clustafari.paths.artifacts_root()` (accessor + cache + `reset_path_cache()` reset), parameterized so call sites can pass an explicit root through; the existing `clustafari_dir()` default behavior is unchanged and remains the fallback for the Slurm defaults copy (presets) which must stay visible to the user.
- Thread the explicit root through `ClusterContext` → runner → `Runnable.execute()` so every run's artifact directory is created under the resolved root; runs dispatched without an explicit root keep using the env-var/default resolution.
- Document the node-local-scratch caveat: node-local scratch (`/scratch/$SLURM_JOB_ID`) is not visible to the caller, so it only suits the Subprocess backend; the Slurm backend needs a root visible to both caller and worker, so a shared scratch (parallel) filesystem is recommended over home NFS where available.
- CHANGELOG entry documenting the new env var, the argument, and the precedence.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `install-layout`: the user state directory gains a configurable artifacts root — resolution precedence (explicit argument → `CLUSTAFARI_ARTIFACT_DIR` → `~/.clustafari`), lazy env-var reading, caching and cache reset.
- `runnable-artifact-protocol`: per-run artifact directories are created under the resolved artifacts root (explicit per-context root when given, else the global resolution) instead of unconditionally under `~/.clustafari`.
- `cluster-context-api`: the context manager accepts an optional `artifacts_dir` argument that overrides the artifacts root for all runs dispatched through it.

## Impact

- `src/clustafari/paths.py` — new `artifacts_root()` accessor (env var + default `~/.clustafari`), cache-aware, reset via `reset_path_cache()`.
- `src/clustafari/runner/runnable.py` — `Runnable` gains an artifacts-root override passed at dispatch; `execute()` creates the run directory under it.
- `src/clustafari/runner/__init__.py` (`BaseRunner.apply_async`) — forwards the artifacts root into the `Runnable`.
- `src/clustafari/manager.py` (`ClusterContext.__init__`) — accepts `artifacts_dir=None` and passes it to every dispatch call.
- `tests/test_paths.py`, new/updated tests for env-var, explicit, precedence, and cache behavior; `tests/test_artifact_cleanup.py` unaffected (default path).
- `README.md` / `docs/usage.md` — artifacts-root section with the node-local scratch caveat.
- `CHANGELOG.md` entry.
