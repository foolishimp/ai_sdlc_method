# Roo Code ADRs

Architecture Decision Records for the Roo Code AISDLC solution.

## ADR Numbering

Roo Code ADRs start at **ADR-201** to avoid conflicts with:
- Claude Code ADRs (ADR-001 to ADR-099)
- Codex ADRs (ADR-101 to ADR-199)

## Current ADRs

| ADR | Title | Status | Requirements |
|-----|-------|--------|--------------|
| [ADR-201](ADR-201-custom-modes-for-stage-personas.md) | Custom Modes for Stage Personas | Accepted | REQ-F-CMD-002, REQ-F-PLUGIN-001/002 |
| [ADR-202](ADR-202-rules-library-for-shared-instructions.md) | Rules Library for Shared Instructions | Accepted | REQ-F-TESTING-001/002, REQ-NFR-TRACE-001/002, REQ-NFR-REFINE-001 |
| [ADR-203](ADR-203-memory-bank-for-persistent-context.md) | Memory Bank for Persistent Context | Accepted | REQ-NFR-CONTEXT-001, REQ-F-WORKSPACE-003 |
| [ADR-204](ADR-204-workspace-safeguards-and-safety-model.md) | Workspace Safeguards and Safety Model | Accepted | REQ-F-WORKSPACE-001, REQ-F-CMD-001, REQ-NFR-TRACE-002 |

## Summary

### ADR-201: Custom Modes for Stage Personas
Decided to use individual mode files in `.roo/modes/` (one per SDLC stage) rather than a single `.roomodes` file. This provides modularity, clear mapping to Claude agents, and independent customization.

### ADR-202: Rules Library for Shared Instructions
Decided to store shared instructions (Key Principles, TDD, BDD, REQ tagging, feedback protocol, safeguards) in `.roo/rules/` and load via `@rules/<filename>` syntax. This enables DRY principles and consistent behavior across modes.

### ADR-203: Memory Bank for Persistent Context
Decided on hybrid approach: use Roo memory bank for Roo-specific context (`projectbrief.md`, `techstack.md`, `activecontext.md`, `methodref.md`) while sharing `.ai-workspace/` structure with Claude/Codex for task tracking.

### ADR-204: Workspace Safeguards and Safety Model
Documented safety model including idempotency, validation-first, no destructive overwrites, backup before modify, and REQ tagging enforcement. Implemented via `workspace-safeguards.md` rule and mode instructions.

## Creating New ADRs

Use template:
```markdown
# ADR-2XX: Title

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
Why is this decision needed?

## Decision
What is the change being proposed?

## Consequences
What are the results of this decision?

## References
- REQ-* keys addressed
- Related ADRs
```
