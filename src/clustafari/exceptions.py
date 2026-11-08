"""Clustafari exceptions."""


class StateError(Exception):
    """Invalid state."""


class RunnableStateError(Exception):
    """Function execution is in invalid state for requested operation."""


class CancelledError(StateError):
    """Run was cancelled; no result exists."""


class TimeoutException(Exception):  # noqa: N818 -- pre-existing public API name
    """Timeout exception while waiting for computation result."""
