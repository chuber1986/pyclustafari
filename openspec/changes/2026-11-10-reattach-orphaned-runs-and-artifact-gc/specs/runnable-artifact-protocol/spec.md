# runnable-artifact-protocol (Delta)

## ADDED Requirements

### Requirement: Dispatch-time metadata file

The system SHALL write a small metadata file into each run's artifact directory at dispatch time, containing at minimum the dispatched function's name, the dispatch (UTC) timestamp, and the dispatching backend kind; the file SHALL be plain-text (JSON), written atomically, and named `meta.json`. For runs whose backend submits a cluster job, the system SHALL record the submitted job id in the metadata file right after submission. The metadata file SHALL be informational for the run itself: its absence or corruption in an otherwise healthy run SHALL NOT fail the run, and an unwritable metadata write SHALL NOT prevent dispatch.

#### Scenario: metadata file exists after dispatch

- **WHEN** a run is prepared for dispatch on any backend
- **THEN** its artifact directory contains `meta.json` with the function name, a UTC dispatch timestamp, and the backend kind

#### Scenario: job id recorded for cluster backends

- **WHEN** the Slurm backend submits a job for a run
- **THEN** the job id is written to that run's `meta.json` immediately after successful submission

#### Scenario: metadata is advisory, not load-bearing

- **WHEN** the metadata file is absent or unreadable in an otherwise healthy run
- **THEN** dispatch, execution, and result retrieval of that run proceed unaffected

## MODIFIED Requirements

### Requirement: Six-file layout derived from a function-named job file

The system SHALL store per run: a pickled job file (function, args, kwargs), a pickled result file (owning object, result), captured stdout, captured stderr, a log, and a state file — plus the dispatch-time metadata file — the run's file names derive from the configured job file path's stem, and the job file location resolves to the repository's packaged job script if present, else to a `PATH` lookup, else raises.

#### Scenario: file set per run

- **WHEN** a run is prepared
- **THEN** its artifact directory contains exactly the job, result, stdout, stderr, log, state, and metadata files, all sharing the job-file stem except `meta.json`

#### Scenario: job script resolution

- **WHEN** the packaged job script exists at its expected repository location
- **THEN** it is used directly; otherwise the system searches `PATH` and raises a value error if the script is found nowhere
