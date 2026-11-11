"""Driver script executed as __main__ for the by-value serialization test (issue #31).

The module-level function below is defined in this script's __main__ module.
Stdlib pickle dispatch fails on it: pickle resolves functions by reference
(`module.qualname`), and the worker subprocess has a different __main__, so
the reference `__main__.g` does not resolve there. The by-value serializer
transports the function itself.

Run with the project venv interpreter (clustafari is installed there):
`.venv/bin/python tests/main_def_driver.py <artifacts_root>` — prints "ok"
and exits 0 when the dispatched result is correct.
"""

import sys

from clustafari import ClusterContext, SubprocessConfig


def g(x):
    return x * 2


def main() -> int:
    artifacts_root = sys.argv[1]
    with ClusterContext(SubprocessConfig(), artifacts_dir=artifacts_root) as ctx:
        result = ctx.apply(g, 21)
    if result != 42:
        print(f"unexpected result: {result!r}", file=sys.stderr)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
