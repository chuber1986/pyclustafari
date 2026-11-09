# slurm-job-monitoring Specification

## Purpose

Defines cluster-side job monitoring: how a submitted job's liveness and abnormal termination are observed through the Slurm interface, and how polling cost is bounded.

## Requirements

### Requirement: Job information resolves output file locations

The system SHALL, on associating a run with a submitted job ID, resolve the job's stdout and stderr file locations from the cluster interface and expose them on the run's information.

#### Scenario: output files resolved at association

- **WHEN** a run is associated with a submitted job
- **THEN** its information carries the job's stdout and stderr file paths as reported by the cluster

### Requirement: Abnormal termination detection

The system SHALL treat a job as dead only when the cluster reports a terminal state (completed, cancelled, failed, timeout, node failure, preemption, boot failure, deadline, out-of-memory, revoked) AND the exit code or its signal is non-zero; normal completion with zero exit code SHALL NOT be treated as dead. A job the user cancelled through the run's own cancellation hook SHALL NOT be treated as dead: the resulting cluster-side `CANCELLED` state (typically with a kill signal) reflects the user's own action, not a worker that died unexpectedly.

#### Scenario: abnormal exit detected

- **WHEN** the job's state is terminal and its exit code or signal is non-zero
- **THEN** the job is reported as terminated

#### Scenario: healthy completion not treated as death

- **WHEN** the job completed with exit code zero
- **THEN** the job is not reported as terminated (the worker's own state file decides completion)

#### Scenario: self-cancelled job not treated as death

- **WHEN** the run was cancelled through its own cancellation hook and the cluster subsequently reports the job as cancelled with a non-zero signal
- **THEN** the job is not reported as terminated (the run is already cancelled; retrieval reports cancellation, not worker death)

### Requirement: Lost job IDs count as dead

The system SHALL treat a job as dead when the cluster interface reports the job ID as invalid or expired (job records no longer retained), while treating other query errors as not dead (the job's true state is unknown, not dead).

#### Scenario: expired job record

- **WHEN** a monitoring query fails with an invalid-job-ID error
- **THEN** the job is reported as terminated

#### Scenario: transient query error

- **WHEN** a monitoring query fails with any other error
- **THEN** the job is not reported as terminated

### Requirement: Poll throttling

The system SHALL issue at most one cluster status query per fixed interval (5 seconds) per run, caching the last observation between queries.

#### Scenario: repeated checks within interval

- **WHEN** termination is checked twice within the throttle interval
- **THEN** only one cluster query is issued and the cached observation is reused

### Requirement: Debug introspection

The system SHALL expose the full cluster-side job record for debugging on the run's information.

#### Scenario: debug info available

- **WHEN** debug information is requested from a run's cluster information
- **THEN** the full job record as reported by the cluster is returned

### Requirement: Output files removed with the information object

The system SHALL unlink the job's stdout/stderr files when the run's information object is garbage-collected.

#### Scenario: collection unlinks outputs

- **WHEN** the run's cluster information object is collected
- **THEN** the resolved stdout and stderr files are unlinked (best-effort)
