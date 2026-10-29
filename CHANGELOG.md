# Changelog

## Unreleased

### Fixed

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

- `Runnable.state` property and `Runnable.fail()` / `Runnable._finish()` helpers.
- `SlurmConfig` `time=` / `TimeResource` walltime support.
- Tests covering dummy/subprocess failure, async/timeout, and `return_object`.

### Removed

- Dead code: the unused `ClusterContext._runs` tracking, `NodeConfig.__hasattr__`
  (Python never invokes a user-defined `__hasattr__`), the import-time
  `pyprojroot.here()` call (raised when no project root marker is present), the
  `SlurmInformation` `__main__` block, and the unused `COMMAND_TEMPLATE` in the
  dummy runner.
- Tracked `.env` / `.autoenv` (both are gitignored and machine-local).
- Dead `pyproject.toml` sections (`[tool.tox]`, `[tool.pyrefly]`, a
  `src/odetect` ruff ignore, and the nonexistent `integration` test path).

### Changed

- `ClusterContext.__exit__` is now a no-op (async runs intentionally outlive the
  context) instead of an opaque `del` loop.
- CONTRIBUTING.md, README.md and the job script were corrected to match the
  actual uv / pre-commit / pytest toolchain; docs typos fixed.

## 0.1.0 (2024-03-02)

- Initial release.
