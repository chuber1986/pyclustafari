# PyClustafari

<!-- [![pypi](https://img.shields.io/pypi/v/pyclustafari.svg)](https://pypi.org/project/pyclustafari/) -->

<!-- [![python](https://img.shields.io/pypi/pyversions/pyclustafari.svg)](https://pypi.org/project/pyclustafari/) -->

<!-- [![Build Status](https://github.com/chuber1986/pyclustafari/actions/workflows/dev.yml/badge.svg)](https://github.com/chuber1986/pyclustafari/actions/workflows/dev.yml) -->

<!-- [![codecov](https://codecov.io/gh/chuber1986/pyclustafari/branch/main/graphs/badge.svg)](https://codecov.io/git/chuber1986/pyclustafari) -->

<!--  -->

<!-- [Project](https://sites.google.com/) **|** [Paper](https://aip.scitation.org/doi/full/10.1063/5.0020404/) -->

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
Download repository:

```bash
$ git clone https://github.com/chuber1986/pyclustafari
$ cd pyclustafari
```

It's recommended to use the SSH link, starting with "git://" instead of the HTTPS link starting with "https://".

Create environment:

```bash
$ uv sync
```

If 'pyslurm' can't be installed, use 'uv env && uv pip install pip' to create an empty environment. Manually install 'pyslurm' with the version matching the Slurm version of your cluster. Afterwards, rerun 'uv sync'.

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

For more detail see [DemoNotebook](./notebooks/demo.ipynb)

## Contact

[Christian Huber](mailto:hiddenaddress@gmail.com)

## License

See [MIT license](./LICENSE)

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[tools/cookiecutter-datascience](https://git.silicon-austria.com/embedded-systems/ru-eai/tools/cookiecutter-datascience)
project template.
