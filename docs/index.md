# pyclustafari

`pyclustafari` (the `clustafari` package) runs single Python functions on a
cluster and returns their results to the caller. It is a
[multiprocessing](https://docs.python.org/3/library/multiprocessing.html)-style
framework intended for interactive Python sessions and Jupyter notebooks: a
context manager provides `apply`, `apply_async`, `map`, and `map_async`, and
the configuration requests specific resources from a cluster node.

The function, its arguments, and context data are serialized and shipped to a
worker; the result is serialized back. Runners are pluggable:

- **Dummy** — runs the function in the current Python environment
- **Subprocess** — runs the function in a new Python instance on the same machine
- **Slurm** — deploys the function to a node on a Slurm cluster (requires
  [PySlurm](https://github.com/PySlurm/pyslurm) matching the cluster's Slurm
  version)

## Getting started

```python
from clustafari import ClusterContext, SlurmConfig, wrap_non_picklable_objects
from clustafari.resources import CPUPerTaskResource, MemoryPerNodeResource


@wrap_non_picklable_objects
def custom_fn(param):
    # ...
    return param + 1


cfg = SlurmConfig(CPUPerTaskResource(1), MemoryPerNodeResource("32M"))

with ClusterContext(cfg) as ctx:
    res = ctx.apply(custom_fn, 123)
```

See [Usage](usage.md) for the full API and [Installation](installation.md)
for setup. The full, docstring-generated API reference is in
[Modules](api.md).
