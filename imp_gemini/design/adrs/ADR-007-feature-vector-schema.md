# ADR-007: Feature Vector YAML Schema

**Status**: Accepted
**Date**: 2026-02-27

## Context
We need a human-readable and machine-parsable format for representing the current state of a feature's journey through the graph.

## Decision
Use YAML for feature vector files (`features/active/{ID}.yml`). The schema must include `feature`, `intent`, `status`, and a `trajectory` map where keys are edge targets or edge names.

## Consequences
- Enables easy inspection by developers.
- Supports versioning of the trajectory alongside code changes.
