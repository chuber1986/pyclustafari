# slurm-job-monitoring Delta

## MODIFIED Requirements

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
