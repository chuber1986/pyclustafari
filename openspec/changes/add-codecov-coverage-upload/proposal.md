# Proposal

## Why

Test coverage is measured but never reported anywhere: the local prek pytest
hook already runs `uv run pytest --cov=clustafari --cov-report=term-missing`
(introduced in 927d807 for #10), but its terminal output is discarded on CI,
and the `checks` job in `.github/workflows/ci.yml` produces no coverage
artifact. Coverage status is therefore invisible on GitHub and on the
(Test)PyPI project page, where the README is rendered as the package
description. The codecov badge in the README is already active but points at
a project that has never received an upload.

## What Changes

- The CI `checks` job gets a coverage step after the prek gate:
  `uv run pytest --cov=clustafari --cov-report=xml --cov-report=term-missing -q`.
  The suite is fast on CI runners (Slurm tests skip without `srun`), so the
  double run is acceptable; deliberately NOT folding `--cov` into the prek
  pytest hook — that would slow every local commit for data only CI needs.
- The `checks` job uploads `coverage.xml` to Codecov via
  `codecov/codecov-action@v5` with the `CODECOV_TOKEN` repository secret.
- The `checks` job header comment in `ci.yml` ("no secrets are used here") is
  corrected: the job now consumes a stored secret, which also matters because
  release.yml calls this workflow via `workflow_call`.
- The README badge stays as is (already uncommented and correct — issue #29's
  premise is partly stale on this point); the remaining work is making it
  report real data.
- Local prek behavior is unchanged: the prek pytest hook keeps its current
  `--cov=clustafari --cov-report=term-missing` invocation, and this change
  resolves the open question in #10 (point 6) in favor of keeping
  `pytest_cov` wired into CI.
- One-time maintainer setup (manual, outside the repo): install the Codecov
  GitHub App on the repo and add the upload token as the `CODECOV_TOKEN`
  repository secret. Tokenless uploads are rate-limited and unreliable.
- Out of scope (explicit follow-up in #29): a minimum-coverage gate
  (`fail_ci_if_error`); no coverage threshold is introduced now.

## Capabilities

### New Capabilities

- `ci-coverage-reporting`: CI computes test coverage for `clustafari` in the
  `checks` job and uploads the report to Codecov on every push/PR, so the
  README badge and PR comments show live coverage.

### Modified Capabilities

- None. `release-publishing` only references the `checks` job as a gate; its
  requirements are unaffected by the job gaining a coverage-upload step.
