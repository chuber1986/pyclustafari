# API reference

Generated from the source docstrings by [mkdocstrings](https://mkdocstrings.github.io/).
Everything below mirrors the public API of the `clustafari` package.

Import from the canonical paths:

```python
from clustafari import ClusterContext, SlurmConfig, wrap_non_picklable_objects
from clustafari.exceptions import StateError, TimeoutException
from clustafari.resources import CPUPerTaskResource, MemoryPerNodeResource
```

## Module: `clustafari`

The top-level module re-exports the public API:

::: clustafari
options:
members:
\- ClusterContext
\- DummyConfig
\- DummyRunner
\- SlurmConfig
\- SlurmRunner
\- SubprocessConfig
\- SubprocessRunner
\- delayed

## Module: `clustafari.resources`

Resource classes used to configure cluster jobs (passed to a runner config,
e.g. `SlurmConfig(CPUPerTaskResource(1), MemoryPerNodeResource("32M"))`):

::: clustafari.resources
options:
filters:
\- "!^\_"

## Module: `clustafari.exceptions`

::: clustafari.exceptions
options:
filters:
\- "!^\_"
