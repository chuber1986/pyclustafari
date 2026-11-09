# Spec Delta

## ADDED Requirements

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
