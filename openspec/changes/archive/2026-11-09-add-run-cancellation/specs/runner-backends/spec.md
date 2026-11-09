# runner-backends Delta

## MODIFIED Requirements

### Requirement: In-process backend executes inline with output capture

The system SHALL execute dispatched functions in the caller's own process, capturing standard output and error into the run's information, and recording any exception (including base exceptions) as a run failure rather than propagating it to the caller directly. Cancellation on this backend is a state-only transition: there is no external execution to kill, and an already-running inline call is not interrupted.

#### Scenario: inline execution success

- **WHEN** a function is dispatched on the in-process backend and succeeds
- **THEN** the result is recorded on the run and the captured stdout/stderr are available in the run's information

#### Scenario: inline execution failure

- **WHEN** the dispatched function raises
- **THEN** the run transitions to failed with the exception's message, without raising into the caller at execution time

#### Scenario: cancel is a state-only transition

- **WHEN** a run on the in-process backend is cancelled before its blocking retrieval completes
- **THEN** the run transitions to cancelled without any external process or job being signalled

### Requirement: Subprocess backend spawns a detached local worker

The system SHALL execute dispatched functions in a fresh local Python process running the packaged worker stub, constructing the process with the caller's Python interpreter and a worker command, prepending the caller's working directory to the child's `PYTHONPATH`, and proceeding without waiting for the child. The spawned process handle SHALL be kept on the run's information object so worker death can be observed and the worker can be cancelled.

#### Scenario: spawn proceeds without waiting

- **WHEN** a function is dispatched on the subprocess backend
- **THEN** the backend spawns the worker process and returns immediately; completion is later observed via the artifact protocol

#### Scenario: spawn failure fails the run

- **WHEN** process creation fails with an OS error
- **THEN** the run transitions to failed with the OS error's message, and no result is ever recorded

#### Scenario: worker dies without writing state

- **WHEN** the spawned worker process exits before the run's state file reports a terminal state
- **THEN** the run is reported as terminated, and retrieval fails the run with the worker's stderr output and the process exit code instead of waiting forever

#### Scenario: cancel terminates and reaps the worker

- **WHEN** a run on the subprocess backend is cancelled while its worker process is alive
- **THEN** the worker is asked to terminate, is killed if it does not exit within a short grace period, and is reaped; retrieval from the cancelled run raises the cancellation error, not a worker-death failure

## ADDED Requirements

### Requirement: Information objects expose a cancellation hook

The system SHALL expose a `cancel()` operation on every run's information object, mirroring `terminated()`: the base implementation is a no-op (no external execution), backends owning an external execution override it to stop that execution. Failures of the underlying stop mechanism are reported to the caller of `Runnable.cancel()` as log warnings and MUST NOT prevent the run's transition to cancelled.

#### Scenario: base information cancel is a no-op

- **WHEN** `cancel()` is called on a run whose information is the base implementation
- **THEN** no action is taken and no error is raised

#### Scenario: stop-mechanism failure does not block cancellation

- **WHEN** the backend-specific stop call raises
- **THEN** the run's information logs a warning and `Runnable.cancel()` still transitions the run to cancelled
