# REVIEW: REQ-F-SENSE-002 — INTRO-008 Wiring Design (v3 proposal)

**Author**: claude
**Date**: 2026-03-13T13:00:36Z
**Addresses**: REQ-F-SENSE-002, INT-023, ADR-S-037, workspace_integrity.py, fd_sense.py
**For**: all

---

## Summary

Design for wiring INTRO-008 (`convergence_evidence_present`) into the health pass and providing a repair path for convergence claims without stream evidence. This is the third iteration — v1 and v2 were rejected on injection-point and type-proliferation grounds. This post records the v3 direction for review before code is written.

---

## Design Evolution

**v1 (rejected)**: inject `run_health_monitors()` into `dispatch_monitor.check_and_dispatch()` on every event-log append. Problem: self-exciting loop — INTRO-008 emits `interoceptive_signal`, which is a new event, which triggers `check_and_dispatch()` again.

**v2 (rejected)**: move injection to explicit health boundary (correct), but introduce `gap_type: projection_authority` and `manifestation: missing_convergence_evidence` as new routing fields on `intent_raised`, plus `affected_edges` hint in `intent_observer.py` and `_handle_projection_authority_gap()` in `edge_runner.py`. Problem: adds routing entropy without a material computational distinction. Jim's principle: only add a new type when it changes routing, governance, and telemetry class in a fundamentally different way.

**v3 (proposed)**:

---

## v3 Functional Decomposition

The key type-signature distinction:

- **EDGE_RUNNER domain**: `(feature, edge) → convergence` — traverse a graph edge toward a new stable asset
- **Retroactive repair domain**: `(gap: EvidenceGap) → event_appended` — record that a stable asset already exists

These have different type signatures. Routing retroactive repair through EDGE_RUNNER is a type error. The repair does not belong in the dispatch loop.

**The composition**:

```
sense_convergence_evidence(workspace) → SenseResult
    ↓ if breached
emit interoceptive_signal per gap          ← observable, in event log
    ↓ affect triage (existing mechanism)
intent_raised → proposals queue            ← visible in gen-status signals
    ↓ human acts on health report
repair_convergence_evidence(gaps, confirmed: [bool]) → [EdgeConvergedEvent]
    ↓
edge_converged{emission: retroactive} per confirmed gap
```

The repair function is a pure function in `workspace_integrity.py` — no routing side effects, no EDGE_RUNNER, no new dispatch path.

**What is preserved**:
- `interoceptive_signal` → `intent_raised` → proposals queue path intact (homeostatic observability)
- `dispatch_monitor` untouched (pure consumer)
- `edge_runner` untouched
- `intent_observer` untouched

**What changes**:
1. `gen-status --health`: add INTRO-008 call; if breached, surface gaps + F_H gate with inline repair offer (batched, per-gap dispositions)
2. `gen-start.md` Step 10: add INTRO-008 call + same inline offer
3. `workspace_integrity.py`: add `repair_convergence_evidence(gaps, confirmed) → list[dict]` — pure function, emits `edge_converged{emission: retroactive}` per approved gap

**No new routing fields. No mutation of dispatch pipeline. No new top-level signal types.**

---

## Retroactive repair event schema

```json
{
    "event_type": "edge_converged",
    "timestamp": "{ISO 8601}",
    "project": "{project}",
    "feature": "{feature_id}",
    "edge": "{edge}",
    "executor": "human",
    "emission": "retroactive",
    "data": {
        "convergence_type": "retroactive_repair",
        "intent_id": "{INT-023 or related}",
        "disposition": "approved",
        "repaired_at": "{ISO 8601}"
    }
}
```

Uses existing `executor` and `emission` fields (REQ-EVENT-005) — no schema extension needed.

---

## F_H Gate (batched, per-gap dispositions)

```
CONVERGENCE EVIDENCE GAPS — INTRO-008 detected N gap(s):

  1. REQ-F-FOO-001 / design→code
     YAML: status=converged
     Stream: no edge_converged terminal event

  2. REQ-F-BAR-001 / code↔unit_tests
     YAML: status=converged
     Stream: no edge_converged terminal event

  These edges converged before ADR-S-037 was in effect.
  Retroactive repair records the evidence — it does not re-validate the work.

  [y] approve all   [n] reject all   [s] selective
```

Per-gap `edge_converged{emission: retroactive}` emitted only for approved entries.

---

## Questions for review

1. **Is `repair_convergence_evidence()` the right place** for the repair function, or should it live in a separate `workspace_repair.py` to keep `workspace_integrity.py` read-only (pure sensing)?

2. **Should `interoceptive_signal` carry the full `affected_edges` list** (for traceability) even if dispatch routing doesn't use it? Or is that adding fields that imply routing intent they don't have?

3. **Does the inline repair offer in gen-status --health feel right** given gen-status is supposed to be a read operation? Should repair live behind a separate command (e.g., `gen-status --health --repair`)?

4. **Is the affect triage path** (`interoceptive_signal` → `intent_raised` → proposals queue) important to preserve for this gap, or is the inline repair path sufficient observability?

---

## Files in scope

```
imp_claude/
  code/genesis/
    workspace_integrity.py   ← ADD: repair_convergence_evidence()
  code/.claude-plugin/plugins/genesis/commands/
    gen-start.md             ← UPDATE: Step 10 table
    gen-status.md            ← UPDATE: --health section
  tests/
    test_intro008_wiring.py  ← NEW (Validates: REQ-SENSE-001, REQ-UX-005, REQ-EVENT-002)
```

No changes to: `dispatch_monitor.py`, `intent_observer.py`, `edge_runner.py`, `fd_classify.py`.

---

## Design document

`imp_claude/design/features/REQ-F-SENSE-002-intro008-wiring-design.md` — to be updated to v3 on review approval.
