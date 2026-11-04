# runner-backends Specification

## Purpose

Defines the three execution backends — in-process, subprocess, and Slurm cluster — their dispatch behavior, and how submission failures surface as run failures.

## Requirements

### Requirement: In-process backend executes inline with output capture

The system SHALL execute dispatched functions in the caller's own process, capturing standard output and error into the run's information, and recording any exception (including base exceptions) as a run failure rather than propagating it to the caller directly.

#### Scenario: inline execution success

- **WHEN** a function is dispatched on the in-process backend and succeeds
- **THEN** the result is recorded on the run and the captured stdout/stderr are available in the run's information

#### Scenario: inline execution failure

- **WHEN** the dispatched function raises
- **THEN** the run transitions to failed with the exception's message, without raising into the caller at execution time

### Requirement: Subprocess backend spawns a detached local worker

The system SHALL execute dispatched functions in a fresh local Python process running the packaged worker stub, constructing the process with the caller's Python interpreter and a worker command, prepending the caller's working directory to the child's `PYTHONPATH`, and proceeding without waiting for the child.

#### Scenario: spawn proceeds without waiting

- **WHEN** a function is dispatched on the subprocess backend
- **THEN** the backend spawns the worker process and returns immediately; completion is later observed via the artifact protocol

#### Scenario: spawn failure fails the run

- **WHEN** process creation fails with an OS error
- **THEN** the run transitions to failed with the OS error's message, and no result is ever recorded

### Requirement: Cluster backend submits via pyslurm

The system SHALL execute dispatched functions by building a submission description whose name is the function's qualified name, pointing stdout/stderr at the run's output files, launching the packaged job script with the worker command and the caller's interpreter path, injecting the caller's working directory into `PYTHONPATH`, and passing the configured resources as submission parameters. The submission interface SHALL be imported lazily at dispatch time.

#### Scenario: successful submission

- **WHEN** a function is dispatched on the cluster backend
- **THEN** a job is submitted with the configured resources and the run is associated with the submitted job's ID and its output/error file locations

#### Scenario: submission failure fails the run

- **WHEN** the submission call raises any exception
- **THEN** the run transitions to failed with that exception's message

#### Scenario: interpreter selection

- **WHEN** the submission description is built
- **THEN** the caller's Python interpreter path is passed to the job script so the cluster job activates the matching environment (current behavior: the interpreter is not configurable per run)
