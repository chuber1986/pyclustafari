# Installation

`pyclustafari` installs the `clustafari` package. It is developed with
[uv](https://docs.astral.sh/uv/); use Python **3.12+**.

```console
$ git clone https://github.com/chuber1986/pyclustafari
$ cd pyclustafari
$ uv sync
```

## PySlurm

The `Slurm` runner requires
[PySlurm](https://github.com/PySlurm/pyslurm), whose version must match your
cluster's Slurm version (e.g. PySlurm 26.5.x for Slurm 26.05.x). PySlurm is a
Cython extension that builds against the cluster's Slurm headers and
libraries, so if `uv sync` cannot build it in your environment:

1. Create the environment without it:

   ```console
   $ uv env
   $ uv pip install pip
   ```

2. Install the PySlurm version matching your cluster's Slurm, then finish:

   ```console
   $ uv sync
   ```

`DummyConfig` and `SubprocessConfig` work without PySlurm.
