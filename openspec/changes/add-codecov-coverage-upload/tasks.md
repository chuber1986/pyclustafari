# Tasks

## 1. CI coverage step and Codecov upload

- [x] 1.1 In `.github/workflows/ci.yml` `checks` job, after the prek gate
  step, add a "Test coverage" step:
  `uv run pytest --cov=clustafari --cov-report=xml     --cov-report=term-missing -q` with the same `PYSLURM_DISABLE_AUTO_INIT`
  / `SLURM_CONF` env as the prek step.
- [x] 1.2 Add a Codecov upload step after it:
  `codecov/codecov-action@v5` with `files: coverage.xml` and
  `token: ${{ secrets.CODECOV_TOKEN }}`.
- [x] 1.3 Update the `checks` job header comment: it now consumes the
  `CODECOV_TOKEN` repository secret (secret is not implicitly forwarded
  through release.yml's `workflow_call`; note this in the comment).

## 2. Manual maintainer setup (outside the repo)

- [ ] 2.1 Install the Codecov GitHub App on chuber1986/pyclustafari.
- [ ] 2.2 Create the upload token on codecov.io and add it as the
  `CODECOV_TOKEN` repository secret in GitHub repo settings.

## 3. Verification

- [x] 3.1 Validate workflow YAML (prettier/check-yaml pass on ci.yml).
- [ ] 3.2 Push branch and confirm on GitHub: `checks` job runs the coverage
  step, upload succeeds (or documents the expected token-missing failure
  if 2.x are not done yet), Codecov check and PR comment appear.
- [x] 3.3 Confirm README badge unchanged and still pointing at
  codecov.io/gh/chuber1986/pyclustafari.
