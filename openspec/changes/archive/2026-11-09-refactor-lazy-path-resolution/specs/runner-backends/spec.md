# Spec Delta

## MODIFIED Requirements

### Requirement: Subprocess backend spawns a detached local worker

The system SHALL execute dispatched functions in a fresh local Python process running the worker stub, whose path SHALL be resolved lazily at config construction or dispatch time (never at import), defaulting to the packaged worker stub per the install-layout capability. Constructing the process uses the caller's Python interpreter and a worker command, prepends the caller's working directory to the child's `PYTHONPATH`, and proceeds without waiting for the child. The spawned process handle SHALL be kept on the run's information object so worker death can be observed. The backend dispatch entry SHALL be a fire-and-forget operation returning `None` in every outcome (successful handoff, preparation failure, handoff failure); the run's information object SHALL be the sole carrier of execution state.

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

### Requirement: Cluster backend submits via pyslurm

The system SHALL execute dispatched functions by building a submission description whose name is the function's qualified name, pointing stdout/stderr at the run's output files, launching the job script with the worker command and the caller's interpreter path, injecting the caller's working directory into `PYTHONPATH`, and passing the configured resources as submission parameters. The job script path SHALL be resolved lazily per the install-layout capability (packaged copy first, checkout and `PATH` as fallbacks) at config construction or dispatch time — never at import — and an unresolvable job script SHALL fail the run at dispatch with an error naming the searched locations. The submission interface SHALL be imported lazily at dispatch time. The backend runner instance SHALL NOT carry per-job state: it is shared across all runs of one configuration, and the submitted job's ID SHALL be kept only on the run's information object.

#### Scenario: successful submission

- **WHEN** a function is dispatched on the cluster backend
- **THEN** a job is submitted with the configured resources and the run is associated with the submitted job's ID and its output/error file locations

#### Scenario: submission failure fails the run

- **WHEN** the submission call raises any exception
- **THEN** the run transitions to failed with that exception's message, and the backend's dispatch entry returns without exposing a job ID

#### Scenario: unresolvable job script fails at dispatch, not import

- **WHEN** the cluster backend dispatches a run and no packaged, checkout, or `PATH` copy of the job script exists
- **THEN** the run transitions to failed with an error naming the searched locations, and `import clustafari` remains unaffected

#### Scenario: no per-job state on the runner

- **WHEN** the cluster backend runner is inspected after dispatching runs
- **THEN** it exposes no job-ID attribute; the submitted job ID is retrievable only from each run's information object

#### Scenario: interpreter selection

- **WHEN** the submission description is built
- **THEN** the caller's Python interpreter path is passed to the job script so the cluster job activates the matching environment (current behavior: the interpreter is not configurable per run)
