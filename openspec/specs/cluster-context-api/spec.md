# cluster-context-api Specification

## Purpose

Defines the user-facing execution API: a context manager that dispatches Python functions to a configured backend, in blocking and non-blocking variants, for single calls and batched maps.

## Requirements

### Requirement: Context manager wraps execution without teardown

The system SHALL provide a context manager that is constructed with a backend configuration, yields itself on entry, and performs no teardown on exit so that non-blocking runs issued inside the context keep running and remain retrievable afterwards.

#### Scenario: Entering returns the context itself

- **WHEN** a context manager is constructed with a backend config and entered
- **THEN** `__enter__` returns the context object itself

#### Scenario: Exiting does not cancel in-flight work

- **WHEN** the context is exited while a non-blocking run is still pending or running
- **THEN** no teardown or cancellation occurs, and the run's result remains retrievable via its handle

### Requirement: Blocking dispatch returns the computed result

The system SHALL dispatch a function with positional and keyword arguments in a blocking call that returns the function's return value, and SHALL raise the run's failure as an error embedding the run's captured log and error output.

#### Scenario: Successful blocking call

- **WHEN** a function is dispatched with args and kwargs and completes successfully
- **WHERE** the call was blocking
- **THEN** the call returns the function's return value

#### Scenario: Failed blocking call raises with diagnostics

- **WHEN** the dispatched function fails
- **THEN** the blocking call raises an error whose message embeds the run's captured log and error output

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

### Requirement: Owning object round-trip on request

The system SHALL return, in place of the bare result, a pair of the function's owning object and the result when the caller requests it at dispatch time.

#### Scenario: return_object returns the pair

- **WHEN** a dispatch call passes `return_object=True`
- **THEN** the blocking call returns `(owning_object, result)` instead of the bare result, where `owning_object` is the object the function was bound to on the worker side (None for plain functions)

### Requirement: Map dispatches element-wise with shared keywords

The system SHALL dispatch one run per element for map calls, binding shared keyword arguments into the dispatched function itself while keeping per-element arguments on each run, and SHALL return results in input order.

#### Scenario: args-only and kwargs-only inputs

- **WHEN** a map call provides only a list of positional-arg tuples, or only a list of kwargs dicts
- **THEN** the missing side is treated as empty for every element, and the run count equals the length of the provided list

#### Scenario: length mismatch rejected

- **WHEN** a map call provides both args and kwargs lists of different lengths
- **THEN** the call raises a value error requiring equal lengths

#### Scenario: both empty

- **WHEN** a map call provides neither args nor kwargs
- **THEN** zero runs are dispatched and the result is an empty list

#### Scenario: order preservation

- **WHEN** a map call completes over N elements
- **THEN** result[i] corresponds to element i of the input, for blocking retrieval in input order

### Requirement: Backend-agnostic facade

The system SHALL expose the four dispatch operations (apply/apply_async/map/map_async semantics) identically regardless of which backend configuration was supplied, delegating them to the configured backend's runner.

#### Scenario: same API across backends

- **WHEN** the context manager is constructed with any backend config (in-process, subprocess, or cluster)
- **THEN** all four dispatch operations are available with identical call signatures and return-shape semantics
