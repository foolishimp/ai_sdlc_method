# ADR-S-037: Projection Authority and Convergence Evidence Validation

**Status**: PROPOSED — open for CONSENSUS review
**Date**: 2026-03-12
**Deciders**: pending ratification
**Tags**: methodology-core, event-stream, projection, convergence, workspace-integrity

---

## Context

The methodology declares the event stream as the foundational substrate from which all
workspace state is derived (Bootloader §V, ADR-S-012). ADR-S-036.1 separates invariant
primes from terminal manifestations, naming State Legibility and Observability as primes.

However, a structural gap exists: workspace files (feature vector YAMLs) can currently
assert convergence independently of the event stream. No interoceptive F_D evaluator
enforces that workspace claims are event-backed projections. The tooling cannot distinguish
genuine convergence from synthetic state.

This gap was discovered during post-mortem analysis of genesis_navigator (2026-03-12):
13 feature vectors claimed `status: converged` across 26 edges; the event log contained
zero `iteration_completed` or `edge_converged` events. The software was functionally correct.
The convergence was not evidenced — it was asserted. The homeostatic loop could not fire
because the sensor that would detect this condition did not exist.

The gap was posted to the methodology marketplace and reviewed by Claude, Codex, and Gemini.
All three concurred on diagnosis, framing, and resolution path. This ADR captures the
consensus outcome.

---

## Problem Statement

Four methodology invariants break simultaneously when workspace claims can outrank the
event substrate:

1. **Event-stream authority collapses** — ADR-S-012 declares state is derived from the
   event substrate. If mutable workspace fields can assert stronger state than the stream
   supports, the methodology becomes state-centric in practice while claiming event-sourcing
   in theory.

2. **Conformance stops being falsifiable** — Tenant equivalence depends on projection as the
   contract. If one implementation accepts workspace assertions as convergence evidence and
   another requires stream evidence, they are no longer testing the same methodology.

3. **Homeostasis becomes optional** — The homeostatic loop can only respond to what sensors
   can see. A convergence claim without stream evidence is invisible to the loop. The loop
   cannot restore integrity it cannot detect has been broken.

4. **Invariant primes degrade into declarations** — A prime with no enforcing sensor is not
   functioning as a constraint. It becomes descriptive rather than operative.

---

## Decision

### 1. Projection Authority Rule

A materialised workspace claim (feature vector YAML, status cache, projection artifact) may
summarise or cache projected state, but **MUST NOT assert a stronger convergence state than
the event substrate and artifact evidence jointly support.**

The event stream is authoritative. Workspace files are subordinate. Where a workspace file
claims `status: converged` and the event stream contains no supporting convergence evidence
for that feature+edge combination, the workspace file's claim is **invalid** — not merely
incomplete.

This rule is the primary decision of this ADR. All other elements are consequences of it.

### 2. Required Terminal Manifestation: Convergence Evidence Present

Added to the terminal manifestation set from ADR-S-036.1:

> **Convergence evidence present**: every workspace convergence claim must be backed by
> required event evidence in the event stream for the claimed feature+edge combination.

Prime basis: Observability + State Legibility (ADR-S-036.1).

### 3. F_D Health Check: `convergence_evidence_present`

Added to `gen-status --health` as a workspace integrity check (not an optional monitor
enhancement — a required F_D invariant):

```
convergence_evidence_present (F_D, workspace-integrity class):

  for each feature vector in .ai-workspace/features/active/ + completed/:
    for each edge where trajectory[edge].status == "converged":

      Phase 1 (required — existence check):
        search events.jsonl for any event with:
          event_type in {edge_converged, ConvergenceAchieved, iteration_completed}
          AND feature == vector.feature_id
          AND edge == edge_name
          AND status == "converged" (where applicable)
        if not found → FAIL

      Phase 2 (recommended — artifact hash link):
        if convergence event found:
          verify event's artifact content hash matches current artifact on disk
          if mismatch → WARN (artifact modified after convergence was recorded)

  On FAIL:
    emit evaluator_detail{
      check_name: "convergence_evidence_present",
      check_type: F_D,
      check_class: workspace_integrity,
      result: fail,
      observed: "no convergence event in stream for {feature}/{edge}",
      expected: "convergence event matching feature and edge"
    }
```

Phase 1 is sufficient for the immediate enforcement requirement. Phase 2 is the stronger
long-term check; it is advisory in this ADR and required in a future revision.

### 4. Workspace Integrity Signal

New entry in the `intent_raised` signal source taxonomy:

```json
{
  "signal_class": "workspace_integrity",
  "signal_source": "convergence_without_evidence",
  "affected_features": ["REQ-F-X-001"],
  "edge": "code↔unit_tests",
  "severity": "high",
  "delta": "convergence claimed; no event evidence in stream"
}
```

`signal_class: workspace_integrity` is introduced as a named class, leaving room for
sibling signals:
- `status_without_projection` — workspace status field not derivable from stream
- `feature_vector_without_lineage` — vector exists with no initialisation event
- `projection_drift` — cached projection diverges from stream replay

### 5. Remediation Path: Batched Audit Vector

When `convergence_without_evidence` is detected, the default remediation path is a **batched
audit/assurance vector** at project scope — not individual hotfix vectors per feature+edge.

Rationale: the initial defect is substrate-integrity debt, not N independent product defects.
The evaluation work is homogeneous. The output is primarily retroactive truthful events,
not per-feature code changes.

```
vector_type: audit
profile: standard
scope: workspace-wide convergence evidence sweep
convergence_criterion:
  all claimed-converged edges have valid convergence events in stream
  OR genuine delta found and refactored to zero
```

If re-evaluation finds real delta on specific features, the audit vector spawns
feature-local work for those features only. Evidence debt and implementation debt are
separated at triage, not assumed equivalent.

### 6. Retroactive Event Validity

Retroactive convergence events are valid under this ADR if they are:
- Artifact-grounded (the convergence reflects a real evaluator run against real artifacts)
- Appended to the stream with accurate timestamps and provenance
- Not contradicted by subsequent modification events for the same artifact

The projection function should prefer **causal/evidential validity** over naive append
recency. For Phase 1, existence of a valid convergence event is sufficient. Phase 2 adds
content hash verification.

Original synthetic events remain in the stream (immutable). Real convergence events appended
later supersede synthetic claims in the projection by evidential weight, not by deletion.

---

## Consequences

### Positive

- **"Converged" means evidenced** — the word carries its intended weight
- **Dark convergence becomes detectable** — a homeostatic sensor now exists for this class
  of substrate violation
- **Retroactive correction is valid methodology** — the genesis_navigator pattern (build
  first, evidence second) is supported provided real evaluators run and real events are
  appended. The path is not mandated; the evidence is.
- **Conformance is falsifiable** — tenant implementations can be tested: does the projector
  derive status from the stream, or does it trust workspace assertions?
- **Gemini implementation path is clear** — Strict Projection mode: Projector derives
  `InstanceNode` status exclusively from the event stream; YAML files are caches only

### Negative / Constraints

- **Existing workspaces with synthetic convergence will FAIL the new health check** — this
  is intentional. The failing check is the detection mechanism, not a regression. The
  remediation path (audit vector) resolves it.
- **Phase 2 (hash link) deferred** — artifact-event hash linking requires content hashing
  infrastructure not yet universal across implementations. Phase 1 (existence check) is the
  minimum viable invariant.
- **Projector refactoring required in all implementations** — Gemini notes the Projector
  currently trusts cached YAML; this ADR requires it to prefer stream evidence. All tenant
  implementations must update their projection layer.

---

## Relationship to Other ADRs

| ADR | Relationship |
|-----|-------------|
| **Bootloader §V** | Event stream as substrate — this ADR adds enforcement to the existing declaration. Bootloader unchanged (principle is already there; this ADR codifies the rule). |
| **ADR-S-012** | Event stream as formal model medium — projection authority rule makes ADR-S-012's intent enforceable at the workspace layer |
| **ADR-S-013** | Completeness visibility — adjacent but distinct. ADR-S-013 addresses convergence output visibility; this ADR addresses convergence claim validity. Not amended. |
| **ADR-S-036** | Invariants as termination conditions — this ADR adds an enforcement mechanism to the existing termination model |
| **ADR-S-036.1** | Invariant primes — `Convergence evidence present` added as a required terminal manifestation of Observability + State Legibility primes |

---

## Open Questions (for CONSENSUS review)

1. **Phase 2 timing**: Should the artifact-event hash link check (Phase 2) be required in
   this ADR with a deferred implementation date, or left as a future revision?

2. **Projector authority in YAML tooling**: Should workspace YAMLs be written to include
   a `evidence_status: stream_backed | asserted` field so tooling can cheaply distinguish
   without re-scanning the event log on every read?

3. **Audit vector type**: Is `vector_type: audit` a new vector type that needs formal
   definition (alongside feature, discovery, spike, poc, hotfix), or is it a profile
   configuration of an existing type?

---

*Proposed: 2026-03-12*
*Pre-consultation: Claude (GAP post), Codex (REVIEW), Gemini (REVIEW) — all concur*
*Applies to: all Genesis implementations*
