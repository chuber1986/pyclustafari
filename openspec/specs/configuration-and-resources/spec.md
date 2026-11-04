# configuration-and-resources Specification

## Purpose

Defines how cluster resource requests are expressed as validated, typed resource objects, how backend configurations are constructed, and how named presets are discovered and loaded.

## Requirements

### Requirement: Typed resource objects validate at construction

The system SHALL provide resource classes for memory (per node/CPU/GPU), CPU counts (per task/GPU), task counts (total/per node/per GPU), GPUs (total/per task/per node), time limit, partitions, required/excluded nodes, and generic resources, each validating its value at construction and raising a value error on invalid input.

#### Scenario: invalid values rejected at construction

- **WHEN** a resource is constructed with a non-integer value where an integer is required, a negative or non-positive value where positive is required, or a unit where none is allowed
- **THEN** construction raises a value error

#### Scenario: string-or-collection shapes

- **WHEN** a resource accepting string-or-list or string-or-dict values is constructed with a value of any other shape (e.g., a number for a generic resource)
- **THEN** construction raises a value error

#### Scenario: unknown size unit warns and falls back

- **WHEN** a size value carries an unrecognized unit suffix
- **THEN** the system emits a warning and treats the value as unit-less rather than failing

### Requirement: Resources render as submission key-value pairs

The system SHALL convert a collection of resource objects into a mapping of submission-system keys to string values suitable for direct consumption by the cluster submission interface.

#### Scenario: rendering collection

- **WHEN** a set of resource objects is rendered
- **THEN** the result maps each resource's submission-system key to its stringified value (units appended, lists comma-joined, dicts rendered as key:value pairs)

### Requirement: Backend configs select runner and carry resources

The system SHALL provide one configuration class per backend that selects that backend's runner, and the cluster backend config SHALL accept positional resource objects, converting them to submission key-value pairs.

#### Scenario: cluster config from resources

- **WHEN** a cluster backend config is constructed from resource objects
- **THEN** the config's runner is the cluster runner and the resources are available as submission key-value pairs

#### Scenario: non-cluster configs are resource-less

- **WHEN** an in-process or subprocess backend config is constructed
- **THEN** it carries no resources and uses no job file (empty job-file path)

### Requirement: Resource attribute access on config

The system SHALL expose a config's resources as attributes and raise an attribute error for unknown names.

#### Scenario: attribute access

- **WHEN** an attribute is read from a config
- **THEN** a stored resource is returned by its name, and unknown names raise an attribute error

### Requirement: Keyword-based cluster config builder

The system SHALL provide a builder accepting keyword parameters (memory, CPUs, GPUs, tasks, nodes, partitions, generic resources, time limit) that creates only the resources whose keywords are set.

#### Scenario: partial keyword set

- **WHEN** the builder is called with a subset of keywords (e.g., memory, cpus, partition)
- **THEN** the resulting submission mapping contains exactly the corresponding keys and no others

### Requirement: Named presets from packaged defaults

The system SHALL ship named resource presets as packaged YAML, expose lookup by name, list all names, and expose each preset also as a class attribute prefixed `CFG_`, loading them lazily on first access.

#### Scenario: lazy preset load

- **WHEN** a preset is first accessed by name or class attribute
- **THEN** the packaged YAML is located, and on first use copied into the user's `~/.clustafari/` directory if absent, then parsed and cached; the user-editable copy is the one loaded

#### Scenario: missing file yields empty defaults

- **WHEN** the defaults file is missing or the path is not a file
- **THEN** no presets are loaded and no error is raised

### Requirement: Reflection-based defaults loading is reusable

The system SHALL provide a reusable loader that parses a defaults file into named lists of resource objects, returning an empty result without error when the file is absent. (Presets with `CFG_` prefixing and lazy copying are built on this loader.)

#### Scenario: reflection-based resource entries

- **WHEN** a defaults file entry lists resources as target-class/args items
- **THEN** each entry is instantiated by reflective class lookup of the target
