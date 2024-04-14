# PyClustafari

<!-- [![pypi](https://img.shields.io/pypi/v/pyclustafari.svg)](https://pypi.org/project/pyclustafari/) -->
<!-- [![python](https://img.shields.io/pypi/pyversions/pyclustafari.svg)](https://pypi.org/project/pyclustafari/) -->
<!-- [![Build Status](https://github.com/chuber1986/pyclustafari/actions/workflows/dev.yml/badge.svg)](https://github.com/chuber1986/pyclustafari/actions/workflows/dev.yml) -->
<!-- [![codecov](https://codecov.io/gh/chuber1986/pyclustafari/branch/main/graphs/badge.svg)](https://codecov.io/git/chuber1986/pyclustafari) -->
<!--  -->

<!-- [Project](https://sites.google.com/) **|** [Paper](https://aip.scitation.org/doi/full/10.1063/5.0020404/) -->

[Christian Huber](https://www.researchgate.net/profile/Christian-Huber-21)

Runs Python functions on a cluster infrastructure.

[//]: # '# "Paper Title, Journal of whatever - special issue, 2020"'

-   Documentation: <https://github.com/chuber1986/pyclustafari/>
-   GitLab: <https://github.com/chuber1986/pyclustafari/>
    [//]: # (\* PyPI: <https://pypi.org/project/pyclustafari/>)
-   Free software: MIT license

## Abstract

TBA

## Table of Contents

1. [Introduction](#introduction)
2. [Requirements and Dependencies](#requirements-and-dependencies)
3. [Getting started](#getting-started)
4. [Usage](#usage)

## Introduction

<a name="introduction"></a>
TBA

## Requirements and Dependencies

<a name="requirements-and-dependencies"></a>

-   Tested on Linux
-   Python (tested with Python3.11)

## Getting started

<a name="getting-started"></a>
Download repository:

```bash
$ git clone https://github.com/chuber1986/pyclustafari
$ cd pyclustafari
```

It's recommended to use the SSH link, starting with "git://" instead of hte HTTPS link starting with "https://".

Create environment:

```bash
$ conda create -n pyclustafari python=3.11
$ conda env update -n pyclustafari --file environment.yaml
```

### pre-commit usage explicit (for devs only)

```bash
$ pre-commit run -a
```

### pre-commit usage during git commit

Once after clone the replository run:

```bash
$ pre-commit install
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
import clustafari
```

TBA

## Contact

[Christian Huber](mailto:hiddenaddress@gmail.com)

## License

See [MIT license](./LICENSE)

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[tools/cookiecutter-datascience](https://git.silicon-austria.com/embedded-systems/ru-eai/tools/cookiecutter-datascience)
project template.
