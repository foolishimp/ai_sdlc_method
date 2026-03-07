# ADR-S-022: Project Lineage and Context Inheritance

**Status**: Accepted
**Date**: 2026-03-07
**Author**: Gemini (derived from ADR-027)
**Requirements**: REQ-CTX-001, REQ-CTX-002
**Extends**: ADR-S-001 (Hierarchy)

## Context

A project is not an isolated blank slate; it is born into a context of prior decisions (Org ADRs), policies, and domain knowledge. This "lineage" shapes the constraint surface of the project from the moment of inception.

## Decision

The methodology formalizes the **Lineage DAG** as the mechanism for context inheritance.

### 1. Two Lineage Types

| Type | Definition | Management |
|------|-----------|------------|
| **Live** | Evolving upstream source (e.g., Org Policy) | URI reference; updates checked via `gen-update` |
| **Static** | Snapshotted source (e.g., Legacy System Docs) | Content copied and hash-sealed in the workspace |

### 2. Context Hierarchy

Context is resolved through a prioritized merge sequence (the lineage path):
1. **Methodology**: Universal axioms and base monitors.
2. **Organization**: Shared technology standards and platform ADRs.
3. **Policy**: Compliance and security constraints.
4. **Domain**: Prior system knowledge and terminology.
5. **Project**: Local overrides and implementation details.

### 3. Constitutive Observability

The "nervous system" (monitors and feedback loops) is inherited through the lineage. A project inherits its base observability from the methodology and organization tiers, ensuring it is "born alive" with sensing capability.

## Consequences

- **Provenance**: Every design decision can be traced back through the lineage to its originating policy or standard.
- **Consistency**: Organization-level standards propagate automatically to all child projects via the live lineage link.
- **Reproducibility**: Static snapshots ensure that the exact constraint surface used during an iteration can be recovered from the content hashes.
