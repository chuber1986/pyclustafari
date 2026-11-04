# Spec Delta

## Purpose

Defines the per-run artifact protocol: how jobs are serialized to the shared folder, how state flows between caller and worker, how results are restored, and how artifacts are cleaned up.

## ADDED Requirements

### Requirement: One artifact directory per run under the shared root

The system SHALL create one artifact directory per run under `~/.clustafari/`, keyed by a joblib hash of the function, arguments, keyword arguments, and a monotonic timestamp so every run gets a distinct directory even for repeated identical calls.

#### Scenario: unique directories per call

- **WHEN** the same function with the same arguments is dispatched twice
- **THEN** the two runs use different artifact directories because the timestamp participates in the hash

### Requirement: Six-file layout derived from a function-named job file

The system SHALL store per run: a pickled job file (function, args, kwargs), a pickled result file (owning object, result), captured stdout, captured stderr, a log, and a state file; the run's file names derive from the configured job file path's stem, and the job file location resolves to the repository's packaged job script if present, else to a `PATH` lookup, else raises.

#### Scenario: file set per run

- **WHEN** a run is prepared
- **THEN** its artifact directory will contain exactly the job, result, stdout, stderr, log, and state files, all sharing the job-file stem

#### Scenario: job script resolution

- **WHEN** the packaged job script exists at its expected repository location
- **THEN** it is used directly; otherwise the system searches `PATH` and raises a value error if the script is found nowhere

### Requirement: Caller-side state machine

The system SHALL track each run through states initialized → ready → finished or failed, where preparation (directory creation and job pickling) moves initialized → ready, completion moves ready → finished, and any preparation or execution failure moves the run to failed.

#### Scenario: preparation failure marks failed instead of raising

- **WHEN** artifact preparation fails (e.g., the function cannot be pickled)
- **THEN** the run transitions to failed with the error recorded, and the failure surfaces later at result retrieval

#### Scenario: state transitions guard operations

- **WHEN** execution is requested on an already-prepared run, or completion is recorded on an unprepared run
- **THEN** the second transition attempt in the same direction raises a state error

### Requirement: Worker-side state reporting

The worker SHALL report its progress through the state file (started, loading, running, dumping, finished) and SHALL record a failed state with a message in the log when any exception occurs, so the caller can observe progress and death by reading files. Unrecognized state values SHALL warn and map to the initial state.

#### Scenario: worker failure is observable

- **WHEN** the worker raises while executing the function
- **THEN** the state file records failure, the message is appended to the log, and the result file is not written

### Requirement: Result retrieval semantics

The system SHALL provide retrieval on the run handle: retrieval before start raises; non-blocking retrieval on an unfinished run raises without changing run state; blocking retrieval polls until the state file reports a terminal state or the cluster-side job is observed dead, with an optional timeout deadline raising on expiry. On completion the system SHALL load the result file, harvest stdout/stderr/log into the run's information, adopt the reported terminal state, and remove the artifact directory on the success path.

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
- **THEN** retrieval yields a null result, marks the run failed, and does not leak a raw unpickling exception

### Requirement: Failed retrieval embeds diagnostics

The system SHALL raise, on retrieval of a failed run, an error whose message embeds the run's log and error output, after removing the artifact directory.

#### Scenario: failed run diagnostics

- **WHEN** retrieval is requested on a run that failed
- **THEN** the raised error's message contains the captured log and error output

### Requirement: Artifact cleanup

The system SHALL remove a run's artifact directory when its result is successfully retrieved, when a failed run's retrieval raises, and as a garbage-collection backstop when an abandoned handle is collected; removal SHALL be best-effort and tolerant of concurrent removal.

#### Scenario: cleanup after normal retrieval

- **WHEN** a finished run's result has been retrieved
- **THEN** the artifact directory no longer exists

#### Scenario: GC backstop

- **WHEN** a run handle is garbage-collected without retrieval
- **THEN** the artifact directory is removed (best-effort)

#### Scenario: concurrent removal tolerated

- **WHEN** two parties remove the same artifact directory concurrently
- **THEN** removal does not raise
