# Changelog

## Unreleased

### Fixed

- A failed run preparation (`Runnable.execute()` — hashing, temp-dir creation,
  or joblib serialization) only failed the run for `RuntimeError`; an
  unpicklable function or argument raised `PicklingError` and a temp-dir or
  write failure raised `OSError`, both of which leaked out of
  `apply_async` / `apply` as raw exceptions instead of producing a failed run.
  `execute()` now catches the preparation error, records it on the run, and
  fails it; `get()` then raises `StateError` with the underlying error text,
  consistent with a function-execution failure.
- The runners no longer proceed after a failed preparation: `DummyRunner` no
  longer runs the function and then dies in `finish()` with a spurious
  `RunnableStateError`; `SubprocessRunner` no longer spawns a worker for a
  job file that was never written; and `SlurmRunner`'s unreachable
  `if file is None` check (dead code once a failed prepare leaves the job file
  unset) is replaced by the same failed-run early return plus an invariant
  assert.
- A Slurm job whose worker was killed before it could write its state file
  (e.g. the kernel OOM-killed the worker before the interpreter even started)
  made `Runnable.get()` / `apply()` wait forever. `SlurmInformation.terminated()`
  now detects a terminal job with an abnormal exit (non-zero exit code or
  signal, e.g. `Killed`) — a clean `COMPLETED 0:0` still means the state file
  is on its way, and the run keeps waiting for it — and `Runnable.is_finished()`
  fails such runs with the job's standard error so `get()` raises `StateError`
  promptly.
- `test_slurm_runner_config` requested `MemoryPerNodeResource(value="10")`
  (10 MB), which cannot run a Python interpreter and was OOM-killed by Slurm;
  it now requests 1 GB.
- Resource value validation was dead for all decorator-based resources
  (`MemoryPer*Resource`, `CPUPer*Resource`, `NTasks*Resource`, `GPUs*Resource`,
  `RequiredNodesResource`, `ExcludedNodesResource`, `TimeResource`). `type_check`
  was an annotated dataclass field whose no-op default shadowed the validators
  set on the class; it is now a `ClassVar`.
- `GenericResource` / `PartitionResource` raised `TypeError` where the rest of the
  module raises `ValueError`; aligned to `ValueError`.
- `SlurmInformation.__del__` raised `AttributeError` (and a
  `PytestUnraisableExceptionWarning`) when the job could not be loaded; cleanup is
  now guarded.
- `DummyRunner` re-raised the underlying function exception from
  `apply_async`; it now fails the run and raises `StateError` from `get()` like
  the other runners.
- `DummyRunner` ignored `return_object=True` and discarded captured output; both
  are now handled.
- `DummyRunner` captured `str(StringIO(...))` — the buffer's repr, not its
  contents — into `info.output` / `info.error`; it now uses `getvalue()`.
- `DummyRunner`'s failure path doubled the error text (the handler assigned
  `info.error = str(e)` and `Runnable.fail()` appended the same message to the
  same info object); the redundant assignment is removed.
- `DummyConfig` / `SubprocessConfig` string representations dropped the first
  character of the class name (e.g. `ubprocessConfig({})`); `__str__` /
  `__repr__` are now implemented once on `NodeConfig`.
- `SubprocessRunner` ran the worker synchronously (no `apply_async`/timeout
  benefit) and used `os.environ["_"]` as the interpreter; it now uses
  `sys.executable` and a non-blocking `Popen`, with the caller's CWD added to the
  worker's `PYTHONPATH` so test-/project-local functions can be imported.
- `SlurmRunner` used `os.environ["_"]` and let a failed `submit()` surface as an
  unhandled error; it now uses `sys.executable` and fails the run.
- `Runnable.get()` computed the timeout from a sleep counter (drift); it now uses
  `time.monotonic()` with a deadline.
- `StateError`, `RunnableStateError` and `TimeoutException` subclassed
  `BaseException`, so broad `except Exception` blocks missed them; they now
  subclass `Exception`.
- `import clustafari` required a working `pyslurm` even for `DummyConfig` /
  `SubprocessConfig`; `pyslurm` is now imported lazily, only by the Slurm runner.
- `clustafari.job` referenced an undefined `$condaname`, used `exit -1`, and
  duplicated the "system interpreter" case; the script is now robust and
  shellcheck-clean.

### Added

- `Runnable.state` property and `Runnable.fail()` / `Runnable.finish()` helpers.
- `SlurmConfig` `time=` / `TimeResource` walltime support.
- Tests covering dummy/subprocess failure, async/timeout, and `return_object`.

### Removed

- Dead code: the unused `ClusterContext._runs` tracking, `NodeConfig.__hasattr__`
  (Python never invokes a user-defined `__hasattr__`), the import-time
  `pyprojroot.here()` call (raised when no project root marker is present), the
  `SlurmInformation` `__main__` block, and the unused `COMMAND_TEMPLATE` in the
  dummy runner.
- Tracked `.env` / `.autoenv` (both are gitignored and machine-local).
- The `clustafari` console script entry point, which pointed at a
  `clustafari.main` that no longer exists since the 2024 packaging refactor
  (the old `main()` was a hard-coded development demo never ported into the
  package); invoking `clustafari` crashed with `ImportError`. The package is
  used through the `ClusterContext` API only, and no CLI was ever
  documented, so the dead entry point is removed.
- Dead `pyproject.toml` sections (`[tool.tox]`, `[tool.pyrefly]`, a
  `src/odetect` ruff ignore, and the nonexistent `integration` test path).

### Changed

- Simplified the runner stack without behavior changes:
  `RunInformation` now uses plain attributes instead of pass-through
  properties and its never-read `result` field is gone (results live on the
  `Runnable`); `NodeConfig` drops the no-op `@dataclass` decorator and its
  `__getattribute__` override in favor of a standard `__getattr__` resource
  fallback; `BaseRunner.map_async` replaces its sentinel count bookkeeping with
  a direct length check; `SlurmConfig.create_config` uses a single
  (resource class, value) spec list instead of two parallel lists; and the
  top-level package replaces its `__exports__` / `_set_attributes`
  `globals()` machinery with plain imports and `__all__`.
- `ClusterContext.__exit__` is now a no-op (async runs intentionally outlive the
  context) instead of an opaque `del` loop.
- CONTRIBUTING.md, README.md and the job script were corrected to match the
  actual uv / pre-commit / pytest toolchain; docs typos fixed.

## 0.1.0 (2024-03-02)

- Initial release.
