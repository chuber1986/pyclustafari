# PyClustafari

[![pypi](https://img.shields.io/pypi/v/pyclustafari.svg)](https://pypi.org/project/pyclustafari/)

[![python](https://img.shields.io/pypi/pyversions/pyclustafari.svg)](https://pypi.org/project/pyclustafari/)

[![Build Status](https://github.com/chuber1986/pyclustafari/actions/workflows/ci.yml/badge.svg)](https://github.com/chuber1986/pyclustafari/actions/workflows/ci.yml)

[![codecov](https://codecov.io/gh/chuber1986/pyclustafari/branch/main/graphs/badge.svg)](https://codecov.io/gh/chuber1986/pyclustafari)

[Christian Huber](https://www.researchgate.net/profile/Christian-Huber-21)

Runs Python functions on a cluster infrastructure.

- Documentation: <https://github.com/chuber1986/pyclustafari/>
- GitHub: <https://github.com/chuber1986/pyclustafari/>
- Free software: MIT license

## Abstract

Deployes single Python functions to an compute cluster and returns the results of the computation. This is intended specifically for interactive Python session and Jupyter notebooks.

## Table of Contents

1. [Introduction](#introduction)
2. [Requirements and Dependencies](#requirements-and-dependencies)
3. [Getting started](#getting-started)
4. [Usage](#usage)

## Introduction

<a name="introduction"></a>
This framework is inspired by the Python 'multiprocessing' library.
It allows executing single functions in a cluster environment. A context manager provides 'apply', 'apply_async', 'map' and 'map_async' methods. The config can be configured to request specific resources from a cluster node. 'apply' and 'map' block the calling Python process to wait for the result. The 'async' variants of these methods allow continuing to work in the caller process and grab the result later.

The project currently supports Dummy (runs the function in the current Python environment), Subprocess (runs the function on the same machine in a new Python instance), and Slurm (deploys the function to a node on a Slurm cluster; requires PySlurm, whose version must match the cluster's Slurm version).

The function, parameters and context data are serialized and stored on a shared folder of the cluster. On the compute node the serialized data is deserialized and the function executed. All results and context information are again serialized and restored by the caller side.

## Requirements and Dependencies

<a name="requirements-and-dependencies"></a>

- Tested on Linux
- PySlurm 26.5 (Slurm 26.05)
- Python (tested with Python3.14)

## Getting started

<a name="getting-started"></a>

**Name mapping:** the PyPI/distribution name is `pyclustafari`, the Python
package you import is `clustafari` — install one name, import the other.

Install from PyPI:

```bash
$ pip install pyclustafari
```

or with [uv](https://docs.astral.sh/uv/):

```bash
$ uv pip install pyclustafari
```

The `Slurm` runner requires PySlurm, whose version must match the cluster's
Slurm version (see [Requirements](#requirements-and-dependencies) and
[Installation](docs/installation.md)).

### Install from source

Needed to build the vendored PySlurm against your cluster's Slurm version.
Download repository:

```bash
$ git clone --recurse-submodules https://github.com/chuber1986/pyclustafari
$ cd pyclustafari
```

It's recommended to use the SSH link (`git@github.com:...`) instead of the HTTPS link starting with "https://".

Create environment:

```bash
$ uv sync
```

`uv sync` builds PySlurm from the vendored submodule `third-party/pyslurm` against the local Slurm headers/libraries. To support a new Slurm version, checkout the matching PySlurm branch (see `third-party/pyslurm`) in the submodule, run `uv lock`, and commit the updated submodule pointer. If 'pyslurm' can't be built this way, use 'uv venv' to create an empty environment and 'uv pip install pip' to bootstrap pip in it. Manually install 'pyslurm' with the version matching the Slurm version of your cluster. Afterwards, rerun 'uv sync'.

### prek usage explicit (for devs only)

```bash
$ uv run prek run --all-files
```

### prek usage during git commit

Once after cloning the repository run:

```bash
$ uv run prek install
$ uv run prek install --hook-type commit-msg
```

Use [ConventionalCommits](https://www.conventionalcommits.org) syntax for commit messages.

```bash
$ git commit -am "this is a message"
```

Install as package (optional):

```bash
$ python -m pip install .
```

The job script ships as package data (`clustafari/job/clustafari.job`) and is
resolved automatically at runtime — no separate `PATH` installation needed.
Adding the project directory to the PYTHONPATH works as well.

## Usage

<a name="usage"></a>
To use PyClustafari in a project

```python
# Import
from clustafari import ClusterContext, SlurmConfig
from clustafari.exceptions import RunnableStateError, TimeoutException
from clustafari.resources import CPUPerTaskResource, MemoryPerNodeResource

# Run a function
with ClusterContext(SlurmConfig()) as ctx:
    res = ctx.apply(function, "param1")
# Run a function that changes it's owning object
with ClusterContext(SlurmConfig()) as ctx:
    obj, _ = ctx.apply(obj.function, "param1", return_object=True)
# Run a function asynchronous and get the result
with ClusterContext(SlurmConfig()) as ctx:
    run = ctx.apply_async(function, "param1")
...
res = run.get(blocking=True)
plot_results(*res)
# Check the progress of an asynchronous run (worker state file):
# pending -> started -> loading -> running -> dumping -> finished/failed
print(run)  # e.g. "function('param1') [running, job 12345]"
run.status  # RunStatus enum: NOT_STARTED ... FINISHED/FAILED/CANCELLED
# Cancel a run you no longer need (e.g. wrong parameters)
from clustafari.exceptions import CancelledError

with ClusterContext(SlurmConfig()) as ctx:
    run = ctx.apply_async(function, "param1")
if wrong_parameters:
    run.cancel()  # stops the Slurm job / worker process
try:
    res = run.get(blocking=True)
except CancelledError:
    res = None
# Run a function asynchronously on 2 sets of parameters and get the results
runs = ctx.map_async(
    function,
    args=[["param1"], ["param2"]],
    kwargs=[{"p1": 1}, {"p1": 2}],
)
...
res = [run.get(blocking=True) for run in runs]
# Use default cluster configuration
SlurmConfig.get_config_names()
cfg = SlurmConfig.get_config("CFG_CPU4_MEM8G_GPU2S")
cfg = SlurmConfig.CFG_CPU1_MEM8G
# Create a new cluster configuration
cfg = SlurmConfig(
    CPUPerTaskResource(3),
    MemoryPerNodeResource("512M"),
)
cfg = SlurmConfig.create_config(
    mem_per_node="4G",
    mem_per_cpu=None,
    mem_per_gpu=None,
    cpu_per_task=2,
    cpu_per_gpu=None,
    required_nodes=None,
    excluded_nodes=None,
    partition=None,
    generic_resource="shard:1",
    n_tasks=None,
    n_tasks_per_node=None,
    n_tasks_per_gpu=None,
    gpus=None,
    gpus_per_task=None,
    gpus_per_node=None,
)
# Run a function using a specific cluster configuration
with ClusterContext(cfg) as ctx:
    res = ctx.apply(function, "param1")
```

### Artifact directory

Run artifacts are stored under `~/.clustafari` by default. To redirect them,
pass an explicit directory (highest precedence) or set the
`CLUSTAFARI_ARTIFACT_DIR` environment variable (read when the artifacts root
is first resolved):

```python
with ClusterContext(SlurmConfig(), artifacts_dir="/scratch/myuser/run") as ctx:
    res = ctx.apply(function, "param1")
```

On clusters, prefer a scratch filesystem over the (often NFS-mounted, small,
backed-up) home directory. Node-local scratch only suits the Subprocess
backend (the worker runs on the caller's machine); the Slurm backend needs a
directory visible to both caller and worker — use a shared scratch/parallel
filesystem with absolute paths.

### Recovering orphaned runs and artifact cleanup

If your kernel dies or the session is closed while runs are in flight, the
`Runnable` handles are lost — but the dispatched work keeps running on the
cluster and its results remain on disk. Discover and re-attach to those
runs in a new session:

```python
import clustafari

# List runs found under the artifacts root (same resolution as dispatch:
# explicit root argument, else CLUSTAFARI_ARTIFACT_DIR, else ~/.clustafari).
for run in clustafari.list_runs():
    print(run.run_id, run.function, run.backend, run.jobid, run.state)

# Rebuild a handle for a run of a previous session and retrieve its result
# (blocking, with the usual timeout semantics).
handle = clustafari.attach("myfunc-3f2b9c0d7e64123456789abcdef01234")
result = handle.get(blocking=True, timeout=600)
```

A failed run raises on retrieval with the run's captured log and error
output, so post-mortem diagnosis works without the original session. Runs
are identified by their artifact directory name; attaching does not
re-dispatch anything — it only reads what the previous session left behind.

Clean up artifact directories of terminal runs by age:

```python
result = clustafari.gc(max_age=7 * 24 * 3600)  # keep one week of artifacts
print(result.removed, "removed,", result.remaining, "remaining")
```

`gc` only removes runs that are terminal (the worker reported
finished/failed, or the cluster job is no longer active) and older than
`max_age`; live runs are never touched. With `max_age=0` every terminal-run
directory is removed — useful after a crash.

For more detail see [DemoNotebook](./notebooks/demo.ipynb)

## Contact

[Christian Huber](mailto:hiddenaddress@gmail.com)

## License

See [MIT license](./LICENSE)

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[tools/cookiecutter-datascience](https://git.silicon-austria.com/embedded-systems/ru-eai/tools/cookiecutter-datascience)
project template.
