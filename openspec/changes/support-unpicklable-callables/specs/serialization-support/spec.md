# Spec Delta: serialization-support

## ADDED Requirements

### Requirement: By-value callable serialization

The system SHALL serialize dispatched jobs (function, args, kwargs) and results with a serializer that transports callables **by value**, so callables that stdlib `pickle` can only reference (lambdas, nested `def`s, `functools.partial` of either, and module-level `def`s defined in the dispatching `__main__` script) survive dispatch to a worker process and result transport back. The serializer configuration (including recursion into referenced globals) SHALL be owned by a single serializer module imported by both the dispatching side and the worker, so both sides always speak the same on-disk protocol.

#### Scenario: lambda dispatch returns result

- **WHEN** a lambda is dispatched via `apply` (blocking) or `apply_async` on any backend
- **THEN** the call's result is returned as if the lambda had been called locally

#### Scenario: lambda capturing script-level globals

- **WHEN** a lambda references a module-level variable of the dispatching script and serializer recursion is enabled
- **THEN** the dispatched job resolves the captured global in the worker and returns the computed result

#### Scenario: module-level def in the dispatching main script

- **WHEN** a module-level function defined in the user's `__main__` driver script is dispatched on a subprocess-based backend whose worker has a different `__main__`
- **THEN** the function is transported by value and executes in the worker, instead of failing with a missing-attribute error

#### Scenario: parent and worker share one protocol

- **WHEN** either side dumps or loads a job or result artifact
- **THEN** both sides use the same configured serializer module, so an artifact written by one side is always readable by the other

## Rationale

dill was chosen over cloudpickle (recorded decision): dill was empirically verified end-to-end on this tree (issue #31 verification pass), the dill unpickler is a stdlib-pickle superset so legacy artifact streams remain readable, and `dill.settings['recurse'] = True` provides the required globals-capture semantics for lambdas.
