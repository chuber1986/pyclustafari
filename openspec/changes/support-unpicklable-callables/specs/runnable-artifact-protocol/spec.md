# Spec Delta: runnable-artifact-protocol

## MODIFIED Requirements

### Requirement: Result retrieval semantics

The system SHALL provide retrieval on the run handle: retrieval before start raises; non-blocking retrieval on an unfinished run raises without changing run state; blocking retrieval polls until the state file reports a terminal state or the cluster-side job is observed dead, with an optional timeout deadline raising on expiry. On completion the system SHALL load the result file, harvest stdout/stderr/log into the run's information, adopt the reported terminal state, and remove the artifact directory on the success path. Because the worker publishes artifacts atomically, an unreadable result file on an otherwise terminal run indicates a genuine failure rather than a concurrent write; the corrupt-result tolerance SHALL remain as a final safety net but SHALL log a warning when it triggers, so a silent success-to-failure demotion becomes visible. The corrupt-result tolerance SHALL also cover deserialization failures of the configured by-value serializer (dill), so a truncated or corrupt dill stream demotes the run to failed without leaking a raw deserialization exception.

#### Scenario: not started rejected

- **WHEN** retrieval is requested on a run that was never started
- **THEN** retrieval raises a state error indicating the job was not started

#### Scenario: polling with timeout

- **WHEN** blocking retrieval is requested with a positive timeout and the run does not finish in time
- **THEN** retrieval raises a timeout error

#### Scenario: cluster-side death detected

- **WHEN** the worker died without reporting a terminal state but the cluster job is observed terminated abnormally
- **THEN** retrieval treats the run as finished, marks it failed with a message embedding the captured stderr (or a generic worker-death message), and cleans up

#### Scenario: corrupt result file tolerated

- **WHEN** the result file is unreadable, truncated, or corrupt (including a corrupt dill stream)
- **THEN** retrieval yields a null result, marks the run failed, does not leak a raw unpickling exception, and logs a warning naming the unreadable result file (the worker itself never publishes partial content at a final path)
