# Design: INTRO-008 Wiring — Health Pass Detection + Explicit Repair
<!-- Implements: REQ-SENSE-001, REQ-UX-005, REQ-EVENT-002 -->
<!-- Feature vector: REQ-F-SENSE-002 -->
<!-- Edge: requirements→design — iteration 3 (revised after Codex ADR-S-037 review + Jim functional principle) -->

**Version**: 3.0.0
**Date**: 2026-03-13
**Status**: Draft — awaiting human approval
**Parent**: REQ-F-SENSE-001 | **Spawned by**: INT-023

**Changes from v2.0**:
- Removed EDGE_RUNNER from the repair path entirely (type mismatch: EDGE_RUNNER domain is `(feature, edge) → convergence`; repair domain is `(gap) → event_appended`)
- Removed `affected_edges` routing field (no dispatch means no dispatch hint is justified)
- Removed `gap_type` / `manifestation` structured triple from signal payload (no material routing distinction — total-function principle)
- Repair semantics repriced: validity requires explicit provenance, not gap + boolean approval
- gen-status --health stays read-oriented by default; repair behind explicit `--repair` affordance
- ADR-S-037 scope minimized to match Codex review findings

---

## 1. Architecture Overview

```
Detection path (every health pass):
  gen-start Step 10 ──► sense_convergence_evidence() ──► breached?
  gen-status --health ─────────────────────────────────► breached?
                                                              │
                              ┌───────────────────────────────┘
                              ▼
                    emit interoceptive_signal
                    {family: gap, contract: projection_authority}
                              │
                    affect triage (existing pipeline)
                              │
                    intent_raised {signal_source: gap}
                    (observability preserved — no silent health gaps)

Repair path (explicit only):
  gen-status --repair ──► display gaps to human
                          F_H gate: confirm retroactive closure?
                          on approval: repair_convergence_evidence(gaps, provenance)
                          ──► emit edge_converged{emission: retroactive}
```

**Design axiom (Jim's total-function principle)**: Do not add a new type unless there is a materially distinct computation behind it. The interoceptive_signal path already carries projection_authority gaps. The repair path is a separate function with a separate invocation surface — not a new routing branch.

**Type distinction (Codex + Jim)**:
- EDGE_RUNNER domain: `(feature, edge) → convergence` — new asset convergence sought
- Repair domain: `(gap) → event_appended` — recording that existing convergence happened
- These are different types. Routing repair through EDGE_RUNNER is a type error.

---

## 2. Component Design

### Component A: INTRO-008 in gen-start Step 10 (LLM command spec update)

**Implements**: REQ-SENSE-001, REQ-UX-005

**Why here, not dispatch_monitor**: `dispatch_monitor.check_and_dispatch()` is an event-log append watcher. Injecting health monitors there creates a self-exciting loop: INTRO-008 emits `interoceptive_signal` → which is a new event → which triggers `check_and_dispatch()` again. Health checks belong at explicit invocation boundaries with their own cadence.

**Change to gen-start.md Step 10 table**:

| Issue | Detection | Recovery |
|-------|-----------|----------|
| Convergence without stream evidence | `sense_convergence_evidence()` breached — YAML claims converged, no terminal event in stream (INTRO-008) | Emit `interoceptive_signal{family: gap, contract: projection_authority}` → affect triage → `intent_raised{signal_source: gap}`. Repair via explicit `gen-status --repair`. |

**gen-start Step 10 Python pseudocode** (LLM executes this):
```python
# Step 10: Recovery checks — runs BEFORE state detection
result = sense_convergence_evidence(workspace_root, events_path)
if result.breached:
    emit_event({
        "event_type": "interoceptive_signal",
        "data": {
            "family": "gap",
            "contract": "projection_authority",
            "scope": [
                {"feature": gap.feature_id, "edge": gap.edge}
                for gap in result.data.gaps
            ],
            "severity": "critical",
            "monitor_id": "INTRO-008",
        }
    })
    # affect triage + intent_raised happen via existing pipeline
    # no repair here — detection only
```

---

### Component B: INTRO-008 in gen-status `--health` emitter

**Implements**: REQ-SENSE-001

Add INTRO-008 to the `health_checked` event emission in `gen-status --health`. The health check is detection-only — it reports gaps, does not repair them.

**Change**: after existing health checks, add:
```python
result = sense_convergence_evidence(workspace_root, events_path)
if result.breached:
    failed_checks.append("convergence_evidence_present")
    # surface gap details in health output — no mutation
    for gap in result.data.gaps:
        print(f"  GAP: {gap.feature_id} / {gap.edge} — YAML converged, no terminal event")
    print("  Repair: gen-status --repair (explicit affordance)")
```

The `health_checked` event's `failed_checks` list gains `"convergence_evidence_present"` when INTRO-008 fires.

**gen-status --health does NOT mutate by default.** Displaying gaps is read-only. Repair requires `--repair`.

---

### Component C: Repair affordance (`gen-status --repair` or `workspace_repair.py`)

**Implements**: REQ-SENSE-001, REQ-EVENT-002

**Repair function signature**:
```python
def repair_convergence_evidence(
    gaps: list[EvidenceGap],
    provenance: RepairProvenance,
) -> list[EdgeConvergedEvent]:
    """
    Emit retroactive edge_converged events for approved gaps.

    The validity of the repair is established by the provenance record,
    not by the existence of a gap plus a boolean. Provenance must carry:
    - executor: who confirmed the convergence (human ID or audit trail)
    - basis: why the convergence was valid (review reference, evaluation record)
    - confirmed_at: when the confirmation was made

    Returns the list of events emitted (for observability).
    """
```

**Invocation surface** (`gen-status --repair`):
```
gen-status --repair

PROJECTION AUTHORITY REPAIR — {N} gap(s) detected by INTRO-008

  Gap 1: REQ-F-FOO-001 / design→code
    Claim: workspace YAML status=converged
    Evidence: no edge_converged terminal event in stream
    Action if approved: append edge_converged{emission: retroactive, executor: human}

  Gap 2: REQ-F-BAR-001 / code↔unit_tests
    (same pattern)

  These gaps predate the INTRO-008 enforcement check.
  Retroactive closure records that convergence occurred; it does not re-validate the work.
  The validity of each repair rests on the accuracy of your confirmation.

  Confirm repairs? [y/n/selective]
  (y = approve all, n = reject all, selective = approve per gap)
```

**Per-gap provenance record**:
```json
{
    "event_type": "edge_converged",
    "feature": "REQ-F-FOO-001",
    "edge": "design→code",
    "executor": "human",
    "emission": "retroactive",
    "data": {
        "convergence_type": "retroactive_repair",
        "confirmed_by": "{human_id_or_session}",
        "confirmed_at": "{ISO 8601}",
        "basis": "human_confirmation_repair",
        "monitor_id": "INTRO-008",
        "repaired_at": "{ISO 8601}"
    }
}
```

**What makes the repair valid**: the human's explicit confirmation and the accuracy of their attestation — not the gap detection itself plus a boolean. The function constructs the provenance record; the human's confirmation is the validity ground.

---

### Component D: Signal classification (fd_classify.py)

**Implements**: REQ-SENSE-001

`interoceptive_signal` with `family: gap` is already a known signal type in the existing sensory pipeline. No new top-level entry needed. The routing is:

```python
# No new entry required — existing gap signal family handles this
# affect triage routes {family: gap, contract: projection_authority} → intent_raised

# fd_classify.py: confirm gap is in KNOWN_SIGNAL_SOURCES if used as signal_source
# The intent_raised event uses signal_source: "gap" — already present
```

**No new `gap_type` field, no new `manifestation` field, no new dispatch table**. The contract field (`projection_authority`) carries sufficient diagnostic information for human-readable observability. Adding structured sub-fields would require a materially distinct computation in downstream routing — which does not exist here.

---

## 3. Data Model

Minimal extensions — no new types:

| Structure | Change |
|-----------|--------|
| `interoceptive_signal` data | Add `scope` field: list of `{feature, edge}` dicts — for human-readable output only |
| `edge_converged` data | Add optional `emission: retroactive`, `confirmed_by`, `confirmed_at`, `basis`, `monitor_id` fields |
| `health_checked` data | `failed_checks` gains `"convergence_evidence_present"` entry |

No changes to:
- `intent_raised` — uses existing `signal_source: gap` field
- `DispatchTarget` — not used in repair path
- `dispatch_monitor.py` — no injection point here
- `edge_runner.py` — not called in repair path
- `intent_observer.py` — not called in repair path

```
interoceptive_signal
  family: "gap"
  contract: "projection_authority"
  scope: [{feature, edge}, ...]   ← list of affected gaps (diagnostic, not routing)
  severity: "critical"
  monitor_id: "INTRO-008"

intent_raised (from affect triage)
  signal_source: "gap"            ← no new fields; gap family already handled
  affected_features: [...]        ← derived from scope

edge_converged (repair output)
  emission: "retroactive"
  executor: "human"
  confirmed_by: ...               ← provenance
  basis: "human_confirmation_repair"
```

---

## 4. ADR Index

| ADR | Applicable decision |
|-----|-------------------|
| ADR-S-037 (Projection Authority) — minimized | Enforcement contract: projection_authority rule + INTRO-008 as enforcing sensor + retroactive closure legibility requirement. Does NOT prescribe repair workflow. |
| ADR-S-036.1 (Prime Convergence) | Observability and state legibility are invariant primes; ADR-S-037 enforces an existing prime manifestation only |
| ADR-S-031 (Observer/Relay/Saga) | Health pass is thin emitter — emits signals, does not orchestrate repair |
| ADR-S-026 (Named Compositions) | No new composition needed; existing gap signal handles this |

**ADR-S-037 minimization** (per Codex review 20260313T000830):

The minimum spec contract for ADR-S-037 is:
1. A workspace claim MUST NOT assert stronger convergence than the event substrate supports.
2. There MUST be a deterministic check that detects violations (INTRO-008).
3. Retroactive closure is valid only when explicitly attributable and legible.

The ADR should NOT prescribe repair workflow, routing fields, or command choreography. Those are tenant implementation choices.

---

## 5. Traceability Matrix

| Component | REQ Keys |
|-----------|----------|
| gen-start Step 10 update | REQ-SENSE-001, REQ-UX-005 |
| gen-status --health update | REQ-SENSE-001 |
| gen-status --repair affordance | REQ-SENSE-001, REQ-EVENT-002 |
| `repair_convergence_evidence()` | REQ-EVENT-002 |

---

## 6. Package/Module Structure

```
imp_claude/
  code/genesis/
    fd_sense.py              ← EXISTING: sense_convergence_evidence() — no change
    workspace_integrity.py   ← EXISTING: INTRO-008 check — no change
    workspace_repair.py      ← NEW: repair_convergence_evidence() — separate from detection
  code/.claude-plugin/plugins/genesis/commands/
    gen-start.md             ← UPDATE: Step 10 table — INTRO-008 row (detection only)
    gen-status.md            ← UPDATE: --health adds INTRO-008; --repair affordance added
  tests/
    test_intro008_wiring.py  ← NEW (Validates: REQ-SENSE-001, REQ-UX-005, REQ-EVENT-002)
```

No changes to:
- `dispatch_monitor.py`
- `edge_runner.py`
- `intent_observer.py`
- `fd_classify.py` (gap signal_source already present)

---

## 7. Source Analysis Findings (v3)

| Finding | Classification | Disposition |
|---------|---------------|-------------|
| dispatch_monitor self-exciting loop (v1 issue) | SOURCE_GAP | resolved_by_design — injection moved to explicit health boundary |
| Type proliferation via `gap_type` / `manifestation` (v2 issue) | SOURCE_GAP | resolved_by_design — removed; no material routing distinction |
| EDGE_RUNNER as repair path (v2 issue) | SOURCE_GAP | resolved_by_design — type mismatch resolved; repair is separate domain |
| `affected_edges` routing hint (v2 issue) | SOURCE_GAP | resolved_by_design — removed; no dispatch path means no dispatch hint |
| Repair validity via gap + boolean (v2 issue) | SOURCE_GAP | resolved_by_design — provenance record carries explicit attestation |
| ADR-S-037 overreach (Codex review) | SOURCE_GAP | resolved_by_design — minimized to enforcement contract only |

---

## 8. Process Gap Analysis (Inward)

| Gap | Type | Action |
|-----|------|--------|
| `repair_convergence_evidence()` not yet implemented | EVALUATOR_MISSING | Fixed in this feature's code edge |
| `workspace_repair.py` module does not exist yet | EVALUATOR_MISSING | New module in code edge |
| gen-status --repair flag not yet in gen-status.md | EVALUATOR_MISSING | gen-status.md update in code edge |
| gen-start Step 10 table does not yet include INTRO-008 row | EVALUATOR_MISSING | gen-start.md update in code edge |
| No affect triage implementation yet | EVALUATOR_MISSING | Tests will mock triage output; full triage is REQ-F-SENSE-001 scope |
