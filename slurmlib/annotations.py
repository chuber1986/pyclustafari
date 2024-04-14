"""Delayed function call API."""

import functools

from joblib import wrap_non_picklable_objects


def delayed(function):
    """Decorator used to capture the arguments of a function."""

    function = wrap_non_picklable_objects(function)

    def delayed_function(*args, **kwargs):
        return functools.partial(function, *args, **kwargs)

    return functools.wraps(function)(delayed_function)
