# Spec Delta

## ADDED Requirements

### Requirement: Context manager accepts an explicit artifacts directory

The context manager SHALL accept an optional `artifacts_dir` argument at construction that names the directory under which all runs dispatched through the context create their artifact directories, overriding the `CLUSTAFARI_ARTIFACT_DIR` environment variable and the `~/.clustafari` default for those runs. Constructing a context without the argument SHALL leave artifacts-root resolution to the env-var/default chain.

#### Scenario: context-scoped override applies to all dispatch forms

- **WHEN** a context manager is constructed with an explicit artifacts directory and functions are dispatched via apply, apply_async, map, and map_async
- **THEN** every dispatched run creates its artifact directory under the explicit directory

#### Scenario: no override defers to the env-var/default chain

- **WHEN** a context manager is constructed without an artifacts directory while `CLUSTAFARI_ARTIFACT_DIR` is set
- **THEN** every dispatched run creates its artifact directory under the environment-variable root
