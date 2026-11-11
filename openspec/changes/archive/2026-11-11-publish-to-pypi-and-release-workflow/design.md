# Design: Publish to PyPI, add trove classifiers, release workflow

## Context

`pyproject.toml` uses `uv_build` with the `src/clustafari` layout. The
distribution name was `clustafari` while the repository, README, and docs
all refer to the project as `pyclustafari`; publishing makes the
distribution name user-facing, so the distribution is renamed to
`pyclustafari` with `tool.uv.build-backend.module-name = "clustafari"`
keeping the import package unchanged (uv_build supports exactly this
split; see D7). CI
(`ci.yml`) exposes a `checks` job (the prek gate: lint, ty, pytest) and a
`docs` job. The pyslurm dependency is a vendored submodule built against
Slurm 26.05 headers — wheels must not embed it; it stays a normal
dependency in the published metadata, while `[tool.uv.sources]` pins it to
the submodule path for **development**
installs. Builds for publishing must not carry that dev-only source
override into the artifacts. See Risks.

## Goals / Non-Goals

Goals:

- Valid, PyPI-presentable metadata (classifiers).
- One-command maintainer release: push tag → built and published
  wheel+sdist, gated on CI checks.
- Correct, prominent docs for the name mapping and the PyPI install route.

Non-Goals:

- Signing (Sigstore attestation is produced by the publish action by
  default; no extra key management).
- Version automation (no release-please/dynamic versioning; the version in
  `pyproject.toml` is bumped manually and the tag must match it — the
  workflow verifies this).
- Conda, anaconda.org, or any channel besides PyPI.
- TestPyPI publishing in the release workflow (dry-run verification is a
  local/workflow-dispatch concern, see Verification).

## Decisions

### D1: Classifiers listed explicitly, license classifier despite SPDX expression

`license = { file = "LICENSE" }` stays (table form, not the PEP 639
`license = "MIT"` string form: the build backend and metadata-version 2.4
support both, but the file table keeps the license text attached for older
pip). The `License :: OSI Approved :: MIT License` classifier is added
anyway — PyPI's license display uses it, and PEP 639 deprecation of
license classifiers is not yet enforced (BuildUsername shows a warning at
most). Python version classifiers 3.12/3.13/3.14 mirror
`requires-python = ">=3.12"` and the versions actually exercised (3.14
locally per README, 3.12/3.13 via the supported range).

### D2: Tag-or-release trigger with version match check

Triggers: `push: tags: ['v*']` and
`release: types: [published]`. On trigger, the workflow asserts
`github.ref_name` (tag push) or `github.event.release.tag_name` (release)
equals the version in `pyproject.toml` (`uv run python -c ...` reading
`importlib.metadata`-style via the built metadata — simplest: parse
`pyproject.toml` with `tomllib`). Mismatch fails the job before any
publish. This prevents the classic "tagged v0.2.0 but forgot to bump" Drift
release.

Alternative considered: workflow_dispatch with version input — rejected;
manual input is exactly the step the version check tries to remove, and
tags remain the source of truth.

### D3: Gate on the `checks` job via `workflow_run`-free wait

The release job runs `needs: checks` where `checks` is a
**reusable-workflow call** (`uses: ./.github/workflows/ci.yml`) scoped to
the tag's commit... `ci.yml` has no `workflow_call` trigger, so instead the
release workflow calls the check logic indirectly: it runs the same gate by
invoking `checks` as a job defined in `release.yml` that re-uses the CI
steps. Duplicating the gate steps is brittle. Chosen alternative:
`needs`-wait via the GitHub API is also brittle (polling).

Chosen: add `on: workflow_call:` to `ci.yml` (the `checks` job is already
ref-scoped by `github.sha` semantics) and have `release.yml` do
`jobs: checks: uses: ./.github/workflows/ci.yml` (called workflows run the
`checks` job for the tag ref; the `docs` job also runs, which is harmless —
it only builds) . The publish job then does `needs: [checks]` plus its own
`if: github.ref_type == 'tag' || github.event_name == 'release'` guard.
This keeps the gate in one place: a `checks` change in `ci.yml` applies to
releases automatically.

### D4: Trusted publishing with a `pypi` environment

`permissions: id-token: write` on the publish job;
`pypa/gh-action-pypi-publish@release/v1` with
`environment: pypi`. Maintainer one-time setup (documented in the workflow
header and `docs/`): create the `pypi` environment in repo settings, and
add a pending/verified publisher on PyPI pointing at
`chuber1986/pyclustafari`, workflow `release.yml`, environment `pypi`.
For the very first release the automatic "new project on first publish"
flow can be used instead. No `PYPI_API_TOKEN` secret is stored.

### D5: Build isolates from the dev-only uv source override

`uv build` in CI without `--locked`... Chosen: plain `uv build` in a
checkout that does NOT run `uv sync` first. `uv build` builds an isolated
environment for the backend; `[tool.uv.sources]` (the submodule pin) is a
uv-workspace/lock concept that `uv build`'s PEP 517 path ignores for
metadata generation — `pyslurm` stays an ordinary PyPI dependency in the
published metadata. Verified in this change's verification step by
inspecting the built wheel's `METADATA` (Requires-Dist: pyslurm, no
direct URL) and by `uv publish --publish-url TestPyPI` dry-run.

Note: local builds in a synced worktree are unaffected (same metadata);
the `uv build` isolation guarantee is what CI relies on.

### D6: README badges uncommented with real targets

Uncomment pypi-v, pypi-pyversions, CI badge (path `ci.yml` — the current
commented badge references `dev.yml`, which does not exist; repair it),
and codecov badge (repo may not have codecov wired; the badge then shows
"unknown" — acceptable, and it lights up if codecov is added later; the
issue explicitly asks for it). The "Project | Paper" line with dead
template links is removed rather than uncommented.

### D7: Rename the distribution to `pyclustafari`, keep the import package `clustafari`

The issue's acceptance (`pip install pyclustafari`) and every existing
badge/docs reference require the **distribution** to be `pyclustafari`;
`pyproject.toml` previously named the project `clustafari`, which would
have published the wrong PyPI project name. `uv_build` supports a
distribution/import-name split via `[tool.uv.build-backend] module-name = "clustafari"`. Consequences handled in this change: `uv.lock` regenerated
(top-level package becomes `pyclustafari`), the wheel RECORD still ships
the `clustafari/` module, sdist top-level dir becomes
`pyclustafari-0.1.0/`. Alternatives: keep `clustafari` as the
distribution (contradicts the issue), or rename the import package too
(breaking, out of scope).

## Risks / Trade-offs

- **Trusted publishing needs one-time PyPI-side setup**: the first run may
  fail if the pending publisher is not registered. Mitigation: workflow
  header documents the setup; the automatic first-publish flow covers
  brand-new projects.
- **`workflow_call` on `ci.yml` widens its triggers**: called workflows
  run in the caller's context with the caller's permissions; `ci.yml`
  needs no secrets, and its `push`/`pull_request` triggers are unaffected.
  The `deploy` job is `if: github.event_name == 'push'` so it stays off
  for tag calls.
- **Wheels are pure-python but platform-dependent metadata**: the wheel is
  `py3-none-any` (no compiled content; pyslurm is compiled at install time
  on the user's machine only in dev installs — wait, no: users installing
  from PyPI get pyslurm **from PyPI** if a matching wheel exists, else the
  sdist build of pyslurm requires Slurm headers. Documented in README as a
  Slurm requirement, not a packaging concern).
- **Tag protection**: nothing in-repo stops an accidental tag; the
  version-match check (D2) is the main guard.
