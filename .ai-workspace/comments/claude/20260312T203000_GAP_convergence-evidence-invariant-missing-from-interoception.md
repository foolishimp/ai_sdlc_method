# GAP: Convergence Evidence Invariant Missing from Interoception

**Author**: claude
**Date**: 2026-03-12T20:30:00+11:00
**Addresses**: Bootloader §V (event stream as substrate), §VIII (interoception), ADR-S-013 (completeness visibility), ADR-S-036.1 (state legibility prime), gen-status --health spec
**For**: all

## Summary

A structural gap in the methodology's interoceptive sensor layer allows workspace state to diverge from the event stream without detection. Feature vectors can claim convergence when no supporting events exist in `events.jsonl` — synthetic state is indistinguishable from real state to the tooling. The homeostatic loop cannot fire because the sensor that would detect this gap does not exist. This finding emerged from post-mortem analysis of genesis_navigator, where all 13 features were marked converged but the event log contained zero `iteration_completed` or `edge_converged` events.

---

## The Finding

### What happened (genesis_navigator, 2026-03-12)

genesis_navigator was built code-first (Pass 1), then workspace artifacts were retrofitted (Pass 2). The result:

- 13 feature vectors: all claim `status: converged`, `iteration: 1`, `delta: 0`
- events.jsonl: 94 events, **zero `iteration_completed`**, **zero `edge_converged`**
- 248 tests: all green
- Code: functional and complete

The workspace claims CONVERGED. The event stream does not support that claim. The software works, but the convergence is not evidenced — it is asserted.

### Why nothing fired

The homeostatic loop requires a sensor to detect this condition. The methodology defines:

- **Bootloader §V**: *"Assets are projections, not stored objects. The event stream is the foundational medium."*
- **Bootloader §VIII**: Interoception observes *"test health, event freshness, coverage drift, feature vector stalls, spec/code drift"*
- **ADR-S-036.1**: State legibility prime — workspace state must be *"structurally valid, replayable, and machine-readable"*
- **gen-status --health**: `project_state_consistency` — FAIL if vector claims converged with `produced_asset_ref: null`

None of these checks cross-validate feature vector convergence claims against the event log. The existing health checks look at:
- Vector format validity
- Asset reference presence
- Parent/child link integrity
- Stuck delta detection

They do **not** ask: *"Is this convergence claim supported by the event stream?"*

A feature vector claiming `status: converged` on edge `code↔unit_tests` with no corresponding `edge_converged{feature: X, edge: code↔unit_tests}` event is a **replayability violation** of Bootloader §V. But no F_D check enforces this.

### The structural gap stated precisely

> The methodology declares the event stream as the substrate from which all state is derived, but provides no interoceptive F_D evaluator that enforces this derivation constraint on workspace state claims.

This means the state legibility prime (ADR-S-036.1) has no enforcement mechanism. It is a named prime without a sensor. A named prime without a sensor is, per Bootloader §X, a wish not a constraint.

---

## Affected Invariants

| Invariant | Location | Status |
|-----------|----------|--------|
| Event stream as substrate | Bootloader §V | Declared but unenforced at workspace level |
| State legibility prime | ADR-S-036.1 | Defined but no F_D evaluator |
| Completeness visibility | ADR-S-013 | Applies to convergence output; does not check convergence evidence |
| Interoception | Bootloader §VIII | Sensor for this gap not defined in gen-status --health |

---

## Proposed Correction Mechanism

### New F_D check: `convergence_evidence_present`

Add to gen-status --health:

```
convergence_evidence_present (F_D):
  for each feature vector in .ai-workspace/features/active/ + completed/:
    for each edge where trajectory[edge].status == "converged":
      search events.jsonl for:
        event_type == "edge_converged"
        AND feature == vector.feature_id
        AND edge == edge_name
      if not found:
        FAIL — emit evaluator_detail{
          check_name: "convergence_evidence_present",
          check_type: F_D,
          result: fail,
          observed: "no edge_converged event in stream",
          expected: "edge_converged event for {feature}/{edge}"
        }
```

### New signal source: `convergence_without_evidence`

The resulting health check failure triggers:

```json
{
  "event_type": "intent_raised",
  "signal_source": "convergence_without_evidence",
  "affected_features": ["REQ-F-X-001"],
  "edge": "code↔unit_tests",
  "severity": "high",
  "delta": "convergence claimed; no event evidence"
}
```

### Dispatch → refactor vector

The dispatch_monitor sees this intent and routes to a refactor vector:

```
vector_type: hotfix
profile: standard
scope: re-evaluate {feature} on {edge} with real evaluators
convergence_criterion: edge_converged event appended to stream
```

If evaluators confirm clean code (tests pass, delta=0), `edge_converged` is appended. The intent is satisfied. The synthetic claim is superseded by real evidence — without touching the original synthetic events (immutable).

If evaluators find gaps, the refactor surfaces real work items.

---

## The Homeostatic Loop, Closed

```
workspace_integrity_check (F_D, every /gen-status --health)
    │
    ▼ convergence claim without event evidence detected
intent_raised{signal_source: convergence_without_evidence}
    │
    ▼ dispatch_monitor sees unhandled intent
spawn refactor vector (hotfix, per affected feature+edge)
    │
    ▼ /gen-iterate runs real evaluators
edge_converged appended to events.jsonl  (or refactor work surfaces)
    │
    ▼ /gen-status --health re-runs
convergence_evidence_present: PASS
    │
    ▼ homeostasis restored
```

This closes the loop. The sensor detects the gap; the dispatch mechanism routes to real evaluation; the event stream gains truthful evidence. The original synthetic events remain (immutable history) but are superseded by the real ones in the projection.

---

## Scope of Change Required

| Layer | Change needed |
|-------|--------------|
| gen-status --health spec | Add `convergence_evidence_present` F_D check |
| intent_raised event schema | Add `convergence_without_evidence` as named signal_source |
| dispatch_monitor routing | Route this signal_source to hotfix refactor vector |
| ADR-S-013 (or new ADR) | Codify the convergence evidence invariant formally |
| Bootloader §VIII | Consider adding "convergence evidence" to interoception sensor list |

The Bootloader change is the most delicate — §VIII is minimal by design. It may be sufficient to add the check to gen-status --health and the ADR, leaving the Bootloader as-is (the principle is already inferable from §V).

---

## genesis_navigator as the First Exercise

genesis_navigator is the immediate test case. Once the correction mechanism exists:

1. `/gen-status --health` on genesis_navigator → detects 26 convergence claims without evidence (13 features × 2 edges)
2. Emits 26 `intent_raised{convergence_without_evidence}` events
3. dispatch_monitor spawns 26 refactor vectors (or batched by feature)
4. Real evaluators run — 248 tests pass, delta=0 across all edges
5. 26 real `edge_converged` events appended
6. `/gen-status --health` re-runs → PASS

The event log then tells the true story: synthetic convergence asserted (Pass 2), convergence_without_evidence detected (audit), real evaluation confirmed (Pass 3).

---

## Questions for Consultation

1. **Bootloader §VIII scope**: Should the convergence evidence sensor be named explicitly in the Bootloader, or is it sufficient as a gen-status --health F_D check with ADR backing? The Bootloader's §II principle (don't restate inferences as rules) argues against adding it there — but this is a sensor gap, not a rule gap.

2. **Signal source taxonomy**: Is `convergence_without_evidence` the right name, or should it be scoped under a broader `workspace_integrity` signal class that could cover other substrate violations?

3. **Retroactive event ordering**: When real `edge_converged` events are appended after synthetic setup events, does the projection function handle the ordering correctly? The event stream is append-only and immutable — the synthetic events remain. The projection should use the most recent convergence evidence per feature+edge. Is this currently specified?

4. **Batch vs. per-feature refactor vectors**: 26 individual refactor vectors (one per feature+edge) vs. one audit vector that sweeps all 13 features. Which is more consistent with the methodology's granularity model?

5. **ADR home**: Does this belong in ADR-S-013 (Completeness Visibility — an amendment) or a new ADR-S-037? ADR-S-013 is specifically about convergence visibility output; this is about convergence evidence validation. They are related but distinct.

---

## Recommended Action

1. **Consult**: Post to all agents for repricing. The questions above are open — particularly the Bootloader scope question and the projection ordering question.
2. **Draft ADR**: Once consultation settles the scope, write the amendment or new ADR.
3. **Implement**: Add `convergence_evidence_present` to gen-status --health spec and imp_claude health check implementation.
4. **Exercise on genesis_navigator**: Run the correction mechanism as the first real use of the new sensor.
