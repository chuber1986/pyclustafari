# release-publishing Specification

## Purpose

Defines how the project is published as a distribution to PyPI: the packaging
metadata contract (classifiers), the tag/release-triggered build-and-publish
workflow using PyPI trusted publishing, and its gating on the CI `checks`
job, so users can install from PyPI without git access.

## Requirements

### Requirement: Distribution name maps to the clustafari import package

The published distribution MUST be named `pyclustafari` while providing the
import package `clustafari`, so `pip install pyclustafari` makes
`import clustafari` work; the built wheel/sdist metadata MUST carry the
`pyclustafari` name.

#### Scenario: Wheel metadata names the distribution pyclustafari

- **WHEN** the built wheel's `METADATA` is inspected
- **THEN** `Name: pyclustafari` and `Requires-Dist: pyslurm` (an ordinary
  PyPI dependency, no direct-URL/submodule reference) are present

### Requirement: Distribution metadata declares Python versions, license, and platform

The distribution metadata (`pyproject.toml` classifiers) MUST declare the
Python versions the project supports (3.12, 3.13, 3.14), the MIT license, the
POSIX/Linux operating system, the science/research audience, and the
distributed-computing topic, in addition to the existing development-status
and generic Python classifiers.

#### Scenario: Metadata lists supported Python versions

- **WHEN** the distribution metadata is inspected (e.g. `uv build` output or
  the `PKG-INFO`/`METADATA` file of the built wheel or sdist)
- **THEN** `Classifier: Programming Language :: Python :: 3.12`, `... 3.13`,
  and `... 3.14` are present

#### Scenario: Metadata lists license, OS, audience, and topic

- **WHEN** the distribution metadata is inspected
- **THEN** `Classifier: License :: OSI Approved :: MIT License`,
  `Classifier: Operating System :: POSIX :: Linux`,
  `Classifier: Intended Audience :: Science/Research`, and
  `Classifier: Topic :: System :: Distributed Computing` are present

### Requirement: Release workflow publishes distributions on tag push or GitHub release

A GitHub Actions release workflow MUST build the wheel and sdist with
`uv build` and publish them to PyPI via trusted publishing (OIDC, no stored
API token), triggered on a pushed `v*` tag or a published GitHub release,
and it MUST gate the publish on the `checks` job from `ci.yml` passing.

#### Scenario: Tag push triggers build and publish

- **WHEN** a tag matching `v*` is pushed (or a release is published)
- **THEN** the workflow builds the wheel and sdist with `uv build` and
  publishes both artifacts to PyPI using OIDC trusted publishing
  (`pypa/gh-action-pypi-publish`)

#### Scenario: Publish is gated on CI checks

- **WHEN** the release workflow starts for a tag or release whose commit has
  not passed the `checks` job
- **THEN** the publish waits until the `checks` job for that ref succeeds
  before publishing; a failed `checks` job prevents publishing

#### Scenario: Publish environment uses the pypi GitHub environment

- **WHEN** the publish job runs
- **THEN** it runs in the `pypi` GitHub environment with `id-token: write`
  permission, so PyPI can verify the OIDC publisher
