# cluster-context-api Delta

## MODIFIED Requirements

### Requirement: Non-blocking dispatch returns a result handle

The system SHALL dispatch a function without waiting, returning a handle from which the result can be retrieved later. The handle SHALL expose a `cancel()` operation that transitions the run to a cancelled terminal state: before dispatch-preparation completes it cancels outright, after that it stops the backend's backing execution best-effort. Cancellation is idempotent and a no-op from terminal states (failed, finished, already cancelled). Retrieval from a cancelled run SHALL raise a dedicated cancellation error (a subtype of the retrieval failure error), and the run's temporary artifacts SHALL be cleaned up on that path.

#### Scenario: Handle retrieval before completion

- **WHEN** the result is requested from a handle whose run has not finished
- **THEN** retrieval raises immediately without altering the run's state (the run stays non-failed and may still finish normally)

#### Scenario: Handle retrieval before start is rejected

- **WHEN** the result is requested from a handle that was never started
- **THEN** retrieval raises an error indicating the job was not started

#### Scenario: Blocking retrieval waits and returns the result

- **WHEN** the result is requested from a finished run's handle
- **THEN** retrieval returns the function's return value; with blocking enabled on an unfinished run, retrieval polls until completion (0.1 s interval) or raises a timeout error when a positive timeout deadline expires

#### Scenario: cancelling a never-dispatched run

- **WHEN** `cancel()` is called on a handle whose run was created but not dispatched
- **THEN** the run transitions directly to cancelled with no stop attempt, and retrieval raises the cancellation error

#### Scenario: cancelling a dispatched run stops the backing execution

- **WHEN** `cancel()` is called on a handle whose run was dispatched to a backend with an external execution
- **THEN** the stop hook runs best-effort, the run transitions to cancelled, retrieval raises the cancellation error, and the run's temporary artifacts are removed

#### Scenario: cancel is idempotent and terminal-state safe

- **WHEN** `cancel()` is called on a run that is already cancelled, failed, or finished
- **THEN** the call is a no-op and the state is unchanged

#### Scenario: retrieval from a cancelled run

- **WHEN** the result is requested from a cancelled run's handle
- **THEN** retrieval raises the dedicated cancellation error (distinguishable from a generic failure error), regardless of blocking mode
