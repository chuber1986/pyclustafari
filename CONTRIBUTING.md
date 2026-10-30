# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.

You can contribute in many ways.

## Types of Contributions

### Report bugs

Report bugs at https://github.com/chuber1986/pyclustafari/issues.

If you're reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

### Fix Bugs

Look through the issues for bugs. Anything tagged with "bug" and "help wanted" is open to whoever wants to implement it.

### Implement Features

Look through the issues for features. Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

### Write Documentation

PyClustafari could always use more documentation, whether as part of the official PyClustafari docs, or docstrings as appropriate.

### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/chuber1986/pyclustafari/issues.

If you are proposing a feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions are welcome :)

## Get Started!

Ready to contribute? Here's how to set up clustafari for local development.

1. Fork the `pyclustafari` repo on GitHub.

2. Clone your fork locally:

   ```bash
   $ git clone https://github.com/<you>/pyclustafari.git
   $ cd pyclustafari
   ```

3. Create a virtual environment and install the project:

   ```bash
   $ uv sync
   ```

   If `pyslurm` can't be installed (it must be built against the cluster's
   Slurm libraries), create the environment without it:

   ```bash
   $ uv env
   $ uv pip install pip
   # install pyslurm matching your cluster's Slurm version, then:
   $ uv sync
   ```

   The Slurm runner requires pyslurm; `DummyConfig` and `SubprocessConfig`
   work without it.

4. Install the prek hooks (once after cloning):

   ```bash
   $ uv run prek install
   $ uv run prek install --hook-type commit-msg
   ```

5. Create a branch for local development:

   ```bash
   $ git checkout -b name-of-your-bugfix-or-feature
   ```

   Now you can make your changes.

6. When you're done making your changes, make sure the linters, type
   checker, and tests pass (the same gate CI runs):

   ```bash
   $ uv run prek run --all-files
   ```

7. Commit your changes and push the branch to GitHub:

   ```bash
   $ git add .
   $ git commit -m "Your detailed description of your changes."
   $ git push origin name-of-your-bugfix-or-feature
   ```

   Use [ConventionalCommits](https://www.conventionalcommits.org) syntax for
   commit messages.

8. Submit a pull request.

## Merge Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put the new functionality into a function with a docstring, and add the feature to the list in README.md.
3. The pull request should work on the supported Python versions (>= 3.12) and pass `uv run prek run --all-files`.

## Tips

To run a subset of tests:

```bash
$ pytest tests/test_clustafari.py::test_apply
```

## Deploying

A reminder for the maintainers on how to deploy. Make sure all your changes are committed (including an entry in `CHANGELOG.md` and the version in `pyproject.toml`). Then run:

```bash
$ git push
$ git push --tags
```
