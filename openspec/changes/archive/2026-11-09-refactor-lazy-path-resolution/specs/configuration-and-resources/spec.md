# Spec Delta

## MODIFIED Requirements

### Requirement: Backend configs select runner and carry resources

The system SHALL provide one configuration class per backend that selects that backend's runner, and the cluster backend config SHALL accept positional resource objects, converting them to submission key-value pairs. Config default parameters for the job script and worker stub SHALL be resolved lazily at construction time per the install-layout capability (never at import), so constructing a config works in an installed package with no checkout and no `PATH` copy of the job script.

#### Scenario: cluster config from resources

- **WHEN** a cluster backend config is constructed from resource objects
- **THEN** the config's runner is the cluster runner and the resources are available as submission key-value pairs

#### Scenario: non-cluster configs are resource-less

- **WHEN** an in-process or subprocess backend config is constructed
- **THEN** it carries no resources and uses no job file (empty job-file path)

#### Scenario: lazy default paths at construction

- **WHEN** a config is constructed without explicit job-file or worker-stub arguments in an installed package with no repo checkout and no job script on `PATH`
- **THEN** construction succeeds and resolves the packaged copies

### Requirement: Named presets from packaged defaults

The system SHALL ship named resource presets as packaged YAML, expose lookup by name, list all names, and expose each preset also as a class attribute prefixed `CFG_`, loading them lazily on first access.

#### Scenario: lazy preset load

- **WHEN** a preset is first accessed by name or class attribute
- **THEN** the packaged YAML is located, and on first use copied into the user's `~/.clustafari/` directory (created on demand) if absent, then parsed and cached; the user-editable copy is the one loaded

#### Scenario: missing file yields empty defaults

- **WHEN** the defaults file is missing or the path is not a file
- **THEN** no presets are loaded and no error is raised
