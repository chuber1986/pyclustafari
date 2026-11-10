# orphaned-run-recovery (Delta)

## Purpose

Lets callers recover results of runs whose owning session died: discover runs in the artifacts root, rebuild retrieval-capable handles for them, and garbage-collect terminal-run artifacts.

## ADDED Requirements

### Requirement: Run discovery over an artifacts root

The system SHALL provide a discovery function that scans an artifacts root (resolving per the install-layout capability: explicit argument, else `CLUSTAFARI_ARTIFACT_DIR`, else `~/.clustafari`) for run directories and returns one descriptor per run directory, with at minimum: function name, run id (the directory's unique identifier), dispatch time, backend kind, job id (when recorded), and the worker-reported state read from the run's state file. Directories that are not run directories (e.g. the Slurm presets copy) SHALL be skipped silently. The discovery function SHALL NOT create the root, SHALL NOT follow into run directories' internals beyond reading the small metadata and state files, and SHALL be read-only.

#### Scenario: descriptors describe existing runs

- **WHEN** the artifacts root contains run directories from previous dispatches
- **THEN** discovery returns one descriptor per run directory with function name, run id, dispatch time, backend kind, and job id taken from the run's metadata, and the state read from the run's state file

#### Scenario: non-run directories are skipped

- **WHEN** the artifacts root also contains a non-run directory (e.g. the Slurm presets copy)
- **THEN** discovery skips it silently and does not raise

#### Scenario: discovery is read-only

- **WHEN** discovery runs against an artifacts root
- **THEN** no directories or files are created, modified, or removed by discovery

#### Scenario: empty root

- **WHEN** the artifacts root does not exist or contains no run directories
- **THEN** discovery returns an empty list

### Requirement: Attach rebuilds a retrieval-capable handle

The system SHALL provide an attach function that takes a run id (or full run-directory name) and an optional artifacts root and rebuilds a handle that supports retrieval with the existing retrieval semantics (blocking poll of the state file, cluster-side death detection, timeout raising, result loading, output harvesting, directory removal on the terminal path). The handle SHALL reconstruct the protocol file paths from the run directory and job-file stem; for cluster backends the reconstructed handle SHALL use the job id from the run's metadata for cluster-side death detection and (best-effort) cancellation. Attaching to a run id that does not exist under the root SHALL raise a lookup error.

#### Scenario: cross-session result retrieval

- **WHEN** a run is dispatched in one session, the handle is dropped, and a later session attaches to the run and retrieves blocking
- **THEN** retrieval returns the function's return value if the run succeeded, or raises an error embedding the run's log and error output if it failed — without the original handle

#### Scenario: attach to a still-running cluster run waits

- **WHEN** a later session attaches to a run whose cluster job is still running and retrieves blocking
- **THEN** retrieval polls the state file and cluster-side death detection until the worker reports a terminal state

#### Scenario: attach uses the recorded job id

- **WHEN** a run with a recorded job id is attached and its worker died without writing a terminal state
- **THEN** cluster-side death detection uses the job id from the run's metadata to observe the job as dead and retrieval marks the run failed with diagnostics

#### Scenario: attach to unknown run id raises

- **WHEN** attach is called with a run id that has no run directory under the resolved root
- **THEN** a lookup error naming the run id and root is raised

### Requirement: Garbage collection of terminal runs

The system SHALL provide a garbage-collection function that removes run directories older than a caller-supplied max age whose run is terminal: the state file reports a terminal worker state (finished/failed), or the caller-side state was terminal, or the cluster-side job (from metadata) is terminal or no longer tracked. The GC function SHALL NOT remove directories of non-terminal runs regardless of age, SHALL skip non-run directories, SHALL tolerate concurrent removal, and SHALL return a summary (removed and remaining counts). With `max_age=0` every terminal-run directory SHALL be removed and every non-terminal one SHALL remain.

#### Scenario: gc with max_age zero

- **WHEN** garbage collection runs with `max_age=0` over a root containing terminal and non-terminal run directories
- **THEN** every terminal-run directory is removed and every non-terminal run directory remains

#### Scenario: routine cleanup spares live runs

- **WHEN** garbage collection runs with a positive `max_age` over a root containing an old terminal run and an old live run
- **THEN** only the old terminal run's directory is removed

#### Scenario: post-crash hygiene via job id

- **WHEN** a run's worker died without writing a terminal state but its cluster job is terminal or no longer tracked by the scheduler
- **THEN** garbage collection removes the run directory once it is older than `max_age`

#### Scenario: concurrent removal tolerated

- **WHEN** two parties garbage-collect the same root concurrently
- **THEN** removal does not raise

#### Scenario: summary returned

- **WHEN** garbage collection removes some run directories
- **THEN** it returns the number of removed and remaining run directories
