# Postmortem Template — AI SDLC Asset Graph Model

**Version**: 2.0
**Reference**: GENESIS_BOOTLOADER.md §VI (The Gradient), §VIII (Homeostasis), REQ-TOOL-016

---

## What This Is

The workspace state is an asset. Running gap analysis or a postmortem is
`iterate()` on that asset — structurally identical to any other graph edge:

```
iterate(
  Asset<workspace_state>,
  Context[spec, constraints, events, feature_vectors],
  Evaluators[configured per analysis type]
) → delta → intent_raised → iterate() back
```

Gap analysis and postmortem are two evaluator configurations — one reads
forward (what is missing now), one reads backward (what happened and why).
Both operate on the same asset. Both produce the same output when delta > 0:
`intent_raised` → `feature_proposal` → feature vector → `iterate()`.

The document sections below are the human-readable rendering of that output.
The event emission in §4 is the machine-actionable signal. Both are required.
A postmortem that produces only a document has not closed the loop.

---

## Template

```
# [PROJECT_NAME] — Postmortem [vVERSION]

**Date**: [ISO 8601]
**Method version**: [genesis method version]
**Profile**: [standard | full | poc | spike | hotfix]
**Asset**: workspace state at [snapshot timestamp]
**Events**: [N] in events.jsonl | Feature vectors: [N] | Reconstruction: complete / partial
```

---

### 1. Asset State — Workspace Discovery

*Read the workspace asset once. §2, §3, and §4 all derive from this section.*

#### 1a. Event Stream

| # | event_type | feature | edge | timestamp |
|---|-----------|---------|------|-----------|
| … | … | | | |

**Counts**:

| event_type | count |
|-----------|-------|
| edge_started | |
| iteration_completed | |
| edge_converged | |
| intent_raised | |
| feature_proposal | |
| release_created | |

**Delta flags** (these are evaluator failures — each will emit `intent_raised` in §4):
- [ ] Features with no `edge_started` / `iteration_completed` / `edge_converged` events: [list]
- [ ] Edges with `edge_started` but no `iteration_completed`: [list]
- [ ] Session gaps > 30 min with no `session_gap` event: [list]

#### 1b. Feature Vector State

| Feature | Req | Design | Code | Tests | UAT | Status |
|---------|-----|--------|------|-------|-----|--------|
| REQ-F-* | ✓/○ | ✓/○ | ✓/○ | ✓/○ | ✓/○ | converged / partial |

Dependency DAG: [topological order]

#### 1c. REQ Coverage

| Domain | Spec | Code | Tests | Telemetry | Delta |
|--------|------|------|-------|-----------|-------|
| [DOM] | N | N | N | N | 0 / +N missing |
| **Total** | N | N% | N% | N% | |

Orphan keys (in code/tests, not in spec): [list or NONE]
Synthetic keys (created during design): [list or NONE]

#### 1d. Constraint Surface

| Dimension | Status | Binding |
|-----------|--------|---------|
| ecosystem_compatibility | RESOLVED / UNRESOLVED | |
| deployment_target | | |
| security_model | | |
| build_system | | |

---

### 2. Evaluator Results — Forward (Gap Analysis)

*What is the delta between the current workspace state and the spec?*
*Each failing check below becomes an `intent_raised` event in §4.*

| Evaluator | Type | Delta | Severity |
|-----------|------|-------|---------|
| req_tags_in_code | F_D | 0 / N untagged files | high |
| req_tags_in_tests | F_D | 0 / N untagged files | high |
| all_req_keys_have_tests | F_D | 0 / N keys without tests | high |
| telemetry_coverage | F_D | advisory / N keys untagged | medium |
| event_log_complete | F_D | 0 / N features missing events | high |
| all_profile_edges_traversed | F_D | 0 / N edges not traversed | high |
| per_feature_uat | F_D | 0 / N features UAT pending | medium |
| session_continuity | F_D | 0 / N unrecorded gaps | medium |

**Total delta**: [N failing evaluators]
**Convergence**: [PASS — workspace asset converged] / [FAIL — delta > 0, iterate() required]

---

### 3. Evaluator Results — Backward (Postmortem)

*What happened? Temporal reconstruction from the event stream.*
*Root causes are evaluator findings on the process, not the code.*

#### 3a. Project Profile

| | |
|--|--|
| **Project** | |
| **Start** | event N — project_initialized — [timestamp] |
| **Release** | event N — release_created — [timestamp] |
| **Elapsed** | [wall clock, excluding session gaps] |
| **Sessions** | N (gaps: [describe]) |
| **Build mode** | manual / engine-assisted / autonomous |

#### 3b. Edge Performance

| Edge | Feature | Iterations | Duration | Evaluators | Result |
|------|---------|-----------|---------|-----------|--------|
| requirements→feature_decomp | all | 1 | 5m | N/N | CONVERGED |
| … | | | | | |

Re-iterations (> 1): [list — each is a delta that forced iterate() back, as designed]
Unrecorded edges (feature vector says converged, no events): [list — evaluator failure]

#### 3c. Root Causes

*Map each finding to its evaluator category. These feed §4.*

| # | Observation | Evaluator category | Severity | Forces iterate() on |
|---|------------|-------------------|---------|-------------------|
| 1 | [what] | F_P gap / event emission / false convergence / spec gap / F_H blocked | high/med/low | [what edge/feature] |

Evaluator categories:

| Category | Meaning |
|----------|---------|
| F_P gap | Engine can evaluate but not construct autonomously — human latency fills the gap |
| Event emission | `iterate()` ran but required events were not emitted |
| False convergence | `delta=0` via skips, not via passing evaluators |
| Spec gap | Underspecification surfaced during construction |
| F_H blocked | Human gate not cleared — edge cannot advance |
| Session discontinuity | Context not reconstructable across session boundary |

#### 3d. Methodology Version Delta

| Aspect | Prior run | This run | Signal |
|--------|-----------|----------|--------|
| Method version | | | |
| Events emitted | N | N | ±N |
| Edges re-iterated | N | N | ±N |
| Coverage | N% | N% | ±N% |

---

### 4. Event Emission — Loop Closure

*Mandatory. The document sections above are the rendering. This section is the signal.*
*Execute after §2 and §3. One `intent_raised` per failing evaluator or root cause.*

**4a. Emit `workspace_analysed`**:

```json
{
  "event_type": "workspace_analysed",
  "timestamp": "{ISO 8601}",
  "project": "{project name}",
  "data": {
    "analysis_type": "gap_analysis|postmortem|both",
    "snapshot_timestamp": "{ISO 8601}",
    "total_delta": "{N failing evaluators}",
    "evaluator_results": [
      {"name": "{evaluator}", "type": "F_D|F_P|F_H", "result": "pass|fail", "delta": "{N}"}
    ]
  }
}
```

**4b. For each failing evaluator or root cause — emit `intent_raised`**:

```json
{
  "event_type": "intent_raised",
  "timestamp": "{ISO 8601}",
  "project": "{project name}",
  "data": {
    "intent_id": "INT-{SEQ}",
    "trigger": "{evaluator name} — {what it found}",
    "delta": "{specific missing artifact or failure}",
    "signal_source": "workspace_analysis",
    "vector_type": "feature|hotfix",
    "severity": "high|medium|low",
    "affected_features": ["{REQ-F-*}"]
  }
}
```

**4c. For each `intent_raised` — emit `feature_proposal` and write `.ai-workspace/reviews/pending/PROP-{SEQ}.yml`**:

```json
{
  "event_type": "feature_proposal",
  "timestamp": "{ISO 8601}",
  "project": "{project name}",
  "data": {
    "proposal_id": "PROP-{SEQ}",
    "intent_id": "INT-{SEQ}",
    "title": "{short description}",
    "description": "{what iterate() must fix}",
    "severity": "high|medium|low",
    "suggested_profile": "standard|hotfix|minimal",
    "status": "draft",
    "source": "workspace_analysis"
  }
}
```

**4d. Loop closure summary**:

```
═══ LOOP CLOSURE ═══
Total delta:    {N} failing evaluators
intent_raised:  {N} events emitted
proposals:      {N} in review queue

Next: /gen-review-proposal → approve → /gen-start (routes to iterate())
Status: CLOSED / PARTIAL / OPEN
═════════════════════
```

---

### 5. Appendix

#### 5a. Event Log Reference

[path to events.jsonl or inline if short]

#### 5b. Deferred Scope

| Item | Reason | Target |
|------|--------|--------|
| | | |
