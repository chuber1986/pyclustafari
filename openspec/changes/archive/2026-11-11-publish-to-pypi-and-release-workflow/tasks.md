# Tasks: Publish to PyPI, add trove classifiers, release workflow

## 1. Packaging metadata

- [x] 1.1 Add trove classifiers to `pyproject.toml` (Python 3.12/3.13/3.14, MIT license, POSIX :: Linux, Science/Research audience, Distributed Computing topic)
- [x] 1.2 Rename distribution to `pyclustafari` with `tool.uv.build-backend.module-name = "clustafari"`; regenerate `uv.lock`

## 2. Release workflow

- [x] 2.1 Add `workflow_call` trigger to `.github/workflows/ci.yml` so `checks` can gate releases
- [x] 2.2 Add `.github/workflows/release.yml`: tag (`v*`)/release trigger, `checks` gate via reusable workflow call, version-match assertion, `uv build`, trusted publishing to PyPI via `pypa/gh-action-pypi-publish` in the `pypi` environment with `id-token: write`

## 3. Documentation

- [x] 3.1 README: uncomment/repair pypi, python-versions, CI (`ci.yml`), codecov badges; remove dead template "Project | Paper" links
- [x] 3.2 README + `docs/installation.md`: document `pip install pyclustafari` → `import clustafari` name mapping as the primary install route; keep source-install instructions

## 4. Verification

- [x] 4.1 `uv build`: wheel + sdist build; METADATA contains all new classifiers; `Requires-Dist: pyslurm` has no direct-URL (submodule) reference
- [x] 4.2 TestPyPI dry-run publish (`uv publish --publish-url https://test.pypi.org/legacy/ --check-url ...`) succeeds with the built artifacts
  - Completed with a maintainer-provided TestPyPI token (user decision in-session): real upload of wheel+sdist succeeded; https://test.pypi.org/project/pyclustafari/ shows `Name: pyclustafari` 0.1.0 with all 10 classifiers and `Requires-Dist: pyslurm`; `uv pip install --index-url https://test.pypi.org/simple/ pyclustafari==0.1.0` into a throwaway 3.14 venv (plus pure-Python deps) → `import clustafari` works, Dummy backend `ctx.apply` runs end-to-end. Note: the TestPyPI upload used token auth; the workflow's OIDC trusted-publishing path is exercised by the first `v*` tag after the PyPI publisher is registered (workflow header documents the setup). TestPyPI CDN served a 404 `/simple/` page for ~1 min after upload — transient, resolved on retry.
- [x] 4.3 Gate: `uvx prek run --all-files` passes; commit, push, open PR, watch CI green
