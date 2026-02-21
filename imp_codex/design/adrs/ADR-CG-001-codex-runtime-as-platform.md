# ADR-CG-001: Codex Runtime as Target Platform

**Status**: Accepted  
**Date**: 2026-02-21  
**Deciders**: Codex Genesis Design Authors  
**Requirements**: REQ-TOOL-001, REQ-TOOL-002, REQ-TOOL-003  
**Supersedes**: ADR-001 (Claude Code as MVP Platform) - for Codex Genesis implementation

---

## Context

The AI SDLC Asset Graph Model is platform-agnostic but requires a concrete runtime binding. Claude is the reference implementation. We need a Codex-native binding that preserves methodology semantics and feature coverage.

Codex runtime primitives differ from Claude and Gemini:

- Tool-calling execution for shell and file operations
- Structured patch application for deterministic file mutation
- Parallel read/check execution
- Explicit conversational review turns for human accountability

### Options Considered

1. **Direct Claude command clone**: replicate slash command behavior exactly.
2. **Codex-native orchestration**: map operations directly to tool-calling routines.
3. **Hybrid binding**: retain command-shaped workflow while implementing execution with Codex-native tools.

---

## Decision

**We adopt the Hybrid binding (Option 3): command-shaped AI SDLC workflows implemented through Codex-native tool orchestration.**

Key mappings:

- Slash command intent -> `aisdlc_*` orchestration routines invoked via Codex tooling.
- Universal iterate agent -> universal iterate orchestrator that reads edge config and drives tools.
- Deterministic evaluators -> shell/test/lint/schema commands under explicit convergence policy.
- Human review -> explicit review boundary in conversation before promote/converge on human-required edges.

---

## Rationale

1. **Feature parity with Claude**: preserves the reference semantics while adapting runtime mechanisms.
2. **Deterministic execution surface**: shell + patch tooling produces auditable side effects and repeatability.
3. **Separation of concerns**: model/graph semantics remain in YAML and workspace files, not hard-coded in runtime glue.
4. **Portability**: shared `.ai-workspace` and event schema allow cross-runtime collaboration (Claude/Gemini/Codex).

---

## Consequences

### Positive

- Maintains 10/10 feature-vector alignment with the reference design.
- Keeps event sourcing and traceability contract unchanged.
- Enables incremental adoption without requiring a new modeling language.

### Negative

- Runtime glue code for orchestration is implementation-specific.
- Human review interactions are conversational unless a structured prompt helper is added.

### Mitigation

- Keep runtime-specific behavior in `codex` tenant and ADR set.
- Add a structured review helper in a follow-up ADR to standardize decision capture.
- Validate parity regularly against Claude feature matrix.

---

## References

- [CODEX_GENESIS_DESIGN.md](../CODEX_GENESIS_DESIGN.md)
- [AISDLC_V2_DESIGN.md](../../../imp_claude/design/AISDLC_V2_DESIGN.md)
- [GEMINI_GENESIS_DESIGN.md](../../../imp_gemini/design/GEMINI_GENESIS_DESIGN.md)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md)
