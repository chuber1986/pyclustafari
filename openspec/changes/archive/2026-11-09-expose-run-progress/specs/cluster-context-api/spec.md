# Spec Delta

## MODIFIED Requirements

### Requirement: Non-blocking dispatch returns a result handle

The system SHALL dispatch a function without waiting, returning a handle from which the result can be retrieved later. The handle SHALL expose a `cancel()` operation that transitions the run to a cancelled terminal state: before dispatch-preparation completes it cancels outright, after that it stops the backend's backing execution best-effort. Cancellation is idempotent and a no-op from terminal states (failed, finished, already cancelled). Retrieval from a cancelled run SHALL raise a dedicated cancellation error (a subtype of the retrieval failure error), and the run's temporary artifacts SHALL be cleaned up on that path.

The handle SHALL expose the run's progress through a `status` property returning one of: not-started (dispatch not yet prepared), pending, started, loading, running, dumping, finished, failed, or cancelled. The status SHALL reflect the worker's reported state-file progress; caller terminal states (finished, failed, cancelled) SHALL take precedence and remain stable; a dispatched run whose backing worker or cluster job is observed dead SHALL report failed. The handle's string representation SHALL include the current status and, when the backend associated a job ID with the run, that job ID.

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

#### Scenario: status reports worker progress stages

- **WHEN** a dispatched run's worker reports started, loading, running, or dumping through the state file
- **THEN** the handle's status reflects the reported stage at the next read

#### Scenario: status of a never-dispatched run

- **WHEN** the status is read on a handle whose run was created but not dispatched
- **THEN** a not-started status is reported

#### Scenario: status after terminal outcome is stable

- **WHEN** the status is read on a run whose result was retrieved (artifacts removed) or that was cancelled
- **THEN** the terminal status (finished, failed, cancelled) is reported, not an error and not a not-started status

#### Scenario: dead backing execution reports failed status

- **WHEN** the status is read on a dispatched run whose backing worker process or cluster job is observed dead without a terminal state-file report
- **THEN** a failed status is reported

#### Scenario: string representation includes status and job ID

- **WHEN** the handle is converted to a string
- **THEN** the result contains the run's current status and, for a backend that submitted a job, the job's ID
