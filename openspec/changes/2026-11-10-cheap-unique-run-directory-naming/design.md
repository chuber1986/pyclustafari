# Design

## Context

`Runnable` currently derives its artifact directory name in `_get_hash()` via `joblib.hash((self.function, self.args, self.kwargs, self._timestamp))`, with `_timestamp` set to `time.monotonic_ns()` in `__init__`. Only `execute()` consumes the value (`self.tempdir = paths.artifacts_root(self._artifacts_dir) / f"{self._get_hash()}"`); nothing else references `_timestamp` or `_get_hash` in `src/`. Two tests in `tests/test_runner.py` pin the naming scheme. The directory name is never parsed back; only uniqueness and existence as a directory name matter.

## Goals / Non-Goals

Goals:

- Zero-payload-cost unique run-directory naming on the dispatch path.
- Keep the existing observable guarantee: repeated identical calls produce distinct directories.
- Slightly improved debuggability: directory names identify the dispatched function.

Non-Goals:

- Changing artifact layout, file naming, root resolution, state machine, worker protocol, or cleanup semantics.
- Making directory names deterministic or content-derived (no deduplication is intended).
- Removing joblib from the project — it still serializes the job and result files.

## Decisions

- **Name format: `f"{function_name}-{uuid4().hex}"`.** The function name prefix (via the existing `_get_function_name`, already used for the job file stem) keeps directories identifiable in `~/.clustafari` listings at no cost; the uuid4 hex body guarantees uniqueness by construction. Example: `map_async-3f2b9c….`
- **Compute the name lazily at dispatch, not in `__init__`.** The current `_timestamp` is set at construction but the hash is only computed in `execute()`; generating the uuid in `execute()` keeps `__init__` free of side effects and avoids claiming a directory name for runs that are never dispatched. `Runnable` instances are never pickled (the job payload is `(function, args, kwargs)` only), so uuid-at-init would also be safe, but lazy matches existing behavior and touches less.
- **Drop `_timestamp` and `_get_hash()` entirely.** A private attribute and method with no other callers; keeping them as aliases would preserve dead weight. The `time` import is removed with them.
- **Rework the two pinning tests.** `test_runnable_get_hash_changes_with_timestamp` and `test_get_hash_returns_str` test the removed implementation. Replace with: two identical dispatches produce two distinct artifact directories (uniqueness, the acceptance criterion), and the run-directory name starts with the dispatched function's name followed by `-` (format contract). A stronger dispatch-path assertion — monkeypatching `joblib.hash` to raise and dispatching successfully — proves no hash call remains on the hot path; add it as it directly encodes the issue's acceptance criterion.

## Risks / Trade-offs

- Directory names were previously content-derived, which allowed eyeballing relation between runs; that is lost (only the function-name prefix remains). Accepted: the issue explicitly trades this away, and the per-run artifact protocol never deduplicated.
- Collision risk of uuid4 is negligible (128 random bits, one directory per run); strictly better than the previous guarantee, which relied on `monotonic_ns()` uniqueness.
- Any user code that parsed run directory names as hashes would break — none exists in-repo; the naming is an internal detail behind `Runnable.tempdir`.
