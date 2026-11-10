# Spec Delta

## ADDED Requirements

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

### Requirement: Context accepts an explicit artifacts directory

The system SHALL accept an optional artifacts directory argument on the context manager that overrides the artifacts root for every run dispatched through it, including blocking and non-blocking single calls and maps. Runs dispatched through a context without the argument SHALL use the environment-variable/default resolution.

#### Scenario: context-scoped override applies to all dispatch forms

- **WHEN** a context manager is constructed with an explicit artifacts directory and functions are dispatched via apply, apply_async, map, and map_async
- **THEN** every dispatched run creates its artifact directory under the explicit directory

#### Scenario: env var applies to contexts without an override

- **WHEN** no explicit artifacts directory is passed to the context manager and `CLUSTAFARI_ARTIFACT_DIR` is set
- **THEN** every dispatched run creates its artifact directory under the environment-variable root
