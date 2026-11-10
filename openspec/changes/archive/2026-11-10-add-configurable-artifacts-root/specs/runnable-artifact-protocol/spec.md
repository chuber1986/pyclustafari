# Spec Delta

## MODIFIED Requirements

### Requirement: One artifact directory per run under the shared root

The system SHALL create one artifact directory per run under the resolved artifacts root, keyed by a joblib hash of the function, arguments, keyword arguments, and a monotonic timestamp so every run gets a distinct directory even for repeated identical calls. The hash SHALL be exactly a string. The artifacts root SHALL resolve per the install-layout capability: an explicit per-context root when dispatched with one, else the `CLUSTAFARI_ARTIFACT_DIR` environment variable, else `~/.clustafari`.

#### Scenario: unique directories per call

- **WHEN** the same function with the same arguments is dispatched twice
- **THEN** the two runs use different artifact directories because the timestamp participates in the hash

#### Scenario: run directories land under the resolved root

- **WHEN** runs are dispatched with an explicit artifacts root, or with `CLUSTAFARI_ARTIFACT_DIR` set, or with neither
- **THEN** each run's artifact directory (containing the job, result, stdout, stderr, log, and state files) is created under the corresponding root
