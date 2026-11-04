# serialization-support Specification

## Purpose
Defines the serialization aids that let functions, bound methods, and their captured state cross process boundaries intact.

## Requirements

### Requirement: Deferred callable annotation

The system SHALL provide an annotation that defers function dispatch and captures call arguments, wrapping the function so un-picklable objects and bound methods survive transport to another process.

#### Scenario: delayed captures args
- **WHEN** a function is annotated and called with args and kwargs
- **THEN** the call returns a deferred object capturing the function and arguments, and the wrapped function remains transportable to another process

### Requirement: Non-picklable function wrapper is re-exported

The system SHALL re-export a joblib-provided wrapper that marks functions as non-picklable so they are transported by reference-plus-source-safe means, exposing it from the package's public surface.

#### Scenario: public import surface
- **WHEN** the package's public names are imported
- **THEN** the wrapper is importable alongside the context manager and backend configs, without importing joblib directly
