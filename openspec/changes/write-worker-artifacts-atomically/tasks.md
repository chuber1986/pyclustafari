# Tasks

## 1. Worker-side atomic writes

- [ ] 1.1 Add `_atomic_write_text(path, text)` and `_atomic_log_append()` helpers in `workerstub.py`; rewire `StateUtils.set_state()` and `StateUtils.log()` to temp-write + `os.replace` (state: `.state.tmp` → `.state`; log keeps accumulated content so each message is present after `log()` returns). Verify: `tests/test_workerstub.py` existing state/log tests still pass.
- [ ] 1.2 Dump the result atomically in `execute()`: `joblib.dump((fnobj, result), tmp_path)` then `os.replace(tmp_path, get_result_file(file))`. Verify: `test_execute_writes_result_files` passes and no `.res.tmp` remains.

## 2. Reader-side visibility

- [ ] 2.1 Log a `logger.warning` in `Runnable._read_job_file()` when the corrupt-result tolerance triggers. Verify: new test `tests/test_runner.py` asserts the warning on a corrupt result file; existing corrupt-file tests still pass.

## 3. Atomicity acceptance test

- [ ] 3.1 Add a test polling a final result path from a thread while the worker dumps a large result: every observed content is absent or fully valid (loads via `joblib.load`). Verify: `pytest tests/test_workerstub.py -k atomic`.

## 4. Docs and gate

- [ ] 4.1 Add a CHANGELOG.md entry under Unreleased describing atomic artifact writes and the reader warning (issue #14). Verify: changelog rendered section exists.
- [ ] 4.2 Run the full suite and the prek gate: `uv run pytest` and `uv run prek run --all-files`. Verify: both pass.
