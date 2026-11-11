# Spec Delta

## Purpose

Define how CI reports test coverage for the `clustafari` package: the
`checks` workflow job computes coverage and uploads it to Codecov on every
push and pull request, so coverage status is visible via the README badge,
Codecov checks, and PR comments.

## ADDED Requirements

### Requirement: CI computes and uploads test coverage to Codecov

The `checks` job in `.github/workflows/ci.yml` MUST run the test suite with
coverage measurement for the `clustafari` package (`pytest --cov=clustafari`
with XML and term-missing reports) after the prek gate, and MUST upload the
resulting XML report to Codecov on every push and pull request that triggers
the workflow, authenticated with the `CODECOV_TOKEN` repository secret.

#### Scenario: Push or PR produces a Codecov report

- **WHEN** the `checks` job runs for a push or pull request
- **THEN** it executes the pytest suite with coverage enabled for
  `clustafari`, produces an XML coverage report, and uploads it to Codecov
- **AND** the Codecov check and PR comment appear for the commit

#### Scenario: Upload runs after the prek gate passes

- **WHEN** the coverage step runs
- **THEN** the prek gate (`uv run prek run --all-files`) has already
  succeeded in the same job

#### Scenario: Upload authentication uses the stored token

- **WHEN** the coverage report is uploaded
- **THEN** the upload step passes the `CODECOV_TOKEN` repository secret to
  the Codecov action

### Requirement: Local prek pytest hook behavior is unchanged

The prek pytest hook MUST keep running `pytest` with terminal coverage output
only (no XML report, no upload), so local `uv run prek run --all-files`
behavior and speed are unchanged by this capability.

#### Scenario: Local prek run stays local-only

- **WHEN** a contributor runs `uv run prek run --all-files` locally
- **THEN** the pytest hook runs with `--cov=clustafari --cov-report=term-missing` and no coverage upload or CI-only reporting
  occurs
