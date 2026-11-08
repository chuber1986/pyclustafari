# runner-backends Delta

## MODIFIED Requirements

### Requirement: Subprocess backend spawns a detached local worker

The system SHALL execute dispatched functions in a fresh local Python process running the packaged worker stub, constructing the process with the caller's Python interpreter and a worker command, prepending the caller's working directory to the child's `PYTHONPATH`, and proceeding without waiting for the child. The spawned process handle SHALL be kept on the run's information object so worker death can be observed.

#### Scenario: spawn proceeds without waiting

- **WHEN** a function is dispatched on the subprocess backend
- **THEN** the backend spawns the worker process and returns immediately; completion is later observed via the artifact protocol

#### Scenario: spawn failure fails the run

- **WHEN** process creation fails with an OS error
- **THEN** the run transitions to failed with the OS error's message, and no result is ever recorded

#### Scenario: worker dies without writing state

- **WHEN** the spawned worker process exits before the run's state file reports a terminal state
- **THEN** the run is reported as terminated, and retrieval fails the run with the worker's stderr output and the process exit code instead of waiting forever
