# ADR-S-027: Specification Consolidation — Authority Boundaries

**Series**: S
**Status**: Accepted
**Date**: 2026-03-09
**Revised**: 2026-03-14 (child ADR index updated — all child ADRs folded into parents and deleted)
**Scope**: Meta-ADR — resolves six authority conflicts across ADR-S-008 through ADR-S-026

**Review record**:
- Triggered by: Codex REVIEW `20260308T190451_REVIEW_Spec-ADR-integration-debt-and-authority-conflicts.md`
- Codex finding: "the spec has crossed the line where additional local improvements are starting to reduce global clarity"

**Note on numbering**: ADR-S-025 §Veto Role deferred veto semantics to "ADR-S-027 (pending)". Veto moves to ADR-S-028. This ADR takes the slot for consolidation — Codex classified consolidation as higher priority than veto extension.

---

## Context

Six overlapping authority regions emerged across ADR-S-008 through ADR-S-026. Each individual ADR is sound; the problem is the integration surface. Later ADRs extended earlier ones without declaring whether they amend, supersede, or interpret the earlier contract. The result is that different implementations can remain "spec compliant" while building materially different systems.

**The six conflicts** (Codex 20260308T190451):

| # | Severity | Conflict |
|---|----------|---------|
| 1 | HIGH | Event model forked — ADR-S-011 (transport) and ADR-S-012 (taxonomy) both claim to govern events; ADR-S-025/026 added event names in neither registry |
| 2 | HIGH | Homeostasis output double-specified — ADR-S-008 (`intent_raised`), ADR-S-010 (`feature_proposal`), ADR-S-026 (typed composition) without lifecycle crosswalk |
| 3 | HIGH | Asset source of truth ambiguous — ADR-S-012 event-first vs ADR-S-009/010 file-first |
| 4 | MED | "Consensus" names two mechanisms — ADR-S-024 (signal gate) vs ADR-S-025 (quorum functor) |
| 5 | MED | Vector envelope duplicated — ADR-S-009 (`feature_vector`) vs ADR-S-026 (`intent_vector`) without formal relationship |
| 6 | MED | Graph abstraction duplicated — ADR-S-006/007 (explicit nodes) vs ADR-S-026 (named compositions) without crosswalk |

---

## Resolutions

Each resolution has been folded directly into the parent ADR. The child ADRs originally created to implement these resolutions have been deleted as of 2026-03-14 and their content merged into the relevant parent file. This document is the authority for the resolution rationale; the parent ADR is the binding specification change.

### Resolution 1: Event Model — Single Registry with Layer Separation

**Authority assignment**:

- ADR-S-012 owns **semantic taxonomy**: event type names, required fields, causal semantics, saga invariant
- ADR-S-011 owns **transport encoding**: OL RunEvent shape, facet definitions, eventType mapping

These are different concerns. New event types MUST be registered in ADR-S-012 (semantic) AND ADR-S-011 (encoding) before use — in that order.

**Implementing ADRs** (folded in-place):
- `ADR-S-011` — CONSENSUS and Named Composition events registered in OL transport layer (§eventType mapping)
- `ADR-S-012` — same events registered in semantic taxonomy; projection scope limited to `.ai-workspace/` (§2, §8)

### Resolution 2: Homeostasis Output — Lifecycle Crosswalk

The lifecycle is a state machine with two paths from `intent_raised`:

```
intent_raised
  ├── requires_spec_change: false → composition_dispatched (no human gate)
  └── requires_spec_change: true  → feature_proposal → F_H gate → spec_modified → composition_dispatched
```

**Implementing ADRs** (folded in-place):
- `ADR-S-008` — `requires_spec_change` branch added to Stage 3 (§Stage 3 Amendment)
- `ADR-S-010` — `feature_proposal` only emits when `requires_spec_change: true` (§feature_proposal invariants)
- `ADR-S-026` — `requires_spec_change` field on composition expression schema

### Resolution 3: Asset Source of Truth — Domain Split

| Domain | Source of truth |
|--------|----------------|
| `specification/` | Files are authoritative; events audit changes |
| `.ai-workspace/` and code | Events are primary; files are materialized projections |

**Implementing ADRs** (folded in-place):
- `ADR-S-009` — spec-layer source-of-truth note and monitoring invariant added (§Layer 1)
- `ADR-S-012` — event-first model scope-limited to `.ai-workspace/` and code domains (§2)

### Resolution 4: Consensus Terminology

"Consensus" is reserved for ADR-S-025's quorum voting functor.
ADR-S-024's mechanism is renamed "Design Signal Gate".

**Implementing ADR** (folded in-place):
- `ADR-S-024` — renamed throughout; substance unchanged (title, all section headings, canonical terminology table)

### Resolution 5: Vector Envelope — Formal Mapping

`feature_vector` is a subtype of `intent_vector`. Formal mapping and YAML schema extension defined.

**Implementing ADRs** (folded in-place):
- `ADR-S-009` — intent_vector schema extension added to workspace YAML (§Intent Vector Schema Extension)
- `ADR-S-026` — vector subtype table present in §4

### Resolution 6: Graph Abstraction — Level Separation

ADR-S-006/007 (Level 5: execution topology) and ADR-S-026 (Level 3: authoring vocabulary) operate at different levels of the five-level stack. They are complementary, not competing. Named compositions compile to explicit topology nodes.

No child ADR required — the five-level stack in ADR-S-026 §1 already provides the crosswalk. This resolution is a clarification, not a spec change.

---

## Amendment Fold Record

As of 2026-03-14, the child ADR scheme has been retired (ADR-S-001 governance update). All children have been folded into their parent files and deleted. The table below records what was folded where:

| Former child ADR | Content now in | Resolution |
|-----------------|----------------|-----------|
| ADR-S-001.1 | ADR-S-001 §ADR Amendment Governance | ADR governance — edit-in-place rule |
| ADR-S-008.1 | ADR-S-008 §Stage 3 Amendment | Resolution 2: requires_spec_change branch |
| ADR-S-009.1 | ADR-S-009 §Layer 1, §Intent Vector Schema Extension | Resolutions 3, 5 |
| ADR-S-010.1 | ADR-S-010 §feature_proposal invariants, §Draft Features Queue | Resolution 2 |
| ADR-S-011.1 | ADR-S-011 §eventType mapping, §sdlc:event_type, §Registration protocol | Resolution 1 |
| ADR-S-012.1 | ADR-S-012 §2 (projection scope) + folded before this batch | Resolutions 1, 3 |
| ADR-S-024.1 | ADR-S-024 (full rewrite with rename) | Resolution 4 |
| ADR-S-026.1 | ADR-S-026 §3 | Resolutions 2, 5 |

---

## Invariants (binding on all implementations from this ADR forward)

1. **Event registration**: any new event type MUST be registered in ADR-S-012 (semantic) and ADR-S-011 (transport) before use.

2. **Homeostasis dispatch**: `intent_raised` MUST declare `requires_spec_change: true|false`. `true` prohibits autonomous dispatch until `spec_modified` is emitted.

3. **Source of truth by domain**: `specification/` files are authoritative. `.ai-workspace/` files are event projections. Not interchangeable.

4. **Consensus vocabulary**: "consensus" refers only to ADR-S-025's CONSENSUS functor. Marketplace signal evaluation is "Design Signal Gate" (ADR-S-024).

5. **Vector schema compliance**: intent vectors spawned after this ADR MUST include the full tuple (ADR-S-026 §4.1 + ADR-S-009.1 extensions). Existing vectors are grandfathered.

6. **Level separation**: named compositions (Level 3) compile to graph topology (Level 5). No implementation executes Level 3 directly.

---

## What does not change

- The four primitives and one operation
- The eight named functors in HIGHER_ORDER_FUNCTORS.md
- ADR-S-025 CONSENSUS semantics
- ADR-S-026 named compositions, five-level stack, intent vector tuple
- ADR-S-009 two-layer deployment model
- `graph_topology.yml` structure
- Veto extension — moved to ADR-S-028

---

## References

- Codex REVIEW: `.ai-workspace/comments/codex/20260308T190451_REVIEW_Spec-ADR-integration-debt-and-authority-conflicts.md`
- ADR-S-001 — ADR amendment governance (edit-in-place rule)
- ADR-S-008, ADR-S-009, ADR-S-010, ADR-S-011, ADR-S-012, ADR-S-024, ADR-S-026 — resolution-implementing parent ADRs (children folded in)
- ADR-S-028 — Veto Role Extension (pending)
