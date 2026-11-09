# Tasks

## 1. Runner attribute and dispatch contract

- [x] 1.1 Delete the never-populated per-job attribute from the cluster backend runner; regression test asserts the attribute is absent after construction (`tests/test_runner_errors.py::test_slurm_runner_has_no_job_id_attribute`)
- [x] 1.2 Change `BaseRunner._run()` to return `None`; drop the dead information-object returns in all three runners, keeping failure-branch early returns where they guard subsequent construction from unbound locals; restore the package-level `RunInformation` re-export in `src/clustafari/runner/__init__.py`; regression test asserts `apply_async` returns the run handle and dispatch results still resolve (`tests/test_manager.py::test_apply_async_returns_runnable_and_discards_run_result`)

## 2. State-file and logging behavior

- [x] 2.1 Map an empty state file to the initial state in `Runnable._read_state_file()` without logging; tests assert empty content yields `State.IDLE` with no warning and non-empty content still parses (`tests/test_runner.py::test_read_state_file_empty_content_returns_idle_without_warning`, `::test_read_state_file_valid_content_still_parses`)
- [x] 2.2 Replace eager `repr(runobj)`/`repr(self)` in run lifecycle log calls (`Runnable.__init__`, `BaseRunner.apply_async`, `Runnable.cancel()`, `Runnable.execute()`) with lazy `%s`-only formatting of the function name

## 3. Types, docs, and dependency gate

- [x] 3.1 Narrow `Runnable._get_hash()` to return `str`; test asserts the hash is a string (`tests/test_runner.py::test_get_hash_returns_str`)
- [x] 3.2 Fix setup docs: replace `git://` clone advice with SSH cloning and the invalid `uv env` command with `uv venv` (`README.md`, `docs/installation.md`)
- [x] 3.3 Remove the deprecated unused `pytest-runner` dev dependency and re-lock (`pyproject.toml`, `uv.lock`); wire `--cov=clustafari --cov-report=term-missing` into the prek pytest hook (`prek.toml`)
- [x] 3.4 Record the fixes in `CHANGELOG.md` under Unreleased

## 4. Validate

- [x] 4.1 `openspec validate fix-runner-stack-code-warts` passes
- [x] 4.2 Full test suite green (`uv run pytest`, 327 passed)
- [x] 4.3 `uvx prek run --all-files` green, including the pytest hook with the new coverage flags
