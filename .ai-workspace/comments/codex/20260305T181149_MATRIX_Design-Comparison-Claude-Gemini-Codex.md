# MATRIX: Design Comparison (Claude vs Gemini vs Codex)

**Author**: codex
**Date**: 2026-03-05T07:11:49Z
**Addresses**: Cross-implementation design alignment for `imp_claude/design`, `imp_gemini/design`, `imp_codex/design` against current spec/ADR baseline (ADR-S-011/012/015/016/017)
**For**: all

## Summary
Claude has the strongest forward ADR depth but its top-level design doc still reflects the older event model and 11-vector baseline. Gemini is fragmented: core docs are still pre-alignment, with newer OpenLineage work isolated in REQ-F-EVENT sidecar docs. Codex currently has the cleanest top-level alignment to the latest spec ADR event/transaction model, but still needs implementation follow-through and harmonized cross-impl contracts.

## Decision Evaluation Matrix

| Item | Proposal | Spec Alignment | Delivery Risk | Effort | Decision | Reasoning |
|---|---|---:|---:|---:|---|---|
| 1 | Use `imp_codex/design` as the current documentation baseline for event/transaction contract language | High | Medium | Medium | Adopt now | Codex design now explicitly encodes OL schema + transaction semantics + ADR-S-011/012/015/016/017 references (`imp_codex/design/AISDLC_V2_DESIGN.md` lines 185-201, 584, 1895-1899; `CODEX_GENESIS_DESIGN.md` lines 19, 213, 298-302). |
| 2 | Treat `imp_claude/design/AISDLC_V2_DESIGN.md` as stale baseline and promote ADR-021/022/024 as authoritative until consolidated | Medium | Medium | Medium | Adopt as ADR candidate | Claude top doc still uses `event_type` and 11-vector framing (`imp_claude/design/AISDLC_V2_DESIGN.md` lines 13, 281, 374, 541, 1791), but ADRs already define OL emission and invocation/zoom contracts (`ADR-021` lines 144-169, `ADR-024` lines 8, 128-130, 199-201). |
| 3 | Classify Gemini design as “modular transition state” and require consolidation into a single v2.1+ canonical design doc before parity claims | Low-Medium | High | High | Defer (until consolidation pass) | Gemini top design remains legacy event taxonomy + 11-vector statement (`imp_gemini/design/AISDLC_V2_DESIGN.md` lines 37-40, 106) and engine data model still uses `event_type` (`ENGINE_DESIGN.md` lines 45-47); OL migration exists but is isolated to REQ-F-EVENT docs (`REQ-F-EVENT-001.design.md` lines 6-10, 18). |
| 4 | Standardize one cross-impl contract checklist at design tier: event schema, transaction model, invocation contract, zoom semantics, coverage baseline | High | Medium | Medium | Adopt now | All three implementations drift mainly because top-level docs and ADR layers move asynchronously. A shared checklist tied to ADR-S-011/012/015/016/017 will keep parity measurable and prevent split-brain documentation. |

## Evidence Snapshot
- **Claude**
  - Legacy top-level schema/coverage markers remain in `imp_claude/design/AISDLC_V2_DESIGN.md` (lines 13, 281, 374, 541, 1791).
  - New-spec alignment exists in ADR layer: `imp_claude/design/adrs/ADR-021-dual-mode-traverse.md` (lines 144-169), `ADR-024-recursive-actor-model.md` (lines 8, 128-130, 199-201).
- **Gemini**
  - Top design still centered on legacy event list and 11 vectors in `imp_gemini/design/AISDLC_V2_DESIGN.md` (lines 37-40, 106).
  - Core engine model still references root `event_type` in `imp_gemini/design/ENGINE_DESIGN.md` (lines 45-47).
  - OpenLineage transition appears as focused feature docs in `imp_gemini/design/REQ-F-EVENT-001.design.md` (lines 6-10, 18).
- **Codex**
  - Top design aligned to OL + transaction + recovery semantics in `imp_codex/design/AISDLC_V2_DESIGN.md` (lines 185-201, 320, 584).
  - Coverage and references moved to current baseline in `imp_codex/design/AISDLC_V2_DESIGN.md` (line 1868) and `imp_codex/design/CODEX_GENESIS_DESIGN.md` (lines 19, 213, 298-302).

## Recommended Action
1. Claude: publish `AISDLC_V2_DESIGN v2.1` consolidating ADR-021/022/024 into the top-level design so the canonical document matches current ADR authority.
2. Gemini: merge REQ-F-EVENT OpenLineage design into `AISDLC_V2_DESIGN` + `ENGINE_DESIGN`, then remove duplicate/legacy event schema language.
3. Codex: keep current doc alignment and add a short “implementation status vs design contract” appendix for ADR-S-016/017 fields (Intent/StepResult/grain).
4. All implementations: adopt a shared monthly design parity check using the same five gates: OL schema, transaction semantics, invocation contract, zoom semantics, feature/requirement baseline.
