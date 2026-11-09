# Spec Delta

## MODIFIED Requirements

### Requirement: Worker-side state reporting

The worker SHALL report its progress through the state file (started, loading, running, dumping, finished) and SHALL record a failed state with a message in the log when any exception occurs, so the caller can observe progress and death by reading files. All protocol files the worker writes — the state file, the result file, and the log — SHALL be published atomically: the worker writes a temporary file in the same directory and renames it onto the final path, so each final path contains either the complete previous content or the complete new content, never a partial write. Unrecognized non-empty state values SHALL warn and map to the initial state. An empty state file — the freshly created, not-yet-written artifact — SHALL be treated as the initial state silently, so the polling loop produces no log output until the worker first reports.

#### Scenario: worker failure is observable

- **WHEN** the worker raises while executing the function
- **THEN** the state file records failure, the message is appended to the log, and the result file is not written

#### Scenario: empty state file reads as initial state

- **WHEN** the caller reads a state file that exists but contains no content (touched before the worker's first report)
- **THEN** the initial state is returned without any warning being logged, on every poll

#### Scenario: unknown state value still warns

- **WHEN** the state file contains a non-empty value that is not a known state
- **THEN** a warning is logged and the initial state is used

#### Scenario: final paths never contain partial content

- **WHEN** a reader polls a final artifact path continuously while the worker writes that artifact (e.g., a large result dump)
- **THEN** every observed content is either absent or fully valid; a partial write is never visible at the final path

### Requirement: Result retrieval semantics

The system SHALL provide retrieval on the run handle: retrieval before start raises; non-blocking retrieval on an unfinished run raises without changing run state; blocking retrieval polls until the state file reports a terminal state or the cluster-side job is observed dead, with an optional timeout deadline raising on expiry. On completion the system SHALL load the result file, harvest stdout/stderr/log into the run's information, adopt the reported terminal state, and remove the artifact directory on the success path. Because the worker publishes artifacts atomically, an unreadable result file on an otherwise terminal run indicates a genuine failure rather than a concurrent write; the corrupt-result tolerance SHALL remain as a final safety net but SHALL log a warning when it triggers, so a silent success-to-failure demotion becomes visible.

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

- **WHEN** the result file is unreadable, truncated, or corrupt
- **THEN** retrieval yields a null result, marks the run failed, does not leak a raw unpickling exception, and logs a warning naming the unreadable result file (the worker itself never publishes partial content at a final path)
