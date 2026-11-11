# Proposal: Publish to PyPI, add trove classifiers, release workflow

## Why

The package cannot be installed by its audience without git access: there is
no PyPI release, the distribution name (`pyclustafari`) and import name
(`clustafari`) differ with no published artifact to anchor the mapping, and
`pyproject.toml` metadata is too thin for PyPI to present the project
correctly (no Python-version, license, or OS classifiers). The README PyPI
and CI badges are commented out pending a real release.

## What Changes

- Add trove classifiers to `pyproject.toml`: Python 3.12/3.13/3.14 versions,
  MIT license, POSIX/Linux OS, `Intended Audience :: Science/Research`,
  `Topic :: System :: Distributed Computing`.
- Add a release workflow `.github/workflows/release.yml`: build with
  `uv build`, publish via PyPI trusted publishing (OIDC,
  `pypa/gh-action-pypi-publish`), triggered on a pushed `v*` tag or a GitHub
  release, gated on the `checks` job from `ci.yml`.
- Uncomment/repair the README badges (pypi, python versions, CI, codecov)
  and document the `pip install pyclustafari` → `import clustafari`
  distribution-vs-import name mapping prominently in README and
  `docs/installation.md`.

## Capabilities

### New Capabilities

- `release-publishing`: Building and publishing releases to PyPI —
  packaging metadata quality (classifiers), the tag/release-triggered
  trusted-publishing workflow, and its gating on the CI `checks` job.

### Modified Capabilities

- `install-layout`: The documented install path gains PyPI as the primary
  installation route (`pip install pyclustafari` → `import clustafari`),
  alongside the existing source-install instructions.

## Impact

- Code: no runtime code changes.
- Packaging: `pyproject.toml` classifiers only; no dependency or version
  changes.
- CI: new workflow file; `ci.yml` untouched.
- Docs: README, `docs/installation.md`.
- Ops (one-time, maintainer): create the `pypi` GitHub environment, and
  register the pending publisher on PyPI (or use the automatic
  first-publish flow for a newly created project). No repository changes
  required for this.
