# Tasks

## 1. Metadata file (protocol delta)

- [x] 1.1 Write `meta.json` atomically in `Runnable.execute()` (function name, UTC dispatch timestamp, backend kind); advisory only — unwritable/missing metadata never fails dispatch
- [x] 1.2 `SlurmRunner._run` records the submitted job id into `meta.json` right after `desc.submit()` (atomic read-modify-write)
- [x] 1.3 Tests: metadata content per backend (dummy/subprocess/slurm stub); missing/corrupt `meta.json` leaves dispatch+retrieval unaffected; file-set test updated to six files + metadata

## 2. Reconstruction path on Runnable

- [x] 2.1 Add classmethod/alternate constructor on `Runnable` rebuilding a handle from an existing run directory: state READY, protocol paths from dir + stem (stem from the single `*.joblib`), info from recorded job id (`SlurmInformation(jobid)`) or plain `RunInformation`
- [x] 2.2 Derive function identity for repr/str/logging from metadata (name property) so retrieval never unpickles the job file
- [x] 2.3 Tests: attached handle `get()` returns result / raises with diagnostics; `str(handle)` shows status and job id; attached+cancelled path removes the directory

## 3. Registry API (`clustafari/registry.py`)

- [x] 3.1 Non-creating artifacts-root resolution in `paths.py` (same precedence chain, no mkdir, honors `reset_path_cache()`)
- [x] 3.2 `list_runs(root=None)`: one-level scan, run-dir = contains `*.joblib`, read-only, tolerant meta/state readers, non-run dirs skipped, empty/missing root → empty list
- [x] 3.3 `attach(run_id, root=None)`: resolve dir by id (accept full dir name), lookup error naming run id + root on miss, delegate to the reconstruction constructor
- [x] 3.4 `gc(max_age, root=None)`: age from `dispatched_at` else dir mtime; terminal = terminal state file OR (jobid-bearing) Slurm job terminal/not tracked; `rmtree(ignore_errors=True)`; returns `GcResult(removed, remaining)`; `max_age=0` removes all terminal
- [x] 3.5 Export `list_runs`, `attach`, `gc`, `GcResult` from `clustafari/__init__.py`

## 4. Acceptance verification

- [x] 4.1 Cross-session test: dispatch in session A (subprocess runner), drop handle, `attach` + `get(blocking=True)` in session B returns the result
- [x] 4.2 GC acceptance: `gc(max_age=0)` removes all terminal-run dirs, spares non-terminal ones (incl. Slurm dead-worker dir with recorded job id)
- [x] 4.3 Full gate: `uv run pytest` green standalone, then `uvx prek run --all-files` clean before push

## 5. Docs

- [x] 5.1 README section: recovering results of orphaned runs (`list_runs`/`attach`), artifact cleanup (`gc`)
- [x] 5.2 CHANGELOG entry under Unreleased
