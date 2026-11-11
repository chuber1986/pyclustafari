# install-layout Specification

## Purpose

Defines how the installed package locates its runtime assets (job script, worker stub) and its user state directory, with lazy resolution and fallback order.

## Requirements

### Requirement: Runtime paths resolve lazily without import side effects

The system SHALL expose accessor functions for the runtime paths (user state directory, job script, worker stub) instead of import-time constants. Importing the package SHALL NOT create directories, scan `PATH`, read the filesystem beyond Python's normal import mechanics, or raise resolution errors; an unresolvable path SHALL raise at first accessor use, not at import.

#### Scenario: clean import has no side effects

- **WHEN** `import clustafari` runs in an environment with no `~/.clustafari` directory, no repo checkout, and no job script on `PATH`
- **THEN** the import succeeds, no `~/.clustafari` directory is created, and no error is raised

#### Scenario: resolution errors surface at first use

- **WHEN** the job-script accessor is called and no packaged, checkout, or `PATH` copy of the job script exists
- **THEN** the accessor raises a descriptive error naming the searched locations, and the package import remains unaffected

### Requirement: Job script ships as packaged data with fallback resolution

The system SHALL ship the job script as package data inside the installed distribution and SHALL resolve it in a defined fallback order at first use: (1) the packaged copy via importlib resources, (2) the repository checkout location, (3) an executable named after the job script on `PATH`. Once resolved, the accessor SHALL return the same path on subsequent calls.

#### Scenario: installed wheel resolves packaged job script

- **WHEN** the package is installed from a wheel and the job-script accessor is called
- **THEN** the resolved path points at the packaged job script inside the installed distribution

#### Scenario: checkout copy is found in a source tree

- **WHEN** running from a source checkout where the packaged copy is not installed as data and the checkout contains the job script
- **THEN** the accessor resolves the checkout copy

#### Scenario: PATH fallback for out-of-tree overrides

- **WHEN** no packaged copy exists and no checkout copy exists, but an executable job script is found on `PATH`
- **THEN** the accessor resolves that `PATH` copy

#### Scenario: resolution is cached

- **WHEN** the job-script accessor is called repeatedly in one process
- **THEN** all calls return the same path after the first resolution

### Requirement: User state directory is created on first use

The system SHALL expose an accessor for the user state directory (`~/.clustafari` by default) and SHALL create it on first use rather than at import; every internal use of the directory (run artifacts, defaults copy) goes through the accessor or explicitly creates the directory before writing.

#### Scenario: first dispatch creates the state directory

- **WHEN** the first run artifacts are written
- **THEN** the state directory exists and the run artifacts are placed under it

#### Scenario: imports do not create the directory

- **WHEN** the package is imported and no state accessor is called
- **THEN** the state directory is not created

### Requirement: Configurable artifacts root with precedence

The system SHALL resolve the artifacts root (the directory under which per-run artifact directories are created) in a defined precedence order: (1) an explicit artifacts directory passed at the use site, (2) the `CLUSTAFARI_ARTIFACT_DIR` environment variable read lazily at resolution time, (3) the user state directory `~/.clustafari` (unchanged default). The resolution SHALL be exposed as an accessor on the paths module, SHALL create the resolved root on first use, SHALL cache the resolution, and SHALL honor `reset_path_cache()`. The env var SHALL be read at resolution time, not at import.

#### Scenario: environment variable selects the root

- **WHEN** `CLUSTAFARI_ARTIFACT_DIR` is set and runs are dispatched without an explicit artifacts directory
- **THEN** all per-run artifact directories are created under the directory named by the environment variable and the default `~/.clustafari` run directories are not used

#### Scenario: explicit argument beats the environment variable

- **WHEN** an explicit artifacts directory is passed at the use site while `CLUSTAFARI_ARTIFACT_DIR` is also set
- **THEN** the run artifact directories are created under the explicit directory, not under the environment-variable directory

#### Scenario: default unchanged when nothing is set

- **WHEN** neither an explicit artifacts directory nor `CLUSTAFARI_ARTIFACT_DIR` is set
- **THEN** run artifact directories are created under `~/.clustafari` exactly as before

#### Scenario: root is created and cached

- **WHEN** the artifacts-root accessor resolves a root (from env var or default) that does not yet exist
- **THEN** the directory is created on first use, subsequent calls return the same path until `reset_path_cache()`, and a re-resolution picks up a changed environment

#### Scenario: presets keep using the state directory

- **WHEN** the Slurm defaults (presets) are loaded or copied into the user-editable location
- **THEN** they continue to use the user state directory (`~/.clustafari`) regardless of the artifacts-root resolution

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
  the way to install, and both state the `pyclustafari` → `import clustafari` name mapping

#### Scenario: Source-install route remains documented

- **WHEN** a reader needs to build from source (e.g. to match a cluster's
  Slurm version)
- **THEN** the existing submodule/`uv sync` source-install instructions
  remain available in `docs/installation.md`
