# ADR-CG-002: Universal Iterate Orchestrator for Codex Runtime

**Status**: Accepted  
**Date**: 2026-02-21  
**Deciders**: Codex Genesis Design Authors  
**Requirements**: REQ-ITER-001, REQ-ITER-002, REQ-EVAL-001, REQ-EVAL-002

---

## Context

The methodology requires one universal `iterate()` operation whose behaviour is defined by edge parameterisation, not by stage-specific agents. In Codex runtime, execution happens through tool calls (`exec_command`, `apply_patch`, `multi_tool_use.parallel`) rather than provider-native slash-command runtime semantics.

We need a Codex-native orchestration pattern that preserves graph semantics and evaluator composition from the shared specification.

## Decision

Use a **single orchestrator routine** (`aisdlc-iterate`) that:

1. Loads edge config from `.ai-workspace/graph/edges/{edge_config}`.
2. Resolves context from tenant-first paths (`.ai-workspace/codex/context/` then `.ai-workspace/context/`).
3. Builds an effective checklist by composing edge checks, project constraints, profile overrides, and feature overrides.
4. Executes evaluator chains as configured (`human`, `agent`, `deterministic`).
5. Emits mandatory protocol side effects (event append, feature projection update, status projection update).

No edge-specific codepaths are allowed outside configuration and checklist composition.

## Rationale

- Preserves the Markov-style transition model and avoids stage hardcoding.
- Keeps behavioural parity with `imp_claude` while using Codex-native execution primitives.
- Makes new edges configurable (YAML changes) rather than procedural (orchestrator code changes).

## Consequences

### Positive

- Deterministic, inspectable behaviour per edge.
- Lower maintenance cost for feature expansion.
- Easier cross-implementation parity checks against `imp_claude`.

### Negative

- More responsibility in configuration quality and validation.
- Requires strong config tests to prevent silent drift.

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §3, §7.5
- [AISDLC_V2_DESIGN.md](../AISDLC_V2_DESIGN.md) §2.1
- [ADR-008-universal-iterate-agent.md](ADR-008-universal-iterate-agent.md)
