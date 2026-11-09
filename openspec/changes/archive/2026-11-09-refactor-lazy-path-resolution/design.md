# Design

## Context

`src/clustafari/paths.py` currently executes at import: `CLUSTAFARI_DIR.mkdir(exist_ok=True)`, then `JOB_FILE` resolution (`ROOT/scripts/clustafari.job`, else `_find_path_to("clustafari.job")`, which raises `ValueError` when neither exists). Callers (all internal):

- `clustafari.config.NodeConfig.__init__` — default `jobfile=JOB_FILE`, `workerstub=WORKERSTUB` (evaluated at class-definition time).
- `clustafari.runner.slurm.config._SlurmConfig.__init__` — same defaults.
- `clustafari.runner.subprocess.config._SubprocessConfig.__init__` — default `workerstub=WORKERSTUB`.
- `clustafari.runner.runnable` — `CLUSTAFARI_DIR / hash` tempdir for run artifacts.
- `clustafari.runner.slurm.__init__` — `_load_default_configurations()` copies packaged `slurm_defaults.yaml` into `CLUSTAFARI_DIR` and tests monkeypatch `slurm_mod.CLUSTAFARI_DIR`.
- `tests/test_config.py` — tests `_find_path_to` directly.

Packaging: `uv_build` backend; `[tool.uv.build-backend] data = { scripts = "scripts" }` currently installs the whole `scripts/` dir (including `extract_slurm_env.sh`) to the venv's `bin/` as data — this is the mechanism the issue asks to replace for the job script. `pyproject` has no `[tool.hatch]`/package-data config today; `uv_build` defaults to `src` layout with module name `clustafari`.

## Goals / Non-Goals

**Goals:**

- Zero side effects at `import clustafari` (no mkdir, no PATH scan, no resolution errors).
- Job script resolvable from an installed wheel via `importlib.resources`.
- Dev/out-of-tree overrides still work (checkout path, PATH), resolved lazily in a fixed order.
- Clear first-use error naming all searched locations.
- Single access surface (`clustafari.paths`) so call sites stay trivial.

**Non-Goals:**

- No config file/env-var override mechanism for the job script or state dir (can be added later on the same accessors).
- No change to the job script's content or the worker stub.
- No Windows support; `PATH` fallback keeps `os.pathsep`-based splitting but the documented platform stays Linux.
- No migration shim for the old constants (this is a pre-1.0 library; the three internal consumers plus tests are the whole known usage).

## Decisions

### D1: Accessor functions with module-level cache, not `lru_cache`

`paths.py` exposes:

- `clustafari_dir() -> Path` — returns `Path.home() / ".clustafari"`, creating it on first call (`mkdir(parents=True, exist_ok=True)`). Cached only in the sense that it is idempotent; no cache invalidation concern. Tests monkeypatch `Path.home` or the module attribute — see D4.
- `job_file() -> Path` — resolution order below, cached in a module-private `_resolved: dict[str, Path]` after first success.
- `workerstub() -> Path` — `Path(workerstub.__file__)`; cheap and static, but goes through the same accessor convention for consistency.
- `reset_path_cache()` — test/interpreter-reload helper clearing the cache.

Alternative considered: `functools.lru_cache` on zero-arg functions. Works, but caching `Path.home()` output via lru_cache makes monkeypatch-based tests awkward (need `cache_clear()` in every test); an explicit tiny dict cache with a `reset_path_cache()` helper is more transparent and testable.

### D2: Job-script fallback order: packaged → checkout → PATH

1. `importlib.resources.as_file(files("clustafari") / "job" / "clustafari.job")` — if the resource exists, return it. This is the installed-wheel path (and, with `uv sync` editable installs, may resolve into the source tree — acceptable, same file).
2. Checkout fallback: `Path(__file__).parents[2] / "scripts" / "clustafari.job"` (i.e. current `ROOT/scripts/...`) — covers source checkouts where the wheel data step didn't run.
3. `PATH` scan for an executable `clustafari.job` — preserves today's out-of-tree override behavior (users who install the script onto `PATH` via the old data mechanism).
4. Else raise `FileNotFoundError` naming all three searched locations (replaces the current `ValueError` whose message doesn't include the paths).

`as_file()` returns a context-managed temp extraction for zip-like importers; for a normal wheel/filesystem install it returns the real path. The accessor uses `as_file(...).__enter__()`-free form: `files(...) / "job" / "clustafari.job"` is checked with `.is_file()` first, and only then materialized via `as_file` context manager around the return — for filesystem importers this yields the concrete path and needs no cleanup; for exotic importers the path may be ephemeral, which is acceptable (documented platform is a real filesystem install). Alternative considered: copy the packaged script to `CLUSTAFARI_DIR` on first use (like `slurm_defaults.yaml`), avoiding any as_file edge cases and giving users a visible, editable copy. Rejected for now — the job script is not user-editable config, and the packaged path is the truthful provenance; revisit if a zip-install user appears.

### D3: Packaging — ship `clustafari.job` as package data, drop the `scripts` data dir

- New file layout: `src/clustafari/job/clustafari.job` (a copy is wrong — the canonical file moves there). `scripts/clustafari.job` is **removed** from the repo; `scripts/extract_slurm_env.sh` stays (CI-only, not needed at runtime).
- `pyproject.toml`: remove `[tool.uv.build-backend] data = { scripts = "scripts" }`. `uv_build` includes all files under the module dir in the wheel by default, so `src/clustafari/job/clustafari.job` ships automatically; add `[tool.uv.build-backend] module-data = true` is unnecessary — default behavior includes it. No wheel-inclusion exclusion needed.
- CI/docs unaffected: CI uses `scripts/extract_slurm_env.sh` from the checkout, not the installed data.

Rationale for moving the canonical file rather than copying: two copies drift; the slurm runner's submission only needs the resolved path, wherever it lives. The repo `scripts/` dir keeps only ops shell scripts. Downstream effect: the issue's acceptance ("job script resolves from an installed wheel") is met by the packaged copy being the first fallback.

### D4: Call-site updates

- Config defaults become `jobfile: Path | str | None = None` → `self.job_file = jobfile if jobfile is not None else paths.job_file()` in `NodeConfig.__init__` (and equivalently for `workerstub`). This is the minimal change: default evaluated at construction, not import, and explicit user overrides still win. Same pattern in `_SlurmConfig` and `_SubprocessConfig`.
- `runnable.py`: `self.tempdir = paths.clustafari_dir() / f"{self._get_hash()}"` — the accessor creates the parent dir on first call, so `tempdir.mkdir(exist_ok=True)` continues to work.
- `slurm/__init__.py`: `_load_default_configurations()` uses `paths.clustafari_dir() / default_fname`; tests currently monkeypatch `slurm_mod.CLUSTAFARI_DIR` — switch to monkeypatching `clustafari.paths.Path.home` (or patch `clustafari_dir`) so the whole lazy chain is exercised. Also ensure the directory exists before `file.write_bytes` (the accessor guarantees it).
- `tests/test_config.py` `_find_path_to` tests: keep (function stays as the PATH fallback), but the missing-prog test now expects `FileNotFoundError` if D2 raises that — decision: keep `_find_path_to` raising `ValueError` unchanged (it is an internal helper; the *accessor* wraps it or raises its own). Simpler: `_find_path_to` keeps current behavior; the new fallback chain raises `FileNotFoundError` only when all steps fail. Existing test unchanged.

### D5: `__init__.py` import order

`paths.py` imports `clustafari.workerstub` (for `Path(workerstub.__file__)`). That import chain is unchanged; `workerstub` has no side effects. No changes needed to package `__init__` — it already only imports modules, and after this change importing `clustafari` triggers no filesystem work.

## Risks / Trade-offs

- **Editable-install path shape**: with `uv sync` (editable), fallback 1 resolves into the source tree — identical file to fallback 2, so behavior is indistinguishable; only provenance differs.
- **`as_file` on non-filesystem importers**: returns an ephemeral path. Documented platform is a normal filesystem venv; if this ever bites, D2's rejected alternative (copy-on-first-use to `CLUSTAFARI_DIR`) is the fix.
- **Removed `scripts/clustafari.job` breaks the old PATH-based data install**: users who relied on `[tool.uv.build-backend] data = { scripts = ... }` placing the job in `bin/` no longer get that; the packaged copy supersedes it. This is the intended breaking change.
- **Test churn**: `test_slurm_config_load_named_defaults` and `test_artifact_cleanup` monkeypatch module constants; they move to patching `clustafari_dir`/`Path.home`. Small, contained.
- **Caching across monkeypatched homes**: tests that patch `Path.home` must call `reset_path_cache()` (or use the `monkeypatch` fixture to patch `clustafari.paths._resolved`), else a cached path from another test leaks. Mitigated by making `reset_path_cache` a documented fixture-level helper in `tests/conftest.py` if needed.
