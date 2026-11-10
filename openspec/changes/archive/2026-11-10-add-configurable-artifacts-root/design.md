# Design

## Context

`paths.clustafari_dir()` returns `Path.home() / ".clustafari"`, cached in `_CACHE["clustafari_dir"]` and reset by `reset_path_cache()` (issue #15 lazy-paths work). Call sites:

- `runner/runnable.py:execute()` — creates `clustafari_dir() / <hash>` and the six per-run files there.
- `runner/slurm/__init__.py:_load_default_configurations()` — copies packaged `slurm_defaults.yaml` into the state dir.
- Tests patch `HOME` + `reset_path_cache()` to isolate.

`Runnable` is created inside `BaseRunner.apply_async()` with no root knowledge; backends only read `runobj.tempfile` after `execute()`.

## Goals / Non-Goals

**Goals:**

- Precedence: explicit use-site argument → `CLUSTAFARI_ARTIFACT_DIR` (lazy) → `~/.clustafari`.
- One resolution entry point in `paths.py`; call sites stay trivial.
- Default behavior byte-identical when nothing is set.
- Per-context override covers apply / apply_async / map / map_async.

**Non-Goals:**

- No per-config (`NodeConfig`) artifacts root — the context argument is the use-site override; adding it to configs too would create two override layers with unclear precedence. Can be added later without breaking this surface.
- No migration of the Slurm presets copy (`slurm_defaults.yaml`) to the artifacts root: presets are user-editable config, not run artifacts, and must stay visible to the user on the login node.
- No automatic node-local-scratch detection or `$SLURM_JOB_ID` templating — the user passes/env-vars the concrete path; docs carry the caveat.
- No renaming/relocation of existing run directories.

## Decisions

### D1: `paths.artifacts_root(root: Path | str | None = None) -> Path`

New accessor:

```python
_ENV_VAR = "CLUSTAFARI_ARTIFACT_DIR"

def artifacts_root(root: Path | str | None = None) -> Path:
    if (d := _CACHE.get("artifacts_root")) is not None and root is None:
        return d
    resolved = (
        Path(root)
        if root is not None
        else Path(os.environ[_ENV_VAR])
        if os.environ.get(_ENV_VAR)
        else Path.home() / _STATE_DIR_NAME
    )
    resolved.mkdir(parents=True, exist_ok=True)
    if root is None:
        _CACHE["artifacts_root"] = resolved
    return resolved
```

- Explicit `root` argument bypasses the cache entirely (always mkdir + return; never cached) so a context constructed before an env change cannot poison the global resolution, and `ClusterContext(artifacts_dir=...)` needs no cache interplay.
- Env-var and default resolutions cache under `"artifacts_root"`; `reset_path_cache()` already clears it.
- Relative paths accepted as given (resolved against cwd like any `Path` use); no `~` expansion needed since env values are typically absolute — but `Path(...).expanduser()` is applied to the env var and argument for ergonomic `~/scratch` values.
- `CLUSTAFARI_DIR` (state dir) and `CLUSTAFARI_ARTIFACT_DIR` stay distinct: only the artifact root is overridable; introducing the generic `CLUSTAFARI_DIR` env var would silently move the presets copy too, which the issue does not ask for. [INFERENCE from issue wording "CLUSTAFARI_DIR / CLUSTAFARI_ARTIFACT_DIR environment variable" — the issue offers either name; we pick the precise one.]

Alternative considered: resolve everything in `Runnable.execute()` via env var only, no argument threading. Rejected: the issue's first precedence tier is the explicit argument, which must reach the per-run creation point.

### D2: Threading — `Runnable(..., artifacts_dir=None)` → `execute()` picks the root

- `Runnable.__init__` gains keyword `artifacts_dir: Path | str | None = None`, stored as `self._artifacts_dir`.
- `execute()` replaces `paths.clustafari_dir() / hash` with `paths.artifacts_root(self._artifacts_dir) / hash`.
- `BaseRunner.apply_async` forwards `artifacts_dir` from its `**kwargs`-adjacent explicit parameter (keyword-only, so user function kwargs are untouched).
- `ClusterContext.__init__(config, artifacts_dir=None)` stores it; `apply`/`apply_async`/`map`/`map_async` pass it down. `map_async` forwards to each `apply_async`.
- Backends (`DummyRunner`, `SubprocessRunner`, `SlurmRunner`) need no change: they call `runobj.execute()` and read `runobj.tempfile`.

Alternative considered: `ClusterContext.__enter__` sets a contextvar/module-global "current root". Rejected: global mutable state leaks across nested contexts and threads; explicit threading through the existing `apply_async → Runnable` call chain is 4 small diffs and testable.

### D3: Worker-side reads need no root knowledge

The Slurm job script and worker stub receive the concrete job-file path as an argument (`script_args=f"3 {sys.executable} {workerstub} {file}"`), so the worker never resolves the root itself. Node-local scratch therefore works for Subprocess backend (same machine) and any setup where the chosen root is visible to both caller and worker; docs state this.

### D4: Docs placement

- `README.md` "Usage" section: short "Artifact directory" snippet showing env var + `ClusterContext(SlurmConfig(), artifacts_dir=...)`, with the NFS/node-local-scratch guidance (shared scratch for Slurm backend; node-local scratch only for Subprocess backend).
- `docs/usage.md`: same section, kept terse.
- CHANGELOG under Unreleased → Added.

## Risks / Trade-offs

- **Caching + env var in long-lived sessions (notebooks)**: the env var is read once and cached; a user exporting the var mid-session sees no effect without `paths.reset_path_cache()`. Documented; consistent with issue #15's lazy-but-cached convention.
- **Explicit root is never cached** → repeated `mkdir(exist_ok=True)` per run: one syscall on an existing dir, negligible.
- **Same-root collision across backends**: hash includes timestamp, so distinct; unchanged from today.
- **Relative env value**: resolved against the worker's cwd on remote nodes for Slurm backend — a footgun if relative; docs recommend absolute paths.
- **Test churn**: none expected; existing tests patch `HOME`/`reset_path_cache()` which still governs the default branch. New tests monkeypatch `os.environ` and use `tmp_path` roots.
