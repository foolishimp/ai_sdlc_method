# ADR-GG-006: Multi-tenant Workspace Structure

**Status**: Accepted
**Date**: 2026-02-21
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-TOOL-010 (Spec/Design Boundary Enforcement), REQ-CTX-002 (Context Hierarchy)

---

## Context

The Asset Graph Model v2.6 enforces a strict **Spec/Design Boundary**. While there is one technology-agnostic Specification (WHAT), there can be multiple technology-bound Designs (HOW) for the same project.

To support this, the `.ai-workspace` directory must be structured to accommodate multiple design "tenants." The user has specified that standards and potentially other context should be organized under `.ai-workspace/<design name>/`.

### Options Considered

1.  **Flattened Structure**: Keep all designs in the same directories, using file naming conventions (e.g., `standards.claude.yml`, `standards.gemini.yml`).
2.  **Design-First Nesting**: Move all methodology assets under a `<design name>` root.
3.  **Scoped Multi-tenancy**: Keep shared assets (Spec, Intent, Events) at the root and nest design-specific assets (Standards, ADRs, Data Models) under `.ai-workspace/<design name>/`.

---

## Decision

**We will adopt the "Scoped Multi-tenancy" model, where technology-bound assets are isolated within `.ai-workspace/<design name>/` directories.**

Updated Workspace Structure:
```
.ai-workspace/
├── spec/                       # Shared tech-agnostic specification (REQ keys)
├── events/                     # Shared immutable event log
├── features/                   # Shared feature vectors (trajectories)
│
├── <design_name>/              # Design-specific tenant (e.g., "gemini_genesis")
│   ├── standards/              # Design-specific standards and patterns
│   ├── adrs/                   # Design-specific architectural decisions
│   ├── data_models/            # Design-specific schemas
│   ├── context_manifest.yml    # Tenant-specific reproducibility hash
│   └── project_constraints.yml # Tenant-specific toolchain config
│
└── <another_design>/           # Sibling design (e.g., "claude_v2")
    ├── standards/
    └── ...
```

---

## Rationale

### Why Scoped Multi-tenancy

1.  **Implementation Isolation**: It allows a project to be realized in different tech stacks (e.g., Python vs. Rust) or for different AI platforms (Gemini vs. Claude) without cross-contamination of standards.
2.  **Explicit Mapping**: Mapping `iterate()` to a specific design tenant becomes a simple path resolution: `.ai-workspace/{design}/standards`.
3.  **Spec Stability**: The shared `spec/` and `features/` directories ensure that the "WHAT" remains invariant across all "HOWs," fulfilling the core promise of the Spec/Design boundary.
4.  **Reproducibility**: Each design tenant has its own `context_manifest.yml`, allowing for independent hashing and audit of different implementations.

---

## Consequences

### Positive

-   **Parallel Realization**: Multiple teams or agents can work on different design implementations in the same repository simultaneously.
-   **Clean Migration**: Moving from one design to another is as simple as creating a new tenant directory and running `/aisdlc-init --design <new>`.

### Negative

-   **Path Complexity**: Tooling must now be aware of the "active design" to resolve context paths correctly.
-   **Duplication Risk**: Some standards might be shared across designs; these must be manually copied or managed via a shared `common/` tenant.

### Mitigation

-   The `aisdlc_iterate` tool will accept an optional `--design` parameter (defaulting to the project's primary design).
-   `aisdlc_init` will be updated to scaffold the design-specific sub-directories.

---

## References

- [GEMINI_GENESIS_DESIGN.md](../GEMINI_GENESIS_DESIGN.md) §1.1
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §2.6 (Spec/Design Boundary)
