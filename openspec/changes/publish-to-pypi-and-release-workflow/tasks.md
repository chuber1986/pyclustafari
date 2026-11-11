# Tasks: Publish to PyPI, add trove classifiers, release workflow

## 1. Packaging metadata

- [ ] 1.1 Add trove classifiers to `pyproject.toml` (Python 3.12/3.13/3.14, MIT license, POSIX :: Linux, Science/Research audience, Distributed Computing topic)
- [ ] 1.2 Rename distribution to `pyclustafari` with `tool.uv.build-backend.module-name = "clustafari"`; regenerate `uv.lock`

## 2. Release workflow

- [ ] 2.1 Add `workflow_call` trigger to `.github/workflows/ci.yml` so `checks` can gate releases
- [ ] 2.2 Add `.github/workflows/release.yml`: tag (`v*`)/release trigger, `checks` gate via reusable workflow call, version-match assertion, `uv build`, trusted publishing to PyPI via `pypa/gh-action-pypi-publish` in the `pypi` environment with `id-token: write`

## 3. Documentation

- [ ] 3.1 README: uncomment/repair pypi, python-versions, CI (`ci.yml`), codecov badges; remove dead template "Project | Paper" links
- [ ] 3.2 README + `docs/installation.md`: document `pip install pyclustafari` → `import clustafari` name mapping as the primary install route; keep source-install instructions

## 4. Verification

- [ ] 4.1 `uv build`: wheel + sdist build; METADATA contains all new classifiers; `Requires-Dist: pyslurm` has no direct-URL (submodule) reference
- [ ] 4.2 TestPyPI dry-run publish (`uv publish --publish-url https://test.pypi.org/legacy/ --check-url ...`) succeeds with the built artifacts
- [ ] 4.3 Gate: `uvx prek run --all-files` passes; commit, push, open PR, watch CI green
