# Proposal

## Why

The worker writes its `.state` and `.res` artifacts with plain in-place writes (`StateUtils.set_state()` truncate-writes the final path; `execute()` joblib-dumps the result straight onto it). Over NFS — this project's deployment reality, since the artifact dir is `~/.clustafari` on the cluster's shared home — a caller-side reader can observe a torn write of a *successful* run and treat it as "no result". `Runnable._read_job_file()` then demotes the run to FAILED (issue #14; the changelog's "corrupt result file tolerated" entry documents the symptom patch).

## What Changes

- Worker writes all protocol files atomically: temp file in the same directory + `os.replace()`.
  - `StateUtils.set_state()`: write `.state.tmp` then `os.replace`.
  - `StateUtils.log()`: write `.log.tmp` snapshot then `os.replace` (append semantics preserved logically by rewriting from in-memory lines).
  - `execute()`: `joblib.dump(..., tmp_path)` then `os.replace(tmp_path, result_file)`.
- Reader hardening: when the corrupt-result tolerance in `Runnable._read_job_file()` triggers, log a `logger.warning` so a silent success→failure demotion becomes visible. The tolerance stays as a final safety net.
- Spec delta on `runnable-artifact-protocol`: the worker-side state-reporting requirement gains atomic-replacement wording (final paths appear only when complete); the "corrupt result file tolerated" scenario is clarified, and now expects a warning to be logged.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities

- `runnable-artifact-protocol`: atomic artifact publication by the worker; corrupt-result tolerance now logs a warning.

## Impact

- `src/clustafari/workerstub.py` (writer), `src/clustafari/runner/runnable.py` (reader warning).
- `tests/test_workerstub.py` (atomicity assertions), `tests/test_runner.py` (warning assertion).
- CHANGELOG.md entry.
