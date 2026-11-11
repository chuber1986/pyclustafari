# Tasks

## 1. Serializer module and dependency

- [x] 1.1 Add `dill` to `pyproject.toml` dependencies and run `uv lock`/`uv sync` to update `uv.lock`.
- [x] 1.2 Create `src/clustafari/serialization.py`: pin `dill.settings['recurse'] = True`, provide `dump(obj, path)` / `load(path)` helpers accepting `Path` (open file objects internally), document the shared-protocol contract and security note in the module docstring.

## 2. Switch the four call sites

- [x] 2.1 `src/clustafari/runner/runnable.py:199` dispatch dump → `serialization.dump`.
- [x] 2.2 `src/clustafari/runner/runnable.py` `_read_job_file` → `serialization.load`; truncation/corruption probe performed: dill raises `pickle.UnpicklingError` (truncated/garbage) and `EOFError` (empty) — all already inside the existing guard tuple, so the guard needed no new exception types (recorded in design.md).
- [x] 2.3 `src/clustafari/workerstub.py` `_atomic_dump` → `serialization.dump`.
- [x] 2.4 `src/clustafari/workerstub.py` dispatch load → `serialization.load`.

## 3. Regression tests (red before green)

- [x] 3.1 Lambda dispatch on Dummy backend returns the result.
- [x] 3.2 Lambda dispatch on Subprocess backend returns the result (blocking and async + kwargs).
- [x] 3.3 Lambda capturing script-level globals resolves in the worker (recursion enabled).
- [x] 3.4 Module-level `def` in a `__main__`-executed driver script dispatches on Subprocess (subprocess script fixture `tests/main_def_driver.py`).
- [x] 3.5 Lambda-returning-lambda result round-trips through the parent-side result load.
- [x] 3.6 `wrap_non_picklable_objects` smoke test (wrapper applied to a factory function, dispatched on Subprocess).
- [x] 3.7 Legacy-payload regression: module-level def, bound method, dataclass instance result unchanged after the swap (pre-existing suite green: 374 passed, 31 deselected).
- [x] 3.8 Corrupt/truncated result file still tolerated under dill error types (pre-existing `test_read_result_files_handles_corrupt_result_file` green; probe confirmed the same exception classes surface).

## 4. Verification and gate

- [x] 4.1 Full non-Slurm suite green serially: `uv run pytest tests -k "not slurm"` — 374 passed, 31 deselected (baseline 364: +11 regression tests, −1 removed implementation-pinned monkeypatch test).
- [x] 4.2 `uvx ty check --python .venv` error-set comparison vs baseline (no new errors — 129 == 129, empty diff).
- [ ] 4.3 `uvx prek run --all-files` gate clean (includes pytest with coverage); commit mdformat auto-fixes if any.
- [ ] 4.4 Conventional commit(s) with `(issue #31)` suffix; push; open PR with `Closes #31`; verify CI check-runs on the pushed SHA.
