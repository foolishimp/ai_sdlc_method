# REVIEW: ADR Follow-Up on Child Structure and Residual Gaps

**Author**: codex
**Date**: 2026-03-09T02:05:52+1100
**Addresses**: `specification/adrs/ADR-S-001.1-hierarchical-adr-numbering.md`, `specification/adrs/ADR-S-008.1-requires-spec-change-branch.md`, `specification/adrs/ADR-S-009.1-intent-vector-schema-extension.md`, `specification/adrs/ADR-S-010.1-requires-spec-change-invariant.md`, `specification/adrs/ADR-S-011.1-event-type-registrations.md`, `specification/adrs/ADR-S-012.1-projection-scope-and-event-registrations.md`, `specification/adrs/ADR-S-024.1-rename-to-design-signal-gate.md`, `specification/adrs/ADR-S-026.1-requires-spec-change-and-subtype-table.md`, `specification/adrs/ADR-S-027-spec-consolidation-authority-boundaries.md`
**For**: all

## Summary
This materially improves the spec. My March 8 review was about unresolved authority boundaries; ADR-S-027 plus the new child ADR structure directly addresses that problem, and ADR-S-001.1 gives the series a governance model that should reduce future drift instead of merely documenting it.

My price is now meaningfully higher. The accepted ADR set is no longer in the "overlapping authorities everywhere" state. Most of the earlier conflict clusters are now structurally resolved. What remains is smaller and more specific: one execution-contract gap around named composition dispatch, and one residual typing ambiguity around how gap-driven work on existing REQ keys maps into the new intent-vector subtype model.

## What the New Structure Fixed

### 1. Authority is now explicit instead of implicit
ADR-S-027 is the key improvement. It does not just note that conflicts existed; it assigns owners and names the resolution path by parent/child pair. That is the right corrective move.

The best part is that the structure now answers the earlier meta-problem:
- parent ADR establishes the stable local contract,
- child ADR carries the delta,
- ADR-S-027 provides the cross-ADR authority matrix.

That is much better than letting later ADRs silently extend earlier ones without declaring the relationship.

### 2. ADR-S-001.1 is a real governance improvement
ADR-S-001.1 explains the amendment model cleanly:
- parent ADRs are immutable,
- child ADRs are the active deltas,
- only one live child per parent should remain in the filesystem,
- git history retains withdrawn reasoning.

That directly addresses the "zombie files bias LLM readers toward stale reasoning" problem. It is a good rule for this repo's actual operating mode.

### 3. The six earlier conflict clusters were mostly resolved
Relative to my prior review:

- Event model conflict: substantially resolved. ADR-S-012 now owns semantic taxonomy; ADR-S-011 owns transport encoding; ADR-S-011.1 and ADR-S-012.1 register the missing event types.
- Homeostasis output conflict: substantially resolved. ADR-S-008.1, ADR-S-010.1, and ADR-S-026.1 now provide the `requires_spec_change` crosswalk.
- Source-of-truth conflict: substantially resolved. ADR-S-009.1 and ADR-S-012.1 draw a domain split between `specification/` and `.ai-workspace/`.
- Consensus naming conflict: resolved. ADR-S-024.1 cleanly separates Design Signal Gate from CONSENSUS.
- Vector duplication: improved. ADR-S-009.1 and ADR-S-026.1 at least provide a formal subtype mapping instead of leaving the relationship completely implicit.
- Graph abstraction duplication: improved. ADR-S-027 makes the intended level separation explicit.

That is enough that I would no longer describe the spec as generally suffering from unresolved authority overlap. The architecture is still ambitious, but the governance and integration story is now much more coherent.

## Residual Findings

### 1. Medium: `composition_dispatched` still lacks a binding compile/dispatch contract
ADR-S-027 invariant 6 says Level 3 named compositions compile to Level 5 graph topology and that implementations do not execute Level 3 directly. That is a good boundary.

But ADR-S-008.1 says `requires_spec_change: false` intents are dispatchable and notes that the implementation "resolves macro from registry." ADR-S-026 still describes the execution contract as requiring:
- macro registry,
- binding validation,
- compilation rule from macro to graph fragment or operator expansion,
- scope policy.

That means the conceptual conflict is fixed, but the execution contract is still not fully bound. The spec now says:
- Level 3 is not directly executed,
- yet dispatch happens from a Level 3 expression,
- without one normative description of the compilation artifact or operator expansion step.

This is no longer a governance conflict. It is now a straightforward missing contract. The next child ADR in this area should define exactly what `composition_dispatched` points to:
- compiled graph fragment,
- operator expansion,
- named workflow template,
- or some other executable intermediate.

### 2. Medium: the subtype table still leaves one important lineage case underspecified
ADR-S-009.1 and ADR-S-026.1 define:

`feature_vector = intent_vector where source_kind ∈ {abiogenesis, parent_spawn}`

But ADR-S-008.1 and ADR-S-010.1 also create a world where an observed gap on an already-defined REQ key can become dispatchable work without going through `feature_proposal`.

That raises a remaining typing question:
- if an implementation gap is discovered against an existing `REQ-F-*`,
- and that work is dispatched directly,
- is the resulting active unit a `feature_vector`,
- a different `intent_vector` subtype,
- or a transient repair vector attached to the feature?

Right now the spec strongly suggests "active intent vector," but the subtype boundary is not explicit enough for all implementations to encode it the same way. This is especially relevant for telemetry gaps, test gaps, and design/code closure work on already-ratified features.

I would not call this a contradiction anymore, but I would call it an underspecified case that will produce tenant drift if left open.

## Net Repricing
My previous review said the spec had crossed into integration debt and needed consolidation before more expansion. That was correct at the time.

With ADR-S-027 and the child ADR series now accepted, the consolidation has largely happened. I would now reprice the spec as:
- structurally coherent at the governance layer,
- materially improved at the semantic authority layer,
- still missing one executable contract for macro dispatch,
- and still needing one sharper rule for gap-driven vector typing.

That is a much healthier place than where the ADR set was on March 8.

## Recommended Action
1. Treat ADR-S-027 plus its child ADRs as a successful consolidation pass; do not reopen the original six conflict clusters unless a concrete counterexample appears.
2. Write one follow-on ADR that binds `composition_dispatched` to a concrete executable intermediate and closes the Level 3 to Level 5 contract.
3. Write one narrow clarification ADR or amendment that states how gap-driven work on existing `REQ-F-*` maps into the intent-vector subtype model.
4. Keep the ADR-S-001.1 child pattern. It is the right structure for this repository.
