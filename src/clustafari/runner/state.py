"""Runnable state classes."""

from enum import StrEnum, auto

from clustafari.utils import State


class RunState(StrEnum):
    """RunState class."""

    INITIALIZED = auto()
    READY = auto()
    FAILED = auto()
    FINISHED = auto()
    CANCELLED = auto()


class RunStatus(StrEnum):
    """Caller-facing status of a dispatched run.

    Mirrors the worker-side progress (`State` in `clustafari.utils`, written
    to the run's state file) with stable caller-side terminal values.
    """

    NOT_STARTED = auto()
    PENDING = auto()
    STARTED = auto()
    LOADING = auto()
    RUNNING = auto()
    DUMPING = auto()
    FINISHED = auto()
    FAILED = auto()
    CANCELLED = auto()


#: Worker-side state-file value -> caller-facing status. `IDLE` (no state
#: file or the freshly touched empty one) means the job is queued/submitted
#: but the worker has not reported yet.
_STATUS_BY_WORKER_STATE: dict[State, RunStatus] = {
    State.IDLE: RunStatus.PENDING,
    State.STARTED: RunStatus.STARTED,
    State.LOAD_FILE: RunStatus.LOADING,
    State.RUNNING: RunStatus.RUNNING,
    State.DUMP_RESULT: RunStatus.DUMPING,
    State.FINISHED: RunStatus.FINISHED,
    State.FAILED: RunStatus.FAILED,
}
