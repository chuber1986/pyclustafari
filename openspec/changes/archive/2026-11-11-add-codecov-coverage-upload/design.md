# Design

## Context

See proposal.md — Why. Current state relevant to implementation:

- `.github/workflows/ci.yml` `checks` job: checkout (submodules) → uv →
  Slurm env cache/extract → `uv sync --locked` → `uv run prek run --all-files`. Job header comment says "no secrets are used here" (written
  for the `workflow_call` entry from release.yml).
- The prek pytest hook (prek.toml, priority 10) already runs
  `uv run pytest -v --cov=clustafari --cov-report=term-missing`; `pytest_cov`
  is a dev dependency (pyproject.toml). `coverage.xml` is already
  gitignored.
- README badge is already enabled. release-publishing spec gates the PyPI
  publish on the `checks` job; release.yml calls ci.yml via `workflow_call`.

## Goals / Non-Goals

**Goals:**

- Coverage data reaches Codecov on every push/PR from the `checks` job.
- CI job structure and local prek behavior otherwise unchanged.

**Non-Goals:**

- No coverage threshold / `fail_ci_if_error` gate (explicit follow-up in #29).
- No changes to release.yml's publish logic; the release-publishing spec is
  untouched.
- No prek hook changes.

## Decisions

- **Second pytest run in CI instead of folding coverage into the prek gate.**
  The prek gate keeps its current invocation; CI adds a separate coverage
  step. Slurm-dependent tests skip without `srun`, so the suite is fast on
  runners and the double run is acceptable. Alternative (reusing the prek
  pytest run's coverage) would require plumbing artifacts out of prek and
  restructuring the hook — not worth it for a fast suite.

- **`codecov/codecov-action@v5` with `CODECOV_TOKEN` secret.** Tokenless
  uploads are rate-limited and unreliable; the issue specifies the token
  path. One-time manual setup (outside the repo, tracked as a task):
  install the Codecov GitHub App, add the `CODECOV_TOKEN` repository secret.

- **Correct the "no secrets" job comment.** ci.yml's `checks` job now
  consumes a secret, and release.yml reuses this workflow via
  `workflow_call`. Update the header comment so the security note matches
  reality; no workflow-level `permissions` change is needed — the token is
  passed as a step input, and codecov-action only needs network egress.

- **README badge: no code change.** Already uncommented and pointing at the
  right URLs; issue #29's badge step is already satisfied. It will start
  rendering live data once the first upload lands.

## Risks / Trade-offs

- **Secret exposure via `workflow_call`:** release.yml inherits the `checks`
  job, but `secrets` are not implicitly forwarded to reusable workflows, so
  the release path cannot leak the token; the coverage step simply uploads
  with no token (or an empty one) if run standalone without secrets. Accept:
  uploads from PRs from forks are the normal tokenless case Codecov handles.
- **Double pytest run adds runner minutes.** Accept: suite skips Slurm tests
  on CI; measured to be fast on runners.
- **Codecov flagging "no coverage found" if paths change:** the upload pins
  `files: coverage.xml`; the report path is fixed by the pytest invocation.
