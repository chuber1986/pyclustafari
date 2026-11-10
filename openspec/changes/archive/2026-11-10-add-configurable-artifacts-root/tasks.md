# Tasks

## 1. Artifacts-root resolution (`paths.py`)

- [x] 1.1 TDD RED: in `tests/test_paths.py` add failing tests — env var selects root (`CLUSTAFARI_ARTIFACT_DIR` set → `paths.artifacts_root()` returns and creates it); explicit argument wins over env var; nothing set → `~/.clustafari`; explicit+env cached vs uncached semantics; `reset_path_cache()` re-reads env; `~` expansion.
- [x] 1.2 GREEN: implement `paths.artifacts_root(root: Path | str | None = None)` per design D1 (env read at call time, cache only global resolutions, mkdir on first use, `expanduser`).

## 2. Threading the root to runs

- [x] 2.1 TDD RED: failing tests — `ClusterContext(DummyConfig(), artifacts_dir=tmp)` dispatches all four forms (apply/apply_async/map/map_async) creating run dirs under `tmp` with the six-file layout; env-var root used when no argument; default root untouched otherwise.
- [x] 2.2 GREEN: `Runnable.__init__(..., artifacts_dir=None)`; `execute()` uses `paths.artifacts_root(self._artifacts_dir) / hash` (design D2).
- [x] 2.3 GREEN: `BaseRunner.apply_async` gains keyword-only `artifacts_dir=None` and forwards it; `ClusterContext` stores and forwards it in `apply`/`apply_async`/`map`/`map_async`.

## 3. Docs & closeout

- [x] 3.1 `README.md` + `docs/usage.md`: "Artifact directory" section — env var, context argument, precedence; node-local scratch caveat (Subprocess backend only; Slurm backend needs a root visible to caller and worker — recommend shared scratch over home NFS).
- [x] 3.2 `CHANGELOG.md` Unreleased → Added: `CLUSTAFARI_ARTIFACT_DIR`, `ClusterContext(..., artifacts_dir=...)`, precedence, lazy read.
- [x] 3.3 Full suite green (`uv run pytest`), lint/type hooks green (`uv run prek run --all-files`).
