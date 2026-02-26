# ADR-004: Hierarchical Context Loading

**Status**: Accepted
**Date**: 2026-02-27

## Context
We need to support global, organizational, and project-specific constraints without manual duplication.

## Decision
Implement a bottom-up resolution strategy: Project \u2192 Team \u2192 Org \u2192 Global. Later levels override or append to earlier ones based on schema-driven merge rules.

## Consequences
- Enables organization-wide standards enforcement.
- Allows projects to override defaults when justified.
