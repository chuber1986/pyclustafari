"""Session A for the cross-session acceptance test (task 4.1).

Dispatches a run via the subprocess backend, prints the run id, and exits
WITHOUT retrieving the result — the handle is dropped, the worker keeps
running, exactly the orphaned-run scenario of issue #18.

Run as a script from the repository root with the repo root and the tests
directory on PYTHONPATH (the test sets this up):
`PYTHONPATH=src:tests python tests/recovery_session_a.py <artifacts_root>`.
The dispatch target lives in the importable `recovery_fn` module so the
worker (a fresh interpreter) can unpickle the job file.
"""

import os
import sys

from clustafari import ClusterContext, SubprocessConfig

from recovery_fn import compute  # noqa: E402  (tests/ is on PYTHONPATH)


def main() -> int:
    artifacts_root = sys.argv[1]
    with ClusterContext(SubprocessConfig(), artifacts_dir=artifacts_root) as ctx:
        run = ctx.apply_async(compute, 21)
        assert run.tempdir is not None
        print(run.tempdir.name, flush=True)
    # Simulate a dead kernel: exit without running cleanup handlers, so the
    # handle's GC backstop (`__del__`) never fires and the artifacts — like
    # the still-running worker — survive the session.
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
