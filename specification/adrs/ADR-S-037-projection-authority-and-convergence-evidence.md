# ADR-S-037: Projection Authority and Convergence Evidence Validation

**Status**: PROPOSED — open for CONSENSUS review (REVIEW-adr-s-037-1)
**Date**: 2026-03-12
**Deciders**: pending ratification
**Tags**: methodology-core, event-stream, projection, convergence, workspace-integrity

---

## Context

ADR-S-012 declares the event stream as the authoritative substrate from which all workspace
state is derived. ADR-S-036.1 names Observability and State Legibility as invariant primes,
with convergence evidence as a required terminal manifestation.

However, no F_D check enforces this at the workspace boundary. Feature vector YAMLs can
currently claim `status: converged` without any corresponding convergence event in the stream.
The tooling cannot distinguish genuine convergence from synthetic state. The homeostatic loop
cannot detect the gap because the sensor does not exist.

This was discovered during post-mortem analysis of genesis_navigator (2026-03-12): 13 feature
vectors claimed convergence across 26 edges; the event log contained zero `iteration_completed`
or `edge_converged` events. The software was functionally correct. The convergence was asserted,
not evidenced.

Pre-consultation: Claude (GAP post), Codex (two REVIEWs), Gemini (REVIEW) — all concur on
diagnosis. Codex specifically: keep the fix minimal — make existing structure operative rather
than introducing new invariant families or vector types.

---

## Decision

### 1. Projection Authority Rule

A materialised workspace claim (feature vector YAML, status cache, any derived artifact) may
cache or summarise projected state, but **MUST NOT assert a stronger convergence state than
the event substrate supports.**

This makes explicit what ADR-S-012 already implies: the event stream is authoritative;
workspace files are subordinate caches. Where a workspace file claims `status: converged` and
the stream contains no supporting evidence for that feature+edge, the claim is invalid.

### 2. F_D Check: `convergence_evidence_present`

Added to `gen-status --health` as a required workspace integrity check:

```
convergence_evidence_present (F_D):

  for each feature vector in .ai-workspace/features/active/ + completed/:
    for each edge where trajectory[edge].status == "converged":

      search events.jsonl for a terminal convergence event matching:
        event_type in {edge_converged, ConvergenceAchieved}   ← canonical per REQ-EVENT-003
        AND (feature == vector.feature_id OR instance_id == vector.feature_id)
        AND edge == edge_name

      if not found → FAIL:
        report: "convergence claimed for {feature}/{edge} — no stream evidence"
```

The check requires a **terminal convergence event** (`edge_converged` / `ConvergenceAchieved`
per REQ-EVENT-003), not any lifecycle event. Explicitly:

- `edge_started` alone: does NOT satisfy it
- `iteration_completed` (even with `status: converged`): does NOT satisfy it —
  `IterationCompleted` is a lifecycle event, not a terminal convergence event
- `edge_converged` / `ConvergenceAchieved`: satisfies it

This alignment with REQ-EVENT-003's convergence event class (`ConvergenceAchieved`) keeps
the check consistent with the canonical event taxonomy.

### 3. Retroactive Attribution Rule

Retroactively populated convergence events are valid provided they are:
- Grounded in a real evaluator run against the actual artifacts (tests passed, delta=0)
- Appended to the stream with accurate timestamps reflecting when evaluation occurred
- Marked with `"emission": "retroactive"` on the event (per REQ-EVENT-005 executor attribution schema)
  so observability debt remains legible

A retroactive event that accurately records a real evaluator result closes the evidence gap.
A retroactive event that fabricates a result violates this rule and the Projection Authority
Rule simultaneously.

The `emission: retroactive` marker is not a penalty — it is traceability. It distinguishes
"we ran real evaluators after the fact and confirmed clean" from "we always had stream evidence."
Both are valid states. Only the latter is invisible to future readers without the marker.

**Naming**: Use `"emission": "retroactive"` (REQ-EVENT-005 field) not a separate `"retroactive": true`
data field. These are the same concept; REQ-EVENT-005's schema is canonical.

---

## What This Does Not Change

- **No new invariant primes** — Observability and State Legibility (ADR-S-036.1) already
  cover this. This ADR adds the enforcing check, not a new prime.
- **No new signal classes or signal taxonomies** — the existing `intent_raised` event with
  `signal_source: convergence_without_evidence` is sufficient. No new class hierarchy needed.
- **No new vector types** — the remediation path uses existing vector types. A hotfix or
  standard vector scoped to re-evaluation is sufficient. `vector_type: audit` is deferred
  unless a concrete implementation need cannot be met with existing types.
- **Bootloader unchanged** — §V and §VIII already provide the governing principles. The
  missing piece was enforcement, not a new axiom.

---

## Consequences

### Positive

- **"Converged" means evidenced** — the existing prime structure now has a sensor
- **Homeostatic loop can fire** — `convergence_without_evidence` becomes detectable and
  routable via existing `intent_raised` machinery
- **Retroactive correction is valid methodology** — build-first patterns are supported
  provided real evaluators run and real events (marked retroactive) are appended
- **Conformance is falsifiable** — tenant projectors can be tested: does the projector
  derive status from the stream, or does it trust workspace assertions?

### Negative / Constraints

- **Existing workspaces with synthetic convergence will fail the new check** — intentional;
  this is the detection mechanism working correctly
- **All tenant projectors must enforce substrate primacy** — workspace YAMLs are caches;
  the projector must prefer stream evidence over YAML assertions

---

## Relationship to Other ADRs

| ADR | Relationship |
|-----|-------------|
| **ADR-S-012** | This ADR makes the projection contract enforceable at the workspace claim boundary |
| **ADR-S-036.1** | Convergence evidence added as a required terminal manifestation of Observability + State Legibility primes |
| **ADR-S-013** | Adjacent (completeness visibility) but distinct — ADR-S-013 is about output visibility; this is about claim validity |
| **Bootloader §V, §VIII** | Unchanged — governing principles already present; this ADR adds enforcement |

---

*Proposed: 2026-03-12*
*Pre-consultation: Claude, Codex, Gemini — all concur*
*Applies to: all Genesis implementations*
