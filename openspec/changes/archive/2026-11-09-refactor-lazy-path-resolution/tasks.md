# Tasks

## 1. Lazy path accessors (`paths.py`)

- [x] 1.1 Rewrite `src/clustafari/paths.py`: remove import-time `CLUSTAFARI_DIR`/`JOB_FILE`/`WORKERSTUB` constants, `mkdir`, and the module-level `JOB_FILE = ... else _find_path_to(...)` resolution; add accessors `clustafari_dir()`, `job_file()`, `workerstub()`, plus `reset_path_cache()` (design D1).
- [x] 1.2 Implement `job_file()` fallback chain: packaged `importlib.resources.files("clustafari") / "job" / "clustafari.job"` → checkout `Path(__file__).parents[2] / "scripts" / "clustafari.job"` → executable on `PATH` via `_find_path_to` → raise `FileNotFoundError` naming all searched locations (design D2). Cache resolution in a module-private dict.
- [x] 1.3 `clustafari_dir()`: return `Path.home() / ".clustafari"`, creating it with `mkdir(parents=True, exist_ok=True)` on first call; no directory creation at import.

## 2. Packaging: job script as package data

- [x] 2.1 `git mv scripts/clustafari.job src/clustafari/job/clustafari.job`; keep `scripts/extract_slurm_env.sh` in place.
- [x] 2.2 `pyproject.toml`: remove `[tool.uv.build-backend] data = { scripts = "scripts" }`.
- [x] 2.3 Verify wheel contents: `uv build --wheel`, inspect the wheel for `clustafari/job/clustafari.job` and absence of installed `bin/` script data.

## 3. Call-site migration

- [x] 3.1 `src/clustafari/config/__init__.py` (`NodeConfig.__init__`): change defaults to `jobfile: Path | str | None = None` / `workerstub: Path | str | None = None`, resolve via `clustafari.paths` accessors when `None` (design D4).
- [x] 3.2 `src/clustafari/runner/slurm/config.py` (`_SlurmConfig.__init__`): same lazy-default pattern.
- [x] 3.3 `src/clustafari/runner/subprocess/config.py` (`_SubprocessConfig.__init__`): same lazy-default pattern for `workerstub`.
- [x] 3.4 `src/clustafari/runner/runnable.py`: replace `CLUSTAFARI_DIR / f"{self._get_hash()}"` with `paths.clustafari_dir() / ...`.
- [x] 3.5 `src/clustafari/runner/slurm/__init__.py`: `_load_default_configurations()` uses `paths.clustafari_dir()`; ensure directory creation happens before `file.write_bytes`.

## 4. Tests

- [x] 4.1 New `tests/test_paths.py`: clean-import test (no `~/.clustafari` created, no resolution error, using a subprocess `python -c "import clustafari"` with patched HOME); packaged-resolution test; checkout-fallback test; PATH-fallback test; all-missing → `FileNotFoundError` naming locations; caching + `reset_path_cache()` behavior.
- [x] 4.2 Update `tests/test_config.py`: `_find_path_to` tests unchanged; monkeypatch-based tests that referenced module constants (`slurm_mod.CLUSTAFARI_DIR`) now patch `clustafari.paths` (e.g. `Path.home` or the accessor) with `reset_path_cache()` between tests.
- [x] 4.3 Update `tests/test_artifact_cleanup.py`: patch the state-dir accessor instead of importing `CLUSTAFARI_DIR`.
- [x] 4.4 Add a regression test proving a `SlurmConfig`/`NodeConfig` can be constructed with no checkout `scripts/clustafari.job` and no `PATH` copy (installed-layout simulation).

## 5. Docs & closeout

- [x] 5.1 Update `docs/installation.md` / `docs/usage.md` if they mention the job script location or `scripts/` install mechanism.
- [x] 5.2 CHANGELOG.md entry under Unreleased: lazy path resolution (no import-time side effects), packaged job script, **BREAKING** removal of `clustafari.paths` module constants.
- [x] 5.3 Full suite green (`uv run pytest`), lint/type hooks green (`uv run prek run --all-files`).
