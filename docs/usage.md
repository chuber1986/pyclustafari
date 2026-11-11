# Usage

To use PyClustafari in a project

```python
from clustafari import ClusterContext, SlurmConfig, wrap_non_picklable_objects
from clustafari.resources import CPUPerTaskResource, MemoryPerNodeResource


@wrap_non_picklable_objects
def custom_fn(param):
    # ...
    return param + 1


cfg = SlurmConfig(
    CPUPerTaskResource(1),
    MemoryPerNodeResource("32M"),
)

with ClusterContext(cfg) as ctx:
    res = ctx.apply(custom_fn, 123)
```

### Callables that pickle cannot serialize by reference

Dispatch transports functions by value (dill), so lambdas, nested `def`s,
`functools.partial` of either, and module-level `def`s defined in your
`__main__` driver script work out of the box — including capturing
script-level globals:

```python
with ClusterContext(SubprocessConfig()) as ctx:
    res = ctx.apply(lambda x: x * 2, 21)  # 42
```

`wrap_non_picklable_objects` remains supported but is no longer needed for
these cases. Note that by-value transport embeds the referenced code (and,
with recursion enabled, captured globals) in the artifact, which grows the
artifact size accordingly.

## Artifact directory

Run artifacts (the pickled function, the result, captured output, and the
worker state/log files) are stored under `~/.clustafari` by default. The
directory can be redirected, in order of precedence:

1. explicit argument: `ClusterContext(cfg, artifacts_dir="/path/to/root")`,
2. environment variable: `CLUSTAFARI_ARTIFACT_DIR=/path/to/root`
   (read when the artifacts root is first resolved in a session),
3. default: `~/.clustafari` (unchanged behavior).

```python
import os

os.environ["CLUSTAFARI_ARTIFACT_DIR"] = "/scratch/myuser"
with ClusterContext(cfg) as ctx:
    res = ctx.apply(custom_fn, 123)  # artifacts land under /scratch/myuser
```

### Choosing a directory on a cluster

Home directories are often NFS mounts with small quotas: artifact I/O pays
NFS latency and visibility penalties and pollutes a shared, backed-up
location. Prefer a scratch filesystem for large-payload runs:

- **Subprocess backend**: the worker runs on the same machine as the caller,
  so node-local scratch (e.g. `/scratch/$SLURM_JOB_ID`) works — but its data
  is not visible to any other node or after job teardown.
- **Slurm backend**: the artifacts directory must be visible to both the
  caller (which reads results) and the worker node (which writes them).
  Node-local scratch will not work here; use a shared parallel/scratch
  filesystem rather than home NFS where available. Always pass absolute
  paths.
