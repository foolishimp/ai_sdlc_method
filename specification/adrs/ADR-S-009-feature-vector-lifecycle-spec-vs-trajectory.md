# ADR-S-009: Feature Vector Lifecycle — Spec Definition vs. Operational Trajectory

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-03
**Revised**: 2026-03-14 (adds spec-file authority clarification and intent vector schema extension — ADR-S-027 Resolutions 3 and 5)
**Scope**: Feature vector two-layer model — `specification/features/`, `.ai-workspace/features/`, `requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` §6

---

## Context

The architecture of feature vectors as two-layer artifacts (spec definition + workspace trajectory) is correct and implied by the existing ADRs. ADR-S-006 establishes `specification/features/FEATURE_VECTORS.md` as the canonical Feature Decomposition artifact. ADR-S-002 establishes that `.ai-workspace/` is "not specification" — it holds derived projections, not authoritative content.

However, the boundary between the layers has never been formally stated. Three problems follow from this:

1. **Accidental definition duplication.** Without an explicit rule, implementations place requirement mappings and success criteria inside workspace YAML files (`.ai-workspace/features/active/*.yml`). In multi-tenant projects, these definitions must then be duplicated per implementation, and diverge silently. The spec layer and workspace layer now say different things about the same feature.

2. **No JOIN semantics.** Without a formal requirement that tools must join both layers, a tool can display only the features it knows about from the workspace — hiding features that exist in the spec but haven't been started yet. This makes "what is the total scope" invisible.

3. **No formal inflate operation.** `gen-spawn` creates a workspace trajectory, but there is no formal statement that this operation reads from the spec layer and projects a trajectory from it. Without this, spawn is an ad-hoc file write rather than a principled operation derived from the spec.

---

## Decision

### Two layers, one feature ID

The `REQ-F-*` key is the stable identifier. It appears in both layers. The layers have different content and different owners.

### Layer 1: Spec Definition (`specification/features/`)

**What it contains:**
| Field | Description |
|-------|-------------|
| Feature ID | `REQ-F-*` — stable, immutable |
| Title | Human-readable name |
| Satisfies | List of REQ-* keys this feature implements |
| What Converges | Observable outcomes at the product level (not the implementation level) |
| Dependencies | Edges in the feature dependency DAG |
| MVP scope | Whether this feature is in MVP or deferred |

**What it must NOT contain:**
- Trajectory state (iteration counts, delta, timestamps, convergence status)
- Implementation-specific asset paths
- Per-tenant progress information

**Owner:** The methodology author (human or homeostasis-approved agent). Written through the spec evolution process (ADR-S-010).

**Spec files are authoritative artifacts, not event projections.** `spec_modified` events (ADR-S-010) are the audit trail of changes to those files — they do not replace the files as source of truth. If a `spec_modified` event and the current file disagree (hash mismatch), the investigation begins with the file and git history, not by overwriting the file from the event log.

**Monitoring invariant**: a hash mismatch between a `specification/` file and its most recent `spec_modified` event MUST be classified as a **CRITICAL** gap by the sensory system. It triggers an `EVOLVE` cycle to resync the audit trail — either by emitting a corrective `spec_modified` event (if the file change was legitimate but unrecorded) or by reverting the file (if the change was unauthorised). This gap MUST NOT be silently ignored or deferred.

### Layer 2: Operational Trajectory (`.ai-workspace/features/active/*.yml`)

**What it contains:**
| Field | Description |
|-------|-------------|
| Feature ID | Reference back to the spec layer (join key) |
| Title | Copied from spec at inflate time — for display without joining |
| Intent | `INT-*` — for traceability |
| Vector type, profile, status | Control fields for the iterate engine |
| Trajectory | Per-node: status, iteration, delta, timestamps, escalations |
| Functor encoding | Mode, valence, overrides (per-implementation) |
| Time box | If applicable |
| Parent / children | Spawn lineage |

**What it must NOT contain:**
- Requirements mapping (`satisfies` list)
- Success criteria / product-level convergence descriptions
- Feature dependency DAG

**Owner:** The iterate engine and workspace commands. Written automatically during `gen-spawn` and `gen-iterate`.

### JOIN Semantics (formal requirement)

Any tool or command that displays features — including `gen-status`, monitor dashboards, and coverage views — **must** join both layers by feature ID:

```
display_features = JOIN(
    spec_features     = parse(specification/features/),
    workspace_vectors = parse(.ai-workspace/features/active/)
) ON feature_id
```

Resulting states:

| In Spec | In Workspace | Display State |
|---------|-------------|---------------|
| Yes | Yes | ACTIVE — show trajectory |
| Yes | No | PENDING — not yet started |
| No | Yes | ORPHAN — workspace vector has no spec definition (error) |

ORPHAN features are a workspace health violation. They arise when a feature was deleted from the spec but its workspace trajectory was not cleaned up, or when a trajectory was manually created without a spec definition.

### The Inflate Operation

`gen-spawn {REQ-F-ID}` is formally defined as:

1. Read the feature definition from `specification/features/` by feature ID.
2. Assert the feature exists in the spec (fail fast — no spec entry = no spawn).
3. Create `.ai-workspace/features/active/{REQ-F-ID}.yml` with:
   - Reference fields (feature ID, title) copied from spec
   - Empty trajectory (all nodes PENDING)
   - Default profile and functor encoding from project constraints
4. Emit `spawn_created` event to the event log.

The inflate operation is the inverse of the fold-back operation: it creates an empty trajectory from a spec definition, just as fold-back incorporates a completed trajectory's insights back into the parent.

### Profile zoom behaviour

| Profile | Feature definition location | Workspace trajectory |
|---------|----------------------------|----------------------|
| `full`, `standard` | `specification/features/` singleton | `.ai-workspace/features/active/` |
| `poc` | Inline with workspace (definition and trajectory co-located) | Same file |
| `spike` | Inline (question + findings replace definition + trajectory) | Same file |

For `poc` and `spike` profiles, the definition/trajectory split is collapsed — these are short-lived, throwaway vectors not intended to contribute to the permanent spec. If a PoC produces a finding worth formalising, it does so through `gen-spawn` (which requires a spec definition entry first).

### Intent Vector Schema Extension

`feature_vector` is formally a subtype of `intent_vector` (ADR-S-026 §4). The `.ai-workspace/features/active/*.yml` schema is extended with the following fields. All new fields are **optional for existing vectors**; **required for vectors created after 2026-03-09**.

| Field | Type | Notes |
|-------|------|-------|
| `source_kind` | enum | `abiogenesis \| gap_observation \| parent_spawn` |
| `trigger_event` | string \| null | Event ID that caused this vector; null for abiogenesis |
| `target_asset_type` | string | The asset type this vector produces |
| `composition_expression` | object | `{macro, version, bindings}` per ADR-S-026 §3 |
| `produced_asset_ref` | string \| null | Populated on convergence; null while iterating |
| `disposition` | enum \| null | `converged \| blocked_accepted \| blocked_deferred \| abandoned \| null` |

**Migration**: existing vectors without these fields are treated as `source_kind: abiogenesis` (if no trigger event exists) or `parent_spawn` (if spawned from another vector); `trigger_event: null`; `produced_asset_ref: null` (if active) or the known asset path (if converged); `disposition: null` (if active) or `converged` (if known converged).

The two-layer deployment model (spec definition / workspace trajectory) is unchanged — this extends the YAML schema, not the deployment model.

---

## Consequences

**Positive:**
- **No definition drift.** Requirements mappings exist in exactly one place (spec). Multi-tenant workspaces reference the same definition without duplication.
- **Scope visibility.** PENDING features are surfaced automatically from the spec — the total roadmap is always visible.
- **Orphan detection.** Workspace health checks can flag trajectories without corresponding spec entries.
- **Clean workspace.** `.ai-workspace/` remains a derived projection of the spec, as ADR-S-002 requires.

**Negative / Trade-offs:**
- Tools that previously only read `.ai-workspace/` must now also read `specification/features/`. This adds a read dependency to the spec layer.
- JOIN failure (spec layer unavailable) must be handled gracefully — tools should display workspace-only data with a warning, not fail silently.

---

## Alternatives Considered

**Keep full definition in workspace YAML**: Simplest for tooling — one file to read. Rejected — violates ADR-S-002 (workspace ≠ spec) and the one-writer rule. Definitions diverge per implementation.

**No JOIN requirement; workspace is the only source of truth for tools**: Tools read only the workspace. Features not started are simply invisible. Rejected — hides the gap between spec scope and actual progress. The "total possibility space" (Gemini's phrase) is the spec, not the workspace.

**Separate `specification/features/` per implementation**: Each `imp_*/` has its own feature definitions. Rejected — violates ADR-S-006 (Feature Decomposition is spec-side and tech-agnostic) and ADR-S-002 (shared contract). One feature decomposition, many implementations.

**PoC/spike collapse**: These profiles keep definition and trajectory co-located because the distinction has no value for short-lived explorations. This is not an alternative — it is a designed zoom behaviour, consistent with the projection profiles in ADR-S-006.

---

## References

- [ADR-S-006](ADR-S-006-feature-decomposition-node.md) — `specification/features/FEATURE_VECTORS.md` as the canonical spec-layer artifact
- [ADR-S-002](ADR-S-002-multi-tenancy-model.md) — `.ai-workspace/` is not specification; shared spec; one-writer rule
- [ADR-S-010](ADR-S-010-event-sourced-spec-evolution.md) — the process by which new features enter `specification/features/`
- [requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) §15 — REQ-EVOL-001 (trajectory-only workspace), REQ-EVOL-002 (JOIN semantics)
