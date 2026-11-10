# Tasks

## 1. Implementation

- [x] 1.1 In `src/clustafari/runner/runnable.py`: replace `_get_hash()` with a unique run-directory name `f"{_get_function_name(self.function)}-{uuid4().hex}"` computed in `execute()`; add the `uuid4` import, remove the `joblib.hash`-based method and the `_timestamp` attribute (the `time` import stays: `get()` polling uses `time.monotonic()`; joblib stays for job/result serialization).

## 2. Tests

- [x] 2.1 In `tests/test_runner.py`: remove `test_runnable_get_hash_changes_with_timestamp` and `test_get_hash_returns_str` (they pin the removed implementation).
- [x] 2.2 Add replacement coverage: two identical dispatches create two distinct artifact directories (uniqueness per call); the run-directory name is `<function-name>-<uuid-hex>`; and dispatching with `joblib.hash` monkeypatched to raise succeeds, proving no payload hash runs on the dispatch path.

## 3. Validation

- [ ] 3.1 Run the runner test module plus the full suite fast loop (`PYTHONPATH=src` against the parent venv) and confirm green.
- [ ] 3.2 Run `uvx prek run --all-files` clean before push (needs synced worktree venv).
