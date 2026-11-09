"""Important Paths collection."""

import importlib.resources
import importlib.resources.abc
import os
from pathlib import Path

from clustafari import workerstub as _workerstub_module

_STATE_DIR_NAME = ".clustafari"
_JOB_FILE_NAME = "clustafari.job"

#: Repo-checkout candidate (dev fallback): <repo>/scripts/clustafari.job.
_CHECKOUT_JOB_FILE = Path(__file__).parents[2] / "scripts" / _JOB_FILE_NAME

_CACHE: dict[str, Path] = {}


def _find_path_to(prog: str) -> Path:
    """Return the first matching entry for prog found on PATH."""
    for p in os.environ["PATH"].split(":"):
        res = list(Path(p).glob(prog))
        if res:
            return res[0]

    msg = "Can't find '%s' in PATH."
    raise ValueError(msg, prog)


def clustafari_dir() -> Path:
    """Return the user state directory, creating it on first use."""
    if (d := _CACHE.get("clustafari_dir")) is not None:
        return d

    d = Path.home() / _STATE_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    _CACHE["clustafari_dir"] = d
    return d


def _packaged_job_file() -> importlib.resources.abc.Traversable | None:
    """Return the packaged job-script resource if it exists, else None."""
    resource = importlib.resources.files("clustafari") / "job" / _JOB_FILE_NAME
    if resource.is_file():
        return resource
    return None


def job_file() -> Path:
    """Return the job script: packaged copy, checkout copy, then PATH."""
    if (j := _CACHE.get("job_file")) is not None:
        return j

    searched: list[str] = []

    resource = _packaged_job_file()
    if resource is not None:
        with importlib.resources.as_file(resource) as resolved:
            _CACHE["job_file"] = resolved
            return _CACHE["job_file"]
    searched.append(f"packaged ({_JOB_FILE_NAME} not shipped inside the clustafari package)")

    checkout = _CHECKOUT_JOB_FILE
    if checkout.is_file():
        _CACHE["job_file"] = checkout
        return checkout
    searched.append(f"checkout ({checkout})")

    try:
        on_path = _find_path_to(_JOB_FILE_NAME)
    except ValueError:
        searched.append("PATH")
    else:
        _CACHE["job_file"] = on_path
        return on_path

    msg = "Can't find 'clustafari.job'; searched: " + "; ".join(searched)
    raise FileNotFoundError(msg)


def workerstub() -> Path:
    """Return the worker stub path."""
    if (w := _CACHE.get("workerstub")) is not None:
        return w

    w = Path(_workerstub_module.__file__ or "")
    _CACHE["workerstub"] = w
    return w


def reset_path_cache() -> None:
    """Clear all cached path resolutions (test/reload helper)."""
    _CACHE.clear()
