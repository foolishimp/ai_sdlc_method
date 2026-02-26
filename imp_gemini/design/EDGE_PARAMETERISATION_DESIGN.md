# Design: Edge Parameterisations

**Version**: 1.0.0
**Date**: 2026-02-27
**Implements**: REQ-F-EDGE-001

---

## Architecture Overview
Edge parameterisations are implemented as YAML configuration files that specify the checklist, evaluators, and guidance for a given graph transition. The `ConfigLoader` resolves these parameters during the iteration loop.

## Component Design

### Component: EdgeConfigResolver
**Implements**: REQ-EDGE-001, REQ-EDGE-002
**Responsibilities**: Loads YAML edge parameters and injects them into the `iterate()` context.
**Interfaces**: get_edge_checklist(edge_name)

### Component: TagValidator
**Implements**: REQ-EDGE-004
**Responsibilities**: Scans candidate artifacts for mandatory `Implements: REQ-*` tags.
**Interfaces**: validate_tags(candidate)

## Traceability Matrix
| REQ Key | Component |
|---------|----------|
| REQ-EDGE-001 | EdgeConfigResolver |
| REQ-EDGE-002 | EdgeConfigResolver |
| REQ-EDGE-004 | TagValidator |

## ADR Index
- [ADR-009: YAML-based Edge Configuration](adrs/ADR-009-edge-configuration.md)
