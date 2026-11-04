# Tasks

## 1. Capture

- [x] 1.1 Write proposal.md (Why / What Changes / Capabilities)
- [x] 1.2 Write six capability spec deltas under `specs/` (ADDED requirements only)
- [x] 1.3 Skip design.md deliberately: documentation-only snapshot; no cross-cutting implementation, new dependency, security, or migration complexity (per design instruction condition)

## 2. Validate

- [x] 2.1 Run `openspec validate establish-baseline-specs` and fix any reported issues

## 3. Land

- [x] 3.1 Run `openspec archive establish-baseline-specs` so the six specs populate `openspec/specs/`
- [x] 3.2 Verify `openspec list --specs` shows the six capabilities
