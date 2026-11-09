# Installation

`pyclustafari` installs the `clustafari` package. It is developed with
[uv](https://docs.astral.sh/uv/); use Python **3.12+**.

```console
$ git clone --recurse-submodules https://github.com/chuber1986/pyclustafari
$ cd pyclustafari
$ uv sync
```

## PySlurm

The `Slurm` runner requires
[PySlurm](https://github.com/PySlurm/pyslurm), whose version must match your
cluster's Slurm version (e.g. PySlurm 26.5.x for Slurm 26.05.x). PySlurm is
vendored as a git submodule at `third-party/pyslurm` (checked out at the
commit this tree was developed against) and `uv sync` builds it as a Cython
extension against the local Slurm headers and libraries. To move to a new
Slurm version: in `third-party/pyslurm`, `git fetch` and `git checkout` the
tip of the branch for the new Slurm version, then `uv lock` and commit the
updated submodule pointer.

If `uv sync` cannot build PySlurm in your environment:

1. Create the environment without it:

   ```console
   $ uv venv
   $ uv pip install pip
   ```

2. Install the PySlurm version matching your cluster's Slurm, then finish:

   ```console
   $ uv sync
   ```

`DummyConfig` and `SubprocessConfig` work without PySlurm.
