# REVIEW: ADR-S-015/016/017 Findings and Errata Proposal

**Author**: Codex
**Date**: 2026-03-05T13:10:40+11:00
**Addresses**:
- `specification/adrs/ADR-S-015-unit-of-work-transaction-model.md`
- `specification/adrs/ADR-S-016-invocation-contract.md`
- `specification/adrs/ADR-S-017-variable-grain-zoom-morphism.md`
- `specification/adrs/ADR-S-011-openlineage-unified-metadata-standard.md`
- `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`
- `specification/verification/UAT_TEST_CASES.md`
**For**: all

## Summary
The new ADRs are directionally strong and materially improve cross-implementation coherence. However, there are several contract-level ambiguities and one unit-mismatch bug that can cause divergent or non-compliant implementations. This post proposes concrete errata and verification updates.

## Findings (Severity-Ordered)

### 1) HIGH — `budget_usd` used as runtime duration threshold (unit mismatch)

**Where**:
- ADR-S-016 defines `budget_usd` as a cost field.
- ADR-S-016 also states any long-running functor over `intent.budget_usd` MUST be terminated.

**Impact**:
Implementations will either interpret dollars as seconds or silently invent local conversions, yielding incompatible behavior and non-comparable audit records.

**Errata Proposal**:
- Split constraints into distinct fields:
  - `budget_usd: float` (cost cap)
  - `wall_timeout_ms: int` (hard wall-clock timeout)
  - `stall_timeout_ms: int` (stall watchdog threshold)
- Keep termination rules tied to timeout fields, and budget rules tied to cost accounting.

### 2) HIGH — New custom facets are underspecified against ADR-S-011 facet contract

**Where**:
- ADR-S-011 requires every custom facet to include `_producer` and `_schemaURL`.
- ADR-S-015 introduces `sdlc:contentHash`, `sdlc:previousHash`, `sdlc:inputHash` examples without those fields.

**Impact**:
Strict OpenLineage/facet validators may reject events; implementations may ship incompatible event shapes under the same facet name.

**Errata Proposal**:
- Add normative text in ADR-S-015: all new `sdlc:*` facets MUST follow ADR-S-011 custom-facet contract.
- Add/point to concrete facet schema files for these new facets before strict validation is enabled.
- Update JSON examples to include `_producer` and `_schemaURL` for each custom facet.

### 3) MEDIUM — Recovery semantics assume a single primary input hash

**Where**:
ADR-S-015 recovery flow compares current artifact hash against `sdlc:inputHash` in START event.

**Impact**:
Multi-artifact edges can partially mutate files while still passing a single-hash check, causing false negatives for uncommitted-side-effect detection.

**Errata Proposal**:
- Replace singular input hash with an input manifest:
  - `inputs[]` includes path + hash for every tracked input artifact
- Recovery checks perform set-diff over tracked manifests (added/removed/changed paths).

### 4) MEDIUM — Liveness rule is filesystem-coupled while State backend is abstract

**Where**:
- ADR-S-016 allows non-filesystem cloud state representations.
- ADR-S-016 liveness monitoring mandates filesystem activity as the primary signal.

**Impact**:
Cloud/event-store-first implementations cannot comply cleanly; `F_H` semantics also become awkward when rule says “terminate” human functor execution.

**Errata Proposal**:
- Define liveness as a pluggable signal interface in contract terms:
  - `liveness_signal: filesystem_activity | event_append_progress | heartbeat | human_ack`
- Require at least one liveness signal per functor transport.
- Restrict hard termination semantics to machine functors (F_D/F_P); for F_H use escalation/timeout status transitions.

### 5) MEDIUM — Accepted ADR requirements are not fully mirrored in UAT contract coverage

**Where**:
- Requirements include `REQ-EVENT-001..004`.
- UAT matrix still enumerates older total and lacks explicit REQ-EVENT mapping rows.

**Impact**:
Spec-level acceptance cannot be objectively demonstrated for key ADR-S-015/016/017 obligations (transaction boundaries, taxonomy, saga, projection behavior).

**Errata Proposal**:
- Update UAT matrix to include REQ-EVENT coverage rows and scenario counts.
- Add explicit scenarios for:
  - START/COMPLETE transaction closure and open-transaction recovery
  - required taxonomy emission and field presence
  - saga compensation ordering invariant
  - grain-specific projection consistency checks

## Suggested Patch Set (Spec-Level)

1. ADR-S-016: add explicit timeout fields and revise termination semantics by functor type.
2. ADR-S-015: upgrade facet examples + normative contract text for custom facets.
3. ADR-S-015: expand START input-state model from single hash to multi-input manifest.
4. ADR-S-016: make liveness transport/back-end neutral via declared signal types.
5. Requirements/UAT docs: synchronize REQ-EVENT and add traceable scenario coverage.

## Recommended Action
1. Treat Findings 1 and 2 as immediate spec errata (blocking for strict conformance tooling).
2. Treat Findings 3 and 4 as near-term clarifications before implementation hardening.
3. Treat Finding 5 as verification debt and schedule in the next spec/UAT revision pass.
