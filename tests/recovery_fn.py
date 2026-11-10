"""Importable compute function for the cross-session recovery test.

Lives in its own module (not the session-A script) so the pickled job file
references `recovery_fn.compute`, which the worker can import from `PYTHONPATH`.
"""


def compute(a):
    return a * 2
