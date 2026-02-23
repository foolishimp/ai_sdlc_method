# ADR-CG-006: Artifact Write Observation via PostToolUse Hook

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Methodology Author
**Requirements**: REQ-SENSE-006, REQ-TOOL-006, REQ-LIFE-008
**Extends**: ADR-011 (Consciousness Loop), ADR-015 (Sensory Service), ADR-CG-001 (Codex Runtime)

---

## Context

The protocol enforcement hooks (§7.7, ADR-011) ensure that iterate() produces mandatory side effects. But when iterate() is bypassed — as it was in test05 and test07 — the hooks never fire. The methodology's observability evaporates.

Rather than forcing all work through iterate() (which would block optimization as LLMs improve), we add a second observability layer: detect artifact creation at the file-write level, regardless of how the write was triggered.

This is the invariant-observation end of the observability sliding scale (§7.7.5). It provides a floor of visibility that holds even when the iterate process is optimized away.

### Options Considered

1. **PreToolUse block** — Prevent writes unless edge_in_progress exists. Forces iterate(). Gets full evaluator data but blocks optimization.
2. **PostToolUse observation** — Emit thin events on artifact writes. Non-blocking. Detects bypasses without preventing them.
3. **Session-end scan** — Check at session boundary for untracked changes. Zero overhead but post-hoc only.
4. **Bootloader enforcement** — Stronger CLAUDE.md constraints. Behavioral, not structural.

---

## Decision

**PostToolUse observation (Option 2).** A hook on `Write|Edit` tool completions maps file paths to asset types and emits `artifact_modified` events. First write to a new asset type per session also emits `edge_started`.

The hook is pure observation — it never blocks, never fails the tool call, and never runs evaluators. It is a reflex-layer sensory input (§4.3).

### Why Not Block (Option 1)

Blocking optimizes for process compliance at the cost of construction speed. As LLMs improve, the value of iterate() is in the evaluators and convergence checks, not in the ceremony of invoking it. A fast agent that produces correct artifacts in one pass should not be slowed down by protocol ceremony. The observability floor ensures we can audit and track progress regardless.

### Why Not Session-End Only (Option 3)

Session-end scanning provides audit data but not real-time progress. A developer watching the genesis-monitor during a long build sees nothing until the session ends. Real-time `artifact_modified` events show work happening as it happens — which files, which asset types, at what rate.

---

## Consequences

### Positive
- Every artifact write visible in events.jsonl regardless of invocation path
- Genesis Monitor shows real-time progress even when iterate() is bypassed
- Audit trail for root cause analysis of failures
- Non-blocking — never interferes with construction speed
- Closes the bypass gap documented in test05/test07

### Negative
- Thin events (file_path + asset_type) vs rich events from iterate() (evaluators, delta, findings)
- Path-to-asset mapping is heuristic-based (directory names), may need per-project configuration
- Hook fires on every Write/Edit (~10-15ms overhead)
- Two observability tiers create complexity: which events came from iterate vs direct writes?

### Implementation
- New script: `on-artifact-written.sh` in hooks/
- Registered in hooks.json as PostToolUse matcher on `Write|Edit`
- Session tracking via `.ai-workspace/.session_assets_seen`
- Cleared by `on-session-start.sh` at session boundary

---

## Requirements Addressed

- **REQ-SENSE-006**: Artifact write observation — file-level event emission for all writes
- **REQ-TOOL-006**: Methodology hooks — adds artifact write to trigger list
- **REQ-LIFE-008**: Protocol enforcement — provides evidence when iterate is bypassed

## References

- ADR-011: Consciousness Loop at Every Observer Point
- ADR-015: Sensory Service Technology Binding
- ADR-CG-001: Codex Runtime as Platform
- Spec §7.7: Protocol Enforcement Hooks
- Spec §7.7.5: Bypass Detection and the Observability Sliding Scale
