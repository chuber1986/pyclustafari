# runnable-artifact-protocol Specification

## Purpose

Defines the per-run artifact protocol: how jobs are serialized to the shared folder, how state flows between caller and worker, how results are restored, and how artifacts are cleaned up.

## Requirements

### Requirement: One artifact directory per run under the shared root

The system SHALL create one artifact directory per run under the resolved artifacts root, named by a unique per-run identifier (a UUID) prefixed with the dispatched function's name, so every run gets a distinct directory even for repeated identical calls. The artifacts root SHALL resolve per the install-layout capability: an explicit per-context root when dispatched with one, else the `CLUSTAFARI_ARTIFACT_DIR` environment variable, else `~/.clustafari`.

#### Scenario: unique directories per call

- **WHEN** the same function with the same arguments is dispatched twice
- **THEN** the two runs use different artifact directories because each run is assigned a fresh unique identifier

#### Scenario: run directories land under the resolved root

- **WHEN** runs are dispatched with an explicit artifacts root, or with `CLUSTAFARI_ARTIFACT_DIR` set, or with neither
- **THEN** each run's artifact directory (containing the job, result, stdout, stderr, log, and state files) is created under the corresponding root

### Requirement: Six-file layout derived from a function-named job file

The system SHALL store per run: a pickled job file (function, args, kwargs), a pickled result file (owning object, result), captured stdout, captured stderr, a log, and a state file — plus the dispatch-time metadata file — the run's file names derive from the configured job file path's stem, and the job file location resolves to the repository's packaged job script if present, else to a `PATH` lookup, else raises.

#### Scenario: file set per run

- **WHEN** a run is prepared
- **THEN** its artifact directory contains exactly the job, result, stdout, stderr, log, state, and metadata files, all sharing the job-file stem except `meta.json`

#### Scenario: job script resolution

- **WHEN** the packaged job script exists at its expected repository location
- **THEN** it is used directly; otherwise the system searches `PATH` and raises a value error if the script is found nowhere

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

### Requirement: Caller-side state machine

The system SHALL track each run through states initialized → ready → finished or failed, where preparation (directory creation and job pickling) moves initialized → ready, completion moves ready → finished, and any preparation or execution failure moves the run to failed.

#### Scenario: preparation failure marks failed instead of raising

- **WHEN** artifact preparation fails (e.g., the function cannot be pickled)
- **THEN** the run transitions to failed with the error recorded, and the failure surfaces later at result retrieval

#### Scenario: state transitions guard operations

- **WHEN** execution is requested on an already-prepared run, or completion is recorded on an unprepared run
- **THEN** the second transition attempt in the same direction raises a state error

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

### Requirement: Run logging never materializes argument payloads

The system SHALL log run lifecycle events without formatting argument payloads into strings when the target log level is disabled: lifecycle messages SHALL use lazy formatting on identity information (the dispatched function's name) rather than the run's full textual representation, which embeds every argument. Enabling debug/info logging SHALL still render the arguments for diagnosis.

#### Scenario: dispatch with large payload at default log level

- **WHEN** a function is dispatched with an argument whose string representation is very large and INFO logging is disabled
- **THEN** no argument payload is stringified for the lifecycle log messages

#### Scenario: diagnostic logging with enabled level

- **WHEN** INFO logging is enabled for the run lifecycle
- **THEN** lifecycle messages identify the run by its dispatched function's name
