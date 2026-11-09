# runnable-artifact-protocol Delta

## MODIFIED Requirements

### Requirement: Worker-side state reporting

The worker SHALL report its progress through the state file (started, loading, running, dumping, finished) and SHALL record a failed state with a message in the log when any exception occurs, so the caller can observe progress and death by reading files. Unrecognized non-empty state values SHALL warn and map to the initial state. An empty state file — the freshly created, not-yet-written artifact — SHALL be treated as the initial state silently, so the polling loop produces no log output until the worker first reports.

#### Scenario: worker failure is observable

- **WHEN** the worker raises while executing the function
- **THEN** the state file records failure, the message is appended to the log, and the result file is not written

#### Scenario: empty state file reads as initial state

- **WHEN** the caller reads a state file that exists but contains no content (touched before the worker's first report)
- **THEN** the initial state is returned without any warning being logged, on every poll

#### Scenario: unknown state value still warns

- **WHEN** the state file contains a non-empty value that is not a known state
- **THEN** a warning is logged and the initial state is used

### Requirement: One artifact directory per run under the shared root

The system SHALL create one artifact directory per run under `~/.clustafari/`, keyed by a joblib hash of the function, arguments, keyword arguments, and a monotonic timestamp so every run gets a distinct directory even for repeated identical calls. The hash SHALL be exactly a string.

#### Scenario: unique directories per call

- **WHEN** the same function with the same arguments is dispatched twice
- **THEN** the two runs use different artifact directories because the timestamp participates in the hash

## ADDED Requirements

### Requirement: Run logging never materializes argument payloads

The system SHALL log run lifecycle events without formatting argument payloads into strings when the target log level is disabled: lifecycle messages SHALL use lazy formatting on identity information (the dispatched function's name) rather than the run's full textual representation, which embeds every argument. Enabling debug/info logging SHALL still render the arguments for diagnosis.

#### Scenario: dispatch with large payload at default log level

- **WHEN** a function is dispatched with an argument whose string representation is very large and INFO logging is disabled
- **THEN** no argument payload is stringified for the lifecycle log messages

#### Scenario: diagnostic logging with enabled level

- **WHEN** INFO logging is enabled for the run lifecycle
- **THEN** lifecycle messages identify the run by its dispatched function's name
