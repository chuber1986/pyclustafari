# Proposal

## Why

A source review of `main` found seven small, independent correctness and polish defects across the runner stack (issue #10): a never-populated attribute, a dead return contract, log spam from an empty state file, eager stringification of potentially huge payloads for disabled log levels, outdated setup instructions, dead/miswired dev dependencies, and an overly wide return annotation. Individually small, but together they mislead maintainers (phantom state, phantom return contract) and degrade interactive-session performance.

## What Changes

- Delete `SlurmRunner.job_id` (never populated; the runner instance is shared per-config, so per-job state does not belong there — the submitted job ID already lives on `SlurmInformation.jobid`).
- Change `BaseRunner._run()` to return `None` (**BREAKING** for subclasses only): `apply_async` discarded the returned information object, so the built-and-returned values were dead code in all three runners. Failure-branch early returns are kept where they guard subsequent construction from unbound locals.
- `Runnable._read_state_file()` maps an empty (freshly touched) state file to `State.IDLE` directly instead of feeding `""` into `State()`, which missed and logged a warning on every 0.1 s poll until the worker wrote `STARTED`.
- Replace eager `repr(runobj)` in log calls (`Runnable.__init__`, `BaseRunner.apply_async`, and the same pattern in `Runnable.cancel()`/`execute()`) with lazy `%s`-only formatting of `runobj.get_function_name()`; `__repr__` runs `str(arg)` over every argument, so dispatching a large array built a giant string even with INFO disabled.
- Fix docs: the `git://` clone advice (protocol dropped by GitHub) becomes SSH cloning; the invalid `uv env` command becomes `uv venv` (README and `docs/installation.md`).
- Remove the deprecated, unused `pytest-runner` dev dependency; wire `--cov=clustafari --cov-report=term-missing` into the prek pytest hook so the installed `pytest_cov` is actually used by the gate.
- Narrow `Runnable._get_hash()` return type from `str | None` to `str` (`joblib.hash` always returns a string).

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runner-backends`: the cluster backend no longer carries per-job state on the runner instance; backend dispatch entry (`_run`) is a fire-and-forget `None`-returning operation, with the run's information object remaining the sole carrier of execution state.
- `runnable-artifact-protocol`: an empty state file (worker not yet reporting) is interpreted as the initial state without log noise; run logging never stringifies argument payloads; the artifact hash is typed exactly as `str`.

## Impact

- Code: `src/clustafari/runner/__init__.py`, `src/clustafari/runner/{dummy,subprocess,slurm}/runner.py`, `src/clustafari/runner/runnable.py`, `prek.toml`, `pyproject.toml`, `uv.lock`, `README.md`, `docs/installation.md`, `CHANGELOG.md`.
- API: `BaseRunner._run()` signature changes from `-> RunInformation` to `-> None`; custom runner subclasses returning an information object would break (none exist in-repo).
- Dependencies: `pytest-runner` removed from dev group; no runtime dependency changes.
- Tests: regression tests for the removed attribute, the `None` contract, empty-state-file handling, and the narrowed hash type.
