# ADR-GG-009: Unified Dogfooding Root

**Status**: Proposed
**Date**: 2026-02-21
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-TOOL-007 (Project Scaffolding), REQ-UX-005 (Recovery), **Self-Referential Construction**

---

## Context

The initial design distributed methodology assets (design docs, ADRs) separately from the implementation code and the methodology state (`.ai-workspace`). While this supported multi-tenancy at the repository root, it created a "split-brain" effect for agents building the methodology itself. 

To improve the dogfooding experience—where the Gemini implementation is used to build the Gemini implementation—we need a more cohesive structure.

### Options Considered

1.  **Distributed Model**: Global `.ai-workspace` at repo root, shared `code/` and `docs/` directories.
2.  **Unified Tenant Folders**: Each design (e.g., `imp_gemini`, `imp_claude`) has its own root folder containing its `code`, `design`, `tests`, and its own `.ai-workspace` state.

---

## Decision

**We will adopt the "Unified Dogfooding Root" model, where each design implementation lives in a self-contained directory (`imp_<design_name>/`) that includes both the implementation artifacts and the self-referential methodology state.**

New Structure:
```
imp_gemini/
├── code/               # Gemini tool implementation (Python/TS)
├── design/             # Gemini-specific design docs and ADRs
├── tests/              # Gemini-specific tool tests
└── .ai-workspace/      # Self-referential state (Dogfooding)
    ├── spec/           # Requirements for the Gemini implementation
    ├── events/         # Log of Gemini's own construction
    └── features/       # Feature vectors for Gemini tools
```

---

## Rationale

### Why Unified Root

1.  **Contextual Coherence**: Agents working on the Gemini implementation have all necessary context (code, design, and requirements) within a single root path. This eliminates "context bleed" from other designs.
2.  **Strict Isolation**: Each implementation is a self-contained "Genesis session." Gemini CLI's work on `imp_gemini` cannot collide with Codex's work on `imp_codex`.
3.  **Recursive Markov Boundary**: The entire folder becomes a single, stable Markov Object. It carries its own "DNA" (code) and its own "Memory" (state), making it perfectly portable and self-consistent.
4.  **Optimized Dogfooding**: By running methodology tools *inside* the folder they are managing, we ensure the tightest possible feedback loop for implementation validation.

---

## Consequences

### Positive

-   **Enhanced Security**: Path-based restrictions are easier to enforce.
-   **Simplified Navigation**: No jumping between repo-level `docs/` and `code/`.
-   **Deterministic State**: The `.ai-workspace` inside the folder is guaranteed to be 100% relevant to the implementation code next to it.

### Negative

-   **Shared Spec Complexity**: Technology-agnostic requirements might need to be synced between different implementation roots if they share the same base spec.
-   **Initial Scaffolding**: Requires moving existing files into the new structure.

---

## References

- [GEMINI_GENESIS_DESIGN.md](../GEMINI_GENESIS_DESIGN.md)
- [ADR-GG-006: Multi-tenant Workspace Structure](./ADR-GG-006-multi-tenant-workspace.md)
