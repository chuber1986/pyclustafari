# Spec Delta: install-layout

## ADDED Requirements

### Requirement: PyPI installation with documented name mapping

The documentation MUST present installing the published `pyclustafari`
distribution from PyPI as the primary installation route, and MUST state
prominently that the distribution name (`pyclustafari`) differs from the
import name (`clustafari`), i.e. `pip install pyclustafari` provides
`import clustafari`.

#### Scenario: Install-from-PyPI route documented with name mapping

- **WHEN** a reader opens the README installation section or
  `docs/installation.md`
- **THEN** both show `pip install pyclustafari` (or the uv equivalent) as
  the way to install, and both state the `pyclustafari` → `import
  clustafari` name mapping

#### Scenario: Source-install route remains documented

- **WHEN** a reader needs to build from source (e.g. to match a cluster's
  Slurm version)
- **THEN** the existing submodule/`uv sync` source-install instructions
  remain available in `docs/installation.md`
