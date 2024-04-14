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
