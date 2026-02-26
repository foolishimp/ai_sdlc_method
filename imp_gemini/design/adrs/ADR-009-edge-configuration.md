# ADR-009: YAML-based Edge Configuration

**Status**: Accepted
**Date**: 2026-02-27

## Context
Different edges in the asset graph require different validation logic and checklists.

## Decision
Store edge-specific parameters in external YAML files (`config/edge_params/*.yml`). Each file defines the `checklist` and `evaluators` for that transition. The engine loads these dynamically at runtime.

## Consequences
- Decouples methodology logic from the iteration engine implementation.
- Enables easy addition of new graph edges without code changes.
