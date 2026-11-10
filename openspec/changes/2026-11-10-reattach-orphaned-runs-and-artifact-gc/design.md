# Design

## Context

Run artifact directories live under the resolved artifacts root (explicit arg → `CLUSTAFARI_ARTIFACT_DIR` → `~/.clustafari`, `paths.artifacts_root()`), named `<function-name>-<uuid4hex>`, containing six stem-derived files (`.joblib`, `.res`, `.out`, `.err`, `.log`, `.state`). Dispatch goes through `Runnable.execute()` (dir + six files + joblib dump); the Slurm backend gets its job id from `JobSubmitDescription.submit()` and keeps it only in memory (`runobj.info = SlurmInformation(jobid)`). Retrieval semantics (blocking poll of the state file, cluster-side death detection, timeout, result loading, output harvesting, directory removal) live in `Runnable.get()`.

## Goals / Non-Goals

**Goals:**

- Recover results of runs from a previous session: discover, attach, `get`.
- Clean up terminal-run artifacts by age: `gc(max_age)`.
- One new small per-run file (metadata) recorded at dispatch; the Slurm job id survives the session.

**Non-Goals:**

- Re-dispatching/re-queueing lost jobs (per issue: attach retrieves only already-dispatched runs).
- Any change to worker-side files or the worker stub.
- Change to retrieval semantics themselves — `attach` reuses them.

## Decisions

### D1: Module-level functions, no context required

`list_runs(root=None)`, `attach(run_id, root=None)`, `gc(max_age, root=None)` as module-level functions exported from `clustafari`, implemented in a new `clustafari/registry.py`. Rationale: recovery and cleanup must work without a backend config; `paths.artifacts_root()` already resolves the root the same way. Alternative rejected: `ClusterContext` methods would require constructing a config just to clean up.

### D2: One JSON metadata file (`meta.json`), advisory

Written at `Runnable.execute()` (atomic write, same pattern as the worker's temp+rename) containing `{"function", "dispatched_at" (UTC ISO-8601), "backend"}`; `SlurmRunner._run` adds `"jobid"` right after successful submission (atomic read-modify-write: re-read, update, temp+rename). Metadata is advisory: a missing/corrupt `meta.json` never fails dispatch, execution, or retrieval. Rationale: the issue explicitly predicts a one-file protocol delta; JSON keeps it human-inspectable; atomicity for the file we ourselves may read in a concurrent session. Alternative rejected: encoding the job id into the directory name — would make `list_runs` parsing backend-dependent and break the existing naming spec.

### D3: Reconstruction reuses `Runnable` internals

`attach` builds a `Runnable` via `__new__` (bypassing `__init__`) and sets state `READY`, protocol file paths derived from the run dir + stem (the stem is recovered from the single `*.joblib` file in the dir), and a `SlurmInformation`-from-jobid info object when `meta.json` records a job id. No re-pickling of the job file is needed for retrieval — `get()` never needs `function`/`args`/`kwargs` to return a result or raise with diagnostics (repr/str of the attached handle derives the function name from `meta.json` instead of the pickled function; a `name` property is added and used by `get()`'s failure message path, repr, and `__del__` logging).

D3 relies on the following `get()` path facts (verified by reading `Runnable.get()`): retrieval never touches `self.function` (the failure message uses `self._info.log`/`self._info.error`, not the repr), retrieval never touches `self._info` beyond `.log`, `.error`, `.output`, `.cancel()`, `termination_error_message()` — so an attached run with a recorded job id reconstructs `SlurmInformation(jobid)` for death detection and best-effort `cancel()`, and one without falls back to a `RunInformation` whose `terminated()` is `False` (keeps polling on the state file only; `list_runs`/`gc` carry the cluster-side terminal check for jobid-bearing runs, and without a jobid there is nothing to query).

### D4: `gc` semantics

`gc(max_age, root=None)` removes run dirs with `mtime <= now - max_age` (directory mtime approximates dispatch time; metadata `dispatched_at` when parseable takes precedence) whose run is terminal: state file ∈ {finished, failed} — via the same tolerant reader used by the caller-side state machine — or (Slurm, jobid present) `SlurmInformation(jobid).terminated()` / terminal job state, applying the existing 5 s check-interval cache to avoid RPC storms. Skips non-run dirs (those without a `*.joblib` file) and tolerates concurrent removal (`shutil.rmtree(..., ignore_errors=True)`, matching `_delete_temp_files`). Returns `GcResult(removed, remaining)`, a small dataclass.

### D5: Discovery is lightweight and read-only

`list_runs` iterates one level of the root; a directory qualifies as a run dir iff it contains a `*.joblib` file; reads only `meta.json` + `.state` (tolerant readers, missing → defaults); never creates the root (unlike `artifacts_root()`, `list_runs` uses a non-creating resolver variant, honoring the same precedence chain). Non-creating resolution is a small addition to `paths.py` (e. g. `artifacts_root_resolve_only()` — naming at implementation time).

### D5 relies on: `paths.artifacts_root()` creates + caches the root; `list_runs` must not create it

### D6: Cross-session pickle risk

The job file (and result file) contain pickled data pickled by the previous session; unpickling in the new session uses the same codebase — user code classes must be importable in the new session anyway for the result to unpickle; the same constraint applies to `joblib.load` of `.res` today. Documented, not solved: cross-version unpickling is out of scope.

## Risks / Trade-offs

- **Directory mtime vs dispatch time for GC age**: mtime updates on any dir entry change, so a long-running live run's dir can look "old" — mitigated by the terminal-state gate: only terminal runs are ever removed; metadata `dispatched_at` is used when parseable.
- **Concurrent session interference**: two sessions GC'ing or one attaching while another GCs — concurrent-removal tolerance (`rmtree(ignore_errors=True)`) and `get()`'s existing missing-file tolerance cover this; a run removed between `list_runs` and `attach` raises the lookup error.
- **`Runnable.__new__` reconstruction is the riskiest piece** — it bypasses `__init__` and depends on which attributes `get()` actually touches; the cross-session acceptance test (dispatch in subprocess session A → attach+`get` in session B) is written against this exact path.
- **pyslurm RPC load from `gc`**: the 5 s check-interval cache in `SlurmInformation.terminated()` applies per instance; GC creates one instance per jobid-bearing dir, so an RPC per dir at most.
- **`meta.json` advisory rule vs strict spec file-set** ("exactly six files") — the protocol spec's file-set requirement is modified to "six + metadata", so no contradiction remains.
