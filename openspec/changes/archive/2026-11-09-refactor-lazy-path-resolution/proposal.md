# Proposal

## Why

`clustafari/paths.py` performs side effects and fragile resolution at import time: it creates `~/.clustafari` on every `import clustafari`, and resolves `JOB_FILE` with a `PATH` scan that raises `ValueError` out of the import when neither the repo checkout nor `PATH` has `scripts/clustafari.job`. A pip-installed package is therefore not self-contained — `import clustafari` fails in notebooks (the primary audience) unless the user separately installs the job script onto `PATH`.

## What Changes

- Resolve paths lazily: module-level constants become accessor functions resolved on first use (cached), so importing `clustafari` performs no filesystem side effects and no `PATH` scanning.
- **BREAKING**: `clustafari.paths` no longer exposes the module constants `CLUSTAFARI_DIR`, `JOB_FILE`, `WORKERSTUB` (import-time `Path` values). Consumers import the accessors instead.
- Ship `clustafari.job` as package data: the job script resolves from `importlib.resources.files("clustafari")` inside the installed wheel; the repo `scripts/` location and a `PATH` scan become fallbacks for dev checkouts and out-of-tree overrides, consulted only by the lazy accessor.
- Move `CLUSTAFARI_DIR.mkdir` out of import: the artifacts root is created on first use (first dispatched run / first config instantiation / defaults loading).
- Error semantics: an unresolvable job file raises a clear error at first use (dispatch/config construction), not at import.
- `scripts/` stays in the checkout for dev/ops use (slurm image extraction, CI); the packaged copy is the runtime default.
- CHANGELOG entry documenting the lazy resolution, the packaged job script, and the removed import-time constants.

## Capabilities

### New Capabilities

- `install-layout`: how the installed package locates its runtime assets (job script, worker stub) and its user state directory, with lazy resolution and fallback order.

### Modified Capabilities

- `runner-backends`: cluster and subprocess backends resolve the job script and worker stub at dispatch/config time instead of import time; an unresolvable job script fails a run at dispatch with a clear error rather than breaking `import clustafari`.
- `configuration-and-resources`: `NodeConfig`-style configs default `jobfile`/`workerstub` to lazily resolved paths at construction; the cluster preset loader still copies packaged defaults into `~/.clustafari` on first use, and the user state directory is created on first use, not at import.

## Impact

- `src/clustafari/paths.py` — lazy accessors, packaged-resource resolution, fallback chain.
- `src/clustafari/config/__init__.py`, `src/clustafari/runner/slurm/config.py`, `src/clustafari/runner/subprocess/config.py` — default parameter values call the accessors.
- `src/clustafari/runner/runnable.py`, `src/clustafari/runner/slurm/__init__.py` — create the artifacts root on first use instead of import.
- `pyproject.toml` — drop `[tool.uv.build-backend] data = { scripts = "scripts" }` in favor of in-package data (or keep both; decided in design).
- `tests/test_config.py`, new `tests/test_paths.py` — import-time side-effect tests, resolution order tests.
- `CHANGELOG.md` entry.
