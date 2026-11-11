"""Shared by-value serialization for job and result artifacts.

Every artifact crossing a process boundary — the dispatch job file
(function, args, kwargs) and the worker's result file (owning object,
result) — is written and read through this module, so the dispatching
side and the worker always speak the same on-disk protocol: mixing
writers/readers (joblib vs dill) fails hard on load.

The serializer is `dill`, which pickles callables **by value**. Stdlib
pickle (joblib's backend) resolves functions by reference
(`module.qualname`) and therefore cannot transport lambdas, nested
`def`s, `functools.partial` of either, or module-level `def`s defined in
the dispatching `__main__` script (the worker subprocess has a different
`__main__`). By-value transport covers all of them (issue #31).

Security note: like stdlib pickle, loading a dill stream can execute
arbitrary code — only load artifact files the cluster infrastructure
wrote. By-value pickling ships more code per artifact than by-reference
pickling; that is the price of the capability.
"""

from pathlib import Path
from typing import Any

import dill

# Recurse into the globals a callable references, so a lambda capturing
# script-level constants/classes carries them inside the artifact
# (without it the worker fails resolving the capture).
dill.settings["recurse"] = True

__all__ = ["dump", "load"]


def dump(obj: Any, path: Path) -> None:
    """Serialize ``obj`` to ``path`` (binary dill stream)."""
    with path.open("wb") as f:
        dill.dump(obj, f)


def load(path: Path) -> Any:
    """Deserialize the dill stream at ``path``."""
    with path.open("rb") as f:
        return dill.load(f)  # noqa: S301 — trusted artifacts only, see module docstring
