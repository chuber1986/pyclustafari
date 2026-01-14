"""Delayed function call API."""

import functools
from collections.abc import Callable

from joblib import wrap_non_picklable_objects


def delayed(function: Callable) -> Callable:
    """Decorate to capture the arguments of a function."""
    function = wrap_non_picklable_objects(function)

    def delayed_function(*args: list, **kwargs: dict):
        return functools.partial(function, *args, **kwargs)

    return functools.wraps(function)(delayed_function)
