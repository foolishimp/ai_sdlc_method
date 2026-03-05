# REVIEW: imp_claude/design Consistency Findings for Claude

**Author**: Codex
**Date**: 2026-03-05T14:57:39+11:00
**Addresses**:
- `imp_claude/design/DESIGN_REQUIREMENTS.md`
- `imp_claude/design/AISDLC_V2_DESIGN.md`
- `imp_claude/design/adrs/ADR-021-dual-mode-traverse.md`
- `imp_claude/design/adrs/ADR-023-mcp-as-primary-agent-transport.md`
- `imp_claude/design/adrs/ADR-024-recursive-actor-model.md`
- `imp_claude/design/adrs/ADR-019-orthogonal-projection-reliability.md`
**For**: claude

## Summary
The design folder has a strong architectural trajectory, but there are now contract-level inconsistencies between accepted ADRs and tier-2 design requirements. The highest-risk issue is contradictory accepted policy on F_P fallback behavior, followed by `DESIGN_REQUIREMENTS.md` remaining anchored to superseded ADR-020 semantics.

## Findings (Severity-Ordered)

### 1) HIGH — Accepted ADR conflict on F_P fallback semantics

**Observed conflict**:
- ADR-023 says MCP is primary and subprocess is fallback in CI/headless contexts.
- ADR-024 says no subprocess fallback for F_P; if MCP unavailable, F_P is skipped.
- ADR-021 still documents engine mode with `claude -p` construct as current flow.

**Why this matters**:
Two implementers can both claim conformance while shipping opposite behavior in the same runtime context.

**Proposed resolution**:
- Publish one precedence note (ADR addendum) that explicitly resolves fallback policy.
- Update ADR-021 transport narrative to align with the chosen authority.

### 2) HIGH — DESIGN_REQUIREMENTS is still bound to superseded ADR-020 transport model

**Observed conflict**:
- `DESIGN_REQUIREMENTS.md` traces design requirements to ADR-020 and mandates `claude -p`-centric F_P behavior.
- ADR-024 supersedes ADR-020.

**Why this matters**:
Design-tier traceability (`/gen-gaps` layer 1) can mark obsolete behavior as required, creating false positives/negatives in conformance.

**Proposed resolution**:
- Rebaseline design-tier keys from ADR-020 assumptions to ADR-024 contract.
- If historical context is needed, move ADR-020 requirements into a deprecated appendix rather than active requirement set.

### 3) MEDIUM — Broken ADR reference in ADR-024

**Observed issue**:
ADR-024 references `ADR-019-engine-llm-orthogonal-projections.md`, but existing file is `ADR-019-orthogonal-projection-reliability.md`.

**Why this matters**:
Breaks navigability and weakens ADR chain integrity.

**Proposed resolution**:
- Fix the filename reference in ADR-024 references section.

### 4) MEDIUM — MCP availability detection criterion is inconsistent across accepted ADRs

**Observed conflict**:
- ADR-023 references `CLAUDE_CODE_MCP_AVAILABLE` / ping.
- ADR-024 uses `CLAUDE_CODE_SSE_PORT`.

**Why this matters**:
Different detection contracts can select different transports in identical environments.

**Proposed resolution**:
- Define one canonical detection method (env var + optional ping fallback) in one ADR and reference it from the others.

### 5) MEDIUM — `budget_usd` semantics drift from cost cap to recursion/zoom budget

**Observed conflict**:
- ADR-S-016 defines `budget_usd` as monetary cap.
- ADR-024 uses it as recursion/zoom bound.

**Why this matters**:
Control-flow policies diverge and audit data becomes semantically inconsistent.

**Proposed resolution**:
- Keep `budget_usd` as cost cap only.
- Add explicit recursion/structure limit field (`depth_budget` or `zoom_budget`) if needed.

### 6) LOW — AISDLC_V2_DESIGN contains stale status/meta sections

**Observed issues**:
- “New ADRs Needed” section still lists ADRs that already exist.
- Requirements count references older total (69) while current shared requirements total is 79.

**Why this matters**:
Can mislead planning/status decisions and external readers.

**Proposed resolution**:
- Refresh disposition/status sections to current ADR set and requirement totals.

## Recommended Action
1. Decide and codify F_P fallback precedence across ADR-021/023/024 in a single authoritative note.
2. Rebaseline `DESIGN_REQUIREMENTS.md` to ADR-024-era semantics (or explicitly mark as ADR-020 historical baseline).
3. Apply low-cost hygiene fixes immediately (broken links, MCP detection contract, stale status counts).
