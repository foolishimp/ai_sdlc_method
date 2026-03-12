# ADR-S-039: Bug Triage and Post-Mortem Escalation

**Status**: Ratified
**Date**: 2026-03-13
**Deciders**: Human (Jim)
**Reference**: Bootloader §XX

---

## Context

During active development, bugs are discovered and fixed constantly. The methodology as defined
required formal feature vectors even for trivial coding mistakes, creating friction that discourages
logging and makes the methodology feel like overhead rather than infrastructure.

Two distinct bug categories exist with fundamentally different handling needs:

1. **Coding errors** — typos, off-by-one, wrong variable, missing null check. Cause is clear,
   fix is local, no design information is contained. These are noise during development.

2. **Design-revealing bugs** — symptoms that indicate a structural gap: a wrong abstraction,
   a missing contract, an unanticipated interaction. These carry design information and warrant
   formal investigation.

The key insight: **you cannot reliably distinguish these categories at fix time**. The bug looks
like a coding error; the design flaw only becomes visible in post-mortem when patterns emerge
across multiple bugs, or when the fix requires touching more than expected.

Therefore the methodology needs two separated phases:
- **Fix + log** (immediate, lightweight, always)
- **Triage** (deferred, batch, on demand)

---

## Decision

### Phase 1: Fix and Log (reflex — no ceremony)

When a bug is found, fix it directly. No feature vector is created. No formal iterate() cycle
is initiated. Append one `bug_fixed` event to `events.jsonl`:

```json
{
  "event_type": "bug_fixed",
  "timestamp": "{ISO 8601}",
  "project": "{project_name}",
  "data": {
    "description": "{one line: what was wrong and what was changed}",
    "file": "{primary file touched}",
    "root_cause": "coding_error | design_flaw | unknown"
  }
}
```

`root_cause` is a **preliminary classification at fix time**. It is provisional — post-mortem
may reclassify it. The three values:

| Value | Meaning | Post-mortem action |
|-------|---------|-------------------|
| `coding_error` | Typo, wrong variable, obvious local mistake | Discard — no further action |
| `design_flaw` | Fix required touching interfaces, contracts, or multiple components | Escalate → `intent_raised` |
| `unknown` | Cause unclear at fix time | Investigate in post-mortem before discarding |

### Phase 2: Post-Mortem Triage (conscious — on demand)

Post-mortem is not a scheduled ceremony. It runs when:
- Preparing a release
- A cluster of related bugs appears
- `/gen-status --health` surfaces a pattern
- The human decides to review

For each `bug_fixed` event with `root_cause: design_flaw` or `root_cause: unknown`:

1. **Design flaw confirmed** → emit `intent_raised` with `signal_source: bug_post_mortem`.
   The intent enters the normal homeostatic loop. Scope is determined by the intent, not the bug.
2. **Unknown resolved to coding error** → discard. Update the event if possible; otherwise leave as-is.
3. **Unknown resolved to design flaw** → same as (1).
4. **Pattern detected** (multiple `coding_error` bugs in same area) → may indicate a missing
   abstraction or unclear contract. Emit `intent_raised` for investigation even if individual
   bugs were coding errors.

### What is NOT required

- A feature vector for the bug fix itself
- An iterate() cycle for the fix
- Human gate approval before fixing
- REQ key traceability for the fix commit

The only required artifact is the `bug_fixed` event. Everything else is optional and
emerges from post-mortem if warranted.

---

## Rationale

### Why log at all?

The event stream is the post-mortem substrate. Without `bug_fixed` events, patterns are
invisible — you cannot detect "five bugs in the auth module this week" or "every bug in
the parser required touching the AST interface." The log is cheap; the insight is not.

### Why defer triage?

Classification at fix time is unreliable. The developer is in fix mode, not analysis mode.
Post-mortem has the benefit of distance, pattern visibility across multiple events, and
the ability to correlate with other signals (gap analysis, telemetry anomalies).

### Why no ceremony for coding errors?

Coding errors during active development are a natural byproduct of construction. The
methodology's formal machinery (feature vectors, evaluators, convergence events) exists
to manage design decisions and ensure quality at architectural boundaries. Applying it to
a typo fix violates the principle that overhead should be proportional to consequence.

### Relationship to the gradient

A coding error produces delta → 0 locally. The fix restores the intended state. No
design information is generated; no gradient remains. Post-mortem confirms this.

A design flaw produces a **persistent delta** — the fix patches the symptom but the
underlying constraint violation remains. Post-mortem detects this and generates work
(intent → vector → iterate). The gradient is non-zero; the methodology engages.

---

## Consequences

### Positive
- Bugs are logged without friction — low barrier means higher compliance
- Post-mortem has a queryable event stream rather than relying on memory or git blame
- Design flaws surface through pattern analysis, not just individual bug reports
- The methodology doesn't impose overhead during active development iteration

### Negative
- `root_cause` at fix time is provisional — post-mortem adds a second pass
- `unknown` events require follow-up; leaving them unreviewed degrades signal quality
- Coding errors are not traced to REQ keys — traceability gap at the fix level

### Mitigations
- `/gen-status --health` can surface unreviewed `unknown` events older than N days
- Post-mortem can be triggered by release gate (no unreviewed `unknown` events before ship)

---

## Event Schema

```json
{
  "event_type": "bug_fixed",
  "timestamp": "2026-03-13T10:00:00Z",
  "project": "genesis_manager",
  "data": {
    "description": "TraceabilityTable missing null check on reqKey caused crash when API returns partial data",
    "file": "src/features/evidence/TraceabilityTable.tsx",
    "root_cause": "coding_error"
  }
}
```

Post-mortem escalation event (if warranted):

```json
{
  "event_type": "intent_raised",
  "timestamp": "2026-03-13T14:00:00Z",
  "project": "genesis_manager",
  "data": {
    "intent_id": "INT-GM-004",
    "trigger": "bug_post_mortem: 3 null-safety bugs in evidence layer suggest missing defensive contract",
    "signal_source": "bug_post_mortem",
    "severity": "medium",
    "affected_req_keys": ["REQ-F-EVI-002"]
  }
}
```

---

*Traces to: Bootloader §XX (Bug Triage and Post-Mortem Escalation)*
*Supersedes: none (new calibration clause)*
*Related: ADR-S-033 (Genesis-enabled systems), ADR-S-039 (this)*
