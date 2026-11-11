# Design

## Context

Dispatch pickles `(fn, args, kwargs)` via `joblib.dump` at `src/clustafari/runner/runnable.py:199` and loads results via `joblib.load` at `runnable.py:296`; the worker does the mirror pair in `src/clustafari/workerstub.py` (`_atomic_dump` at :38, load at :88). joblib delegates to stdlib pickle, which resolves functions by reference (`module.qualname`) — lambdas, nested defs, partials of either, and `__main__`-defined module-level functions all fail, the last because the worker subprocess has a different `__main__`. A verification pass on this tree (issue #31 comment, HEAD `cf1b128`) proved the dill swap works across all four sites with the non-Slurm suite green. `joblib` remains a project dependency for `wrap_non_picklable_objects` (public re-export in `clustafari/__init__.py`, `annotations.py`) and legacy artifact recovery paths; only the four dump/load sites switch.

## Goals / Non-Goals

**Goals:**

- All four artifact dump/load sites use one dill-based serializer module.
- Lambdas, nested defs, partials, and `__main__`-defined module-level functions dispatch successfully on Dummy and Subprocess backends.
- Lambda capture of script-level globals works (`dill.settings['recurse'] = True` pinned in the serializer module).
- Corrupt-result tolerance covers dill's deserialization error types.
- `dill` pinned as a real dependency in `pyproject.toml` + `uv.lock`.

**Non-Goals:**

- Changing the on-disk artifact layout, file naming (`.joblib` suffix stays for compatibility with `from_run_dir`/recovery globbing), or the six-file protocol.
- Migrating or rewriting previously written artifacts.
- Supporting dill-specific features beyond by-value callables (e.g. pickling entire modules/dictionaries of code).
- Cloudpickle support (decided against — see Risks).

## Decisions

1. **dill, not cloudpickle.** Both work mechanically. dill was verified end-to-end on this exact tree (364 passed, 31 deselected in the issue's verification); dill's unpickler is a stdlib-pickle superset, so old joblib/pickle-written artifacts probably still load — the safer one-time migration property; `recurse=True` gives the required globals-capture semantics with one setting.
1. **Single serializer module `src/clustafari/serialization.py`.** Owns the dill settings and `Path`-accepting `dump`/`load` helpers (dill requires open file objects; joblib accepted `Path` directly). All four call sites import from it, guaranteeing parent and worker share one protocol — mixed joblib/dill fails hard (`ModuleNotFoundError: No module named '__builtin__'`).
1. **Torn-read guard in `runnable.py` `_read_job_file` needs no new exception types.** A truncation/corruption probe on dill streams (implemented as part of this change) showed: truncated streams raise `pickle.UnpicklingError` ("pickle data was truncated"), empty files `EOFError`, garbage bytes `pickle.UnpicklingError` — all already in the guard tuple `EOFError, struct.error, OSError, ValueError, pickle.UnpicklingError`. The guard is unchanged; the corrupt-result delta scenario is covered by existing types. The probe also confirmed dill loads legacy stdlib-pickle streams (migration property).
1. **Legacy `.joblib` naming kept.** Recovery paths (`registry.py`, `Runnable.from_run_dir`) glob `*.joblib` regardless of writer; dill streams in those files are read the same way. Renaming the suffix would break recovery compatibility for zero behavior gain.

## Risks / Trade-offs

- **Artifact size grows**: by-value pickling ships referenced source/globals in the artifact. Already inherent for lambdas; bounded by user payload sizes.
- **Security surface unchanged in class**: dill unpickles arbitrary code, but stdlib pickle already did; by-value transport ships more code per artifact. Documented in the serializer module docstring.
- **`recurse=True` cost**: dill re-pickles referenced globals recursively; acceptable per the verification pass, pinned deliberately.
- **Unreproduced shutdown-order warning**: one exit-time `Runnable.__del__` `AttributeError` observed once in ~10 verification runs (interpreter-shutdown GC order, pre-existing suspicion, not proven dill-related). If it reproduces during implementation, investigate `_delete_temp_files` under shutdown GC before blaming dill.
- **Old artifacts**: dill's unpickler should read legacy streams (superset), verified only for the round-trip of new writes; recovery of pre-swap artifacts is best-effort and not a guaranteed property.
