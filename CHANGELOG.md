# Changelog

## Unreleased

### Added

- By-value callable serialization (issue #31): `apply`/`apply_async`/`map*`
  now accept callables that stdlib pickle cannot serialize by reference —
  lambdas, nested `def`s, `functools.partial` of either, and module-level
  `def`s defined in the dispatching `__main__` driver script (the worker
  subprocess has a different `__main__`). Job and result artifacts are
  serialized with `dill` (recursion into referenced globals enabled), owned
  by a single serializer module (`clustafari.serialization`) imported by
  both the dispatching side and the worker. `wrap_non_picklable_objects`
  remains available but is no longer required for such callables. Legacy
  stdlib-pickle/joblib artifact streams still load (the dill unpickler is a
  superset); artifact files keep the `.joblib` suffix and on-disk layout.

## 0.2.0 (2026-11-11)

### Added

- Cross-session run recovery and artifact GC (issue #18): `list_runs()`
  discovers runs under the artifacts root, `attach(run_id)` rebuilds a
  retrieval-capable handle for a run of a dead session
  (`attach(...).get(blocking=True)` returns the result or raises with the
  run's diagnostics), and `gc(max_age)` removes artifact directories of
  terminal runs older than `max_age` (`max_age=0` clears all terminal runs;
  live runs are never removed). Each run now records a small advisory
  `meta.json` (function name, UTC dispatch time, backend kind; the Slurm
  backend adds the submitted job id) — dispatch metadata only, never
  load-bearing for a run's execution.

- The artifacts root is configurable (issue #16): pass
  `ClusterContext(config, artifacts_dir=...)` to override the root for all
  runs dispatched through the context, or set the `CLUSTAFARI_ARTIFACT_DIR`
  environment variable (read lazily when the artifacts root is first
  resolved). Precedence: explicit argument → environment variable → default
  `~/.clustafari` (unchanged). Useful for pointing large-payload artifact
  I/O at a scratch filesystem instead of a small NFS-mounted home; note
  node-local scratch only suits the Subprocess backend, while the Slurm
  backend requires a root visible to both caller and worker (shared
  scratch/parallel filesystem).

- `clustafari.job` ships as package data (`clustafari/job/clustafari.job`):
  a pip-installed package is self-contained and resolves the job script from
  the installed distribution. The lazy resolver falls back to the repository
  checkout copy and then to an executable `clustafari.job` on `PATH`
  (issue #15).

- Run handles expose the worker-side progress: `run.status` returns a
  `RunStatus` (`NOT_STARTED`, `PENDING`, `STARTED`, `LOADING`, `RUNNING`,
  `DUMPING`, `FINISHED`, `FAILED`, `CANCELLED`) derived from the run's state
  file (issue #11). `str(run)` includes the current status and — for a
  Slurm-backed run — the job ID (`"fn1(1) [running, job 12345]"`), so
  `squeue`/`scancel` copy-paste works; `repr(run)` is unchanged.

### Changed

- Run artifact directories are named with `uuid4().hex` prefixed by the
  dispatched function's name instead of a `joblib.hash` over the full
  payload plus a timestamp, removing a redundant full serialization pass
  per dispatch; uniqueness per run is guaranteed by construction
  (issue #17).
- **BREAKING**: `clustafari.paths` no longer exposes import-time constants
  `CLUSTAFARI_DIR`, `JOB_FILE`, `WORKERSTUB`; use the accessor functions
  `clustafari_dir()`, `job_file()`, `workerstub()` (plus `reset_path_cache()`
  for tests) instead (issue #15).
- Importing `clustafari` performs no filesystem side effects any more:
  `~/.clustafari` is created on first use, and the job script is resolved
  lazily at config construction / dispatch time. A missing job script now
  raises `FileNotFoundError` (naming the searched locations) at first use
  instead of breaking the import (issue #15).
- The `[tool.uv.build-backend] data = { scripts = "scripts" }` install step
  is removed; `scripts/clustafari.job` moved into the package as
  `src/clustafari/job/clustafari.job` (the dev `scripts/extract_slurm_env.sh`
  stays) (issue #15).

### Fixed

- The worker publishes its artifacts atomically: the state file, the result
  dump, and the log are written to a temporary file in the artifact directory
  and renamed onto their final path (`os.replace`), so a reader on a shared
  filesystem (NFS) can no longer observe a torn write of a run that actually
  succeeded and demote it to FAILED (issue #14).
- `Runnable._read_job_file()` now logs a warning when the corrupt-result
  safety net triggers, making any residual success-to-failure demotion
  visible instead of silent (issue #14).
- An empty (freshly touched) worker state file no longer spams the log with
  `Unknown state '' ... defaulting to IDLE` warnings on every poll
  (~10x/s until the worker writes `STARTED`);
  `Runnable._read_state_file()` maps empty content to `State.IDLE` directly
  (issue #10).
- `SlurmRunner` no longer declares a never-populated `job_id` attribute; the
  submitted Slurm job ID lives only on `SlurmInformation.jobid` (issue #10).
- Logging no longer stringifies large job payloads for disabled log levels:
  `Runnable` and `BaseRunner.apply_async` log the function name instead of
  eagerly formatting the full `repr(runobj)` (issue #10).
- README/docs: the obsolete `git://` clone protocol advice is replaced with
  SSH cloning, and the invalid `uv env` command is corrected to `uv venv`
  (issue #10).
- `Runnable.get()` no longer leaves the run's `~/.clustafari/<hash>` tempdir
  behind when the execution failed: the artifacts are now deleted as soon as
  `get()` reports the failure (previously they were only removed on success or
  when the `Runnable` was garbage collected). `Runnable.__del__()` remains as
  a backstop for runs whose result is never retrieved (issue #7).
- `Runnable._read_job_file()` only degraded a corrupt result file to "no
  result" for `EOFError`; a truncated pickled result file (a torn write, e.g.
  over NFS) raises `struct.error`/`UnpicklingError`, which crashed `get()`
  with a raw deserialization error. All unreadable-result conditions
  (`EOFError`, `struct.error`, `OSError`, `ValueError`,
  `pickle.UnpicklingError`) now report the run as failed instead.

### Added

- Test coverage raised from ~82% to 99% (issue #7): new test modules for
  artifact cleanup (`tests/test_artifact_cleanup.py`), the worker stub
  (`tests/test_workerstub.py`), `Runnable` internals and state machine
  (`tests/test_runner.py`), runner error paths (`tests/test_runner_errors.py`),
  `SlurmInformation` with a mocked pyslurm Job (`tests/test_slurm_info.py`),
  `ClusterContext`/`map_async` argument handling (`tests/test_manager.py`),
  resource value corner cases (`tests/test_resources_extra.py`),
  `utils`/paths/config/`delayed` (`tests/test_utils.py`,
  `tests/test_config.py`).

### Changed

- `BaseRunner._run()` now returns `None`; the previously built-and-discarded
  `RunInformation` return values were dead code (issue #10).
- `Runnable._get_hash()` return type narrowed from `str | None` to `str`
  (`joblib.hash` always returns a string) (issue #10).
- Removed the deprecated and unused `pytest-runner` dev dependency; the prek
  pytest gate now runs with `--cov=clustafari --cov-report=term-missing` so
  the installed `pytest_cov` is actually used (issue #10).
- Switched the local/CI code-quality gate from pre-commit to
  [prek](https://github.com/j178/prek) with a native `prek.toml`; `.pre-commit-config.yaml`
  is removed. The gate covers repository-integrity checks, conventional-commit
  message linting, `uv lock`/`uv sync`, shellcheck, ruff (format + check), the
  `ty` type checker, mdformat, nbstripout, Prettier (YAML/JSON), and the
  pytest suite; run it locally with `uv run prek run --all-files`.
- Added a GitHub Actions CI pipeline (`.github/workflows/ci.yml`) analogous to
  the useful-utilities GitLab CI: a `checks` job runs the prek gate, a `docs`
  job builds the mkdocs site, and a `deploy` job publishes it to GitHub Pages.
  pyslurm is built in CI against a Slurm 26.05 client environment extracted
  from the `giovtorres/slurm-docker` image (the image PySlurm's own CI uses)
  via `scripts/extract_slurm_env.sh`.
- The documentation site now uses the mkdocs Read the Docs theme with SAL
  branding (matching the useful-utilities docs) instead of mkdocs-material;
  docs dependencies moved to a dedicated `docs` uv group
  (`uv sync --locked --group docs`).
- `pyslurm` is now a git submodule vendored at `third-party/pyslurm` (checked
  out detached at the PySlurm commit this tree was developed against,
  Slurm 26.05.x / branch 26.5.x, commit 1e97f854) instead of a git-pinned
  remote dependency; `uv sync` builds the checked-out source. Cloning now
  requires `--recurse-submodules`. To move to a new Slurm/pyslurm version,
  check out the matching branch tip in the submodule, run `uv lock`, and
  commit the updated submodule pointer.
- `test_slurm_runner_config` now skips when no Slurm is available, like the
  other Slurm runner tests.

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
