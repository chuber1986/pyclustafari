"""Clustafari exceptions."""


class StateError(BaseException):
    """Invalid state."""


class RunnableStateError(BaseException):
    """Function execution is in invalid state for requested operation."""


class TimeoutException(BaseException):
    """Timeout exception while waiting for computation result."""
