"""SlurmLib exceptions."""


class StateError(BaseException):
    pass


class RunnableStateError(BaseException):
    pass


class TimeoutException(BaseException):
    pass
