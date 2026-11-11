# Proposal

## Why

`ClusterContext.apply/apply_async/map*` fail on any callable that stdlib `pickle` cannot serialize by reference: lambdas, nested `def`s, `functools.partial` of either, and — most commonly — module-level `def`s in the user's `__main__` driver script (the worker subprocess has a different `__main__`, so by-reference resolution fails). The failure surfaces asynchronously from `get()` as an opaque `StateError` with the real cause buried in the worker log. Issue #31 additionally documents that the documented `wrap_non_picklable_objects` workaround has no direct test coverage.

## What Changes

- Switch the artifact serializer for the four load-bearing dump/load sites (dispatch dump, parent-side result load, worker result dump, worker dispatch load) from joblib/stdlib-pickle to **dill**, which pickles callables **by value**.
- Add a small serializer module (`src/clustafari/serialization.py`) owning the dill configuration (notably `dill.settings['recurse'] = True` for lambda global-capture support) and the `Path`-accepting dump/load helpers, so parent and worker always speak the same protocol.
- Extend the corrupt-result torn-read guard in `runnable.py` with dill's equivalent exception types.
- Add `dill` as a real project dependency (`pyproject.toml` + `uv.lock`).
- Add regression tests: lambda dispatch on Dummy and Subprocess backends, lambda capturing script-level globals, lambda-returning-lambda, module-level `def` in a `__main__`-executed driver script on Subprocess, and a `wrap_non_picklable_objects` smoke test (previously untested).
- Record the dill-vs-cloudpickle decision (dill: verified end-to-end on this tree in issue #31's verification pass, unpickles legacy stdlib-pickle streams as a superset, `recurse` gives the required globals-capture semantics).

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `serialization-support`: the artifact serializer SHALL be dill-based (by-value callable transport), configured via a dedicated serializer module; dispatch SHALL accept callables stdlib pickle cannot serialize by reference, including lambdas, nested defs, and `__main__`-defined module-level functions.
- `runnable-artifact-protocol`: the corrupt-result tolerance in result retrieval SHALL also cover dill deserialization errors; job/result artifacts continue to share the same on-disk protocol between parent and worker.
