# ADR-008: Event-Sourced Dependency Tracking

**Status**: Accepted
**Date**: 2026-02-27

## Context
Features often depend on other features (e.g., a UI component depending on an API).

## Decision
Track dependencies using the event log. A `feature_spawned` event will optionally include a `parent` field. The `Projector` will use this to build the dependency DAG.

## Consequences
- Dependency graph is fully reconstructible from the audit log.
- Enables automated blocking of downstream work if dependencies are not stable.
