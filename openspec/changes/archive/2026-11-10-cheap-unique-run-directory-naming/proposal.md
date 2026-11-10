# Proposal

## Why

`Runnable._get_hash()` (`src/clustafari/runner/runnable.py`) names each run's artifact directory with `joblib.hash((function, args, kwargs, timestamp))`. This pickles the entire payload (function plus every argument) a second time on every dispatch only to produce a directory name — for large arrays this doubles serialization cost per call, and the pass cannot be cached because the timestamp changes per run. The content contributes nothing functionally: uniqueness already comes from the timestamp, and the directory is per-run, not deduplicated. Replacing the hash with a UUID removes the cost while keeping the uniqueness guarantee by construction.

## What Changes

- Replace `Runnable._get_hash()` (`joblib.hash` over the full payload plus timestamp) with a cheap unique run-directory name: `uuid4().hex`, prefixed with the dispatched function's name for debuggability (e.g. `map_async-3f2b9c…`).
- Run-directory naming is no longer content-derived; uniqueness is guaranteed by construction instead of by a hash over a monotonic timestamp.
- Remove the now-unused `_timestamp` attribute and the `joblib` import dependency on the dispatch path (joblib remains in use for job/result serialization).
- Update the `runnable-artifact-protocol` spec requirement that names the joblib-hash implementation detail; the observable behavior — unique directory per run, even for repeated identical calls — is unchanged.
- Update existing tests that pin the hash-based naming (`test_runnable_get_hash_changes_with_timestamp`, `test_get_hash_returns_str`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `runnable-artifact-protocol`: the "One artifact directory per run under the shared root" requirement currently mandates a joblib hash keyed by function, arguments, keyword arguments, and a monotonic timestamp; it is reworded to mandate a unique per-run directory name (uuid-based, function-name-prefixed) with the same observable guarantee — distinct directories per run, including repeated identical calls. All other requirements (six-file layout, state machine, worker reporting, retrieval, cleanup, logging) are untouched.
