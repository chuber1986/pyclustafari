# runnable-artifact-protocol (Delta)

## MODIFIED Requirements

### Requirement: One artifact directory per run under the shared root

The system SHALL create one artifact directory per run under the resolved artifacts root, named by a unique per-run identifier (a UUID) prefixed with the dispatched function's name, so every run gets a distinct directory even for repeated identical calls. The artifacts root SHALL resolve per the install-layout capability: an explicit per-context root when dispatched with one, else the `CLUSTAFARI_ARTIFACT_DIR` environment variable, else `~/.clustafari`.

#### Scenario: unique directories per call

- **WHEN** the same function with the same arguments is dispatched twice
- **THEN** the two runs use different artifact directories because each run is assigned a fresh unique identifier

#### Scenario: run directories land under the resolved root

- **WHEN** runs are dispatched with an explicit artifacts root, or with `CLUSTAFARI_ARTIFACT_DIR` set, or with neither
- **THEN** each run's artifact directory (containing the job, result, stdout, stderr, log, and state files) is created under the corresponding root
