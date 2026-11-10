"""Cross-session run discovery, attachment, and artifact garbage collection.

The recovery API behind issue #18: a session that died leaves its dispatched
runs in the artifacts root. `list_runs` discovers them, `attach` rebuilds a
retrieval-capable handle, and `gc` removes terminal-run artifacts by age.
"""

import logging
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from clustafari import paths, utils
from clustafari.utils import State

__all__ = ["GcResult", "RunDescriptor", "attach", "gc", "list_runs"]

logger = logging.getLogger(__name__)

_META_FILE = "meta.json"


@dataclass(frozen=True)
class RunDescriptor:
    """Lightweight description of a run found in the artifacts root."""

    #: Directory name (the run id, `<function>-<uuid hex>`).
    run_id: str
    #: Dispatched function's name (from metadata when recorded).
    function: str | None
    #: Dispatch time in UTC (from metadata when recorded).
    dispatched_at: datetime | None
    #: Backend kind ("slurm", "subprocess", "dummy", ...).
    backend: str | None
    #: Cluster job id, when the backend submitted one.
    jobid: int | None
    #: Worker-reported state read from the run's state file.
    state: State


@dataclass(frozen=True)
class GcResult:
    """Summary of a garbage-collection pass over an artifacts root."""

    #: Run directories removed by this pass.
    removed: int
    #: Run directories still present after the pass.
    remaining: int


def _parse_jobid(raw: Any) -> int | None:
    """Return the job id from advisory metadata, tolerantly (None when invalid)."""
    if raw is None or isinstance(raw, bool):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _run_dir_id(run_dir: Path) -> str:
    """Return the run id of a run directory: the directory's name."""
    return run_dir.name


def _dispatched_at(meta: dict[str, Any]) -> datetime | None:
    """Return the recorded dispatch time, tolerantly."""
    raw = meta.get("dispatched_at")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def read_meta(run_dir: Path) -> dict[str, Any]:
    """Read a run directory's metadata, tolerantly (empty dict on any failure)."""
    return utils._read_meta_path(run_dir / _META_FILE)  # noqa: SLF001


def _iter_run_dirs(root: Path) -> list[Path]:
    """Return the run directories directly under root (contains a *.joblib)."""
    if not root.is_dir():
        return []
    return sorted(d for d in root.iterdir() if d.is_dir() and any(d.glob("*.joblib")))


def _read_worker_state(run_dir: Path) -> State:
    """Read the run's state file tolerantly (IDLE when absent or unreadable)."""
    statefiles = list(run_dir.glob("*.state"))
    if not statefiles:
        return State.IDLE
    try:
        content = statefiles[0].read_text().strip()
    except OSError:
        return State.IDLE
    if not content:
        return State.IDLE
    return State(content.lower())


def list_runs(root: Path | str | None = None) -> list[RunDescriptor]:
    """Discover runs in the artifacts root.

    Scans one level of the resolved artifacts root (explicit ``root`` argument,
    else ``CLUSTAFARI_ARTIFACT_DIR``, else ``~/.clustafari``) and returns one
    descriptor per run directory. Read-only: the root is not created, and
    directories without a ``*.joblib`` file (e.g. the Slurm presets copy) are
    skipped silently.
    """
    resolved = paths.artifacts_root_resolve_only(root)
    descriptors: list[RunDescriptor] = []
    for run_dir in _iter_run_dirs(resolved):
        meta = read_meta(run_dir)
        jobid_raw = meta.get("jobid")
        descriptors.append(
            RunDescriptor(
                run_id=_run_dir_id(run_dir),
                function=meta.get("function") if isinstance(meta.get("function"), str) else None,
                dispatched_at=_dispatched_at(meta),
                backend=meta.get("backend") if isinstance(meta.get("backend"), str) else None,
                jobid=_parse_jobid(jobid_raw),
                state=_read_worker_state(run_dir),
            )
        )
    return descriptors


def attach(run_id: str, root: Path | str | None = None) -> Any:
    """Rebuild a retrieval-capable handle for a run of a previous session.

    ``run_id`` is the run directory's name as reported by :func:`list_runs`.
    The returned handle supports the usual retrieval semantics —
    ``attach(...).get(blocking=True)`` returns a result computed in a
    previous session (or raises it, with the run's diagnostics, if the run
    failed). Raises ``FileNotFoundError`` when no run directory of that id
    exists under the resolved root.
    """
    from clustafari.runner import Runnable

    resolved = paths.artifacts_root_resolve_only(root)
    run_dir = resolved / run_id
    if not (run_dir.is_dir() and any(run_dir.glob("*.joblib"))):
        msg = f"No run '{run_id}' found under artifacts root {resolved}."
        raise FileNotFoundError(msg)
    return Runnable.from_run_dir(run_dir)


def _slurm_job_terminal(jobid: int) -> bool:
    """Return whether a cluster job is terminal or no longer tracked.

    Any pyslurm failure other than the invalid-job-id error is treated as
    "not known to be terminal" (a transient controller problem must not
    delete a live run's artifacts).
    """
    try:
        from pyslurm import Job, RPCError
    except ImportError:
        return False

    from clustafari.runner.slurm.info import SlurmInformation

    try:
        job = Job.load(jobid)
    except RPCError as e:
        # ESLURM_INVALID_JOB_ID: past slurmctld's retention window.
        return e.errno == SlurmInformation._ESLURM_INVALID_JOB_ID  # noqa: SLF001
    except Exception:  # noqa: BLE001
        return False

    return job.state in SlurmInformation._TERMINAL_STATES  # noqa: SLF001


def gc(max_age: float, root: Path | str | None = None) -> GcResult:
    """Remove artifact directories of terminal runs older than ``max_age``.

    A run is removed when it is older than ``max_age`` (its recorded dispatch
    time, falling back to the directory's mtime) *and* terminal: the state
    file reports a terminal worker state, or the recorded cluster job is
    terminal or no longer tracked by the scheduler. Non-terminal runs are
    never removed regardless of age; directories without a ``*.joblib`` file
    are skipped. Removal is best-effort (tolerates concurrent removal).
    """
    resolved = paths.artifacts_root_resolve_only(root)
    now = time.time()

    removed = 0
    run_dirs = _iter_run_dirs(resolved)
    for run_dir in run_dirs:
        meta = read_meta(run_dir)
        age = _dispatched_at(meta)
        if age is not None:
            age_s = max(0.0, now - age.timestamp())
        else:
            try:
                age_s = now - run_dir.stat().st_mtime
            except OSError:
                continue
        if age_s < max_age:
            continue

        if not _run_is_terminal(run_dir, meta):
            continue

        shutil.rmtree(run_dir, ignore_errors=True)
        if not run_dir.exists():
            removed += 1

    return GcResult(removed=removed, remaining=len(run_dirs) - removed)


def _run_is_terminal(run_dir: Path, meta: dict[str, Any]) -> bool:
    """Return whether the run in run_dir has reached a terminal outcome."""
    if _read_worker_state(run_dir) in (State.FINISHED, State.FAILED):
        return True

    jobid = _parse_jobid(meta.get("jobid"))
    if jobid is not None:
        return _slurm_job_terminal(jobid)

    return False
