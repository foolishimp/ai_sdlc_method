# Postmortem Template — AI SDLC Asset Graph Model

**Version**: 1.1
**Reference**: AI_SDLC_ASSET_GRAPH_MODEL.md §VI (The Gradient), GENESIS_BOOTLOADER.md §VIII (Homeostasis), REQ-TOOL-016

---

## Design Principle: Shared Discovery + Homeostatic Loop Closure

Gap analysis and postmortem are two projections of the same discovery pass. But they are not just reports — they are **sensors**. Findings that remain as document annotations without corresponding `intent_raised` events have not completed the loop.

```
Discovery Layer (run once)
  ├── Event stream            → Temporal reconstruction (postmortem)
  ├── Feature vector state    → Edge performance / convergence (both)
  ├── Coverage map (L1/2/3)  → Code coverage gaps  → intent_raised
  ├── Methodology trace (L4) → Process gaps        → intent_raised
  └── Constraint surface      → Context validation (both)

         ┌─────────────────┐
Discovery ┤                 ├── Gap Analysis   (forward: what is missing now)
         │   same data     ├── Postmortem     (backward: what happened and why)
         └─────────────────┘── Event emission (§6 — closes the homeostatic loop)
```

**The homeostatic invariant**: failure per iteration is acceptable. The purpose of the loop is to detect failures, convert them to intent vectors, and force iterate() back. A postmortem that finds root causes but emits no `intent_raised` events has produced a document. A postmortem that emits `intent_raised` events for each finding is a sensor — it forces the correction.

**Layer 4 — Methodology Compliance Gaps** (extends /gen-gaps Layers 1–3):

| Layer 4 check | Failure signal | Severity |
|---|---|---|
| All code edges have `edge_started` + `iteration_completed` + `edge_converged` | Feature built outside `/gen-iterate` path | High |
| All shared edges have `iteration_completed` (even 1-pass convergences) | Iteration history invisible to monitor | Medium |
| All edges in active profile traversed before release | Partial graph traversal at release | High |
| Session gaps > 30 min have `session_gap` event | Session discontinuity unrecorded | Medium |
| UAT edges traversed per-feature, not just aggregate | Per-feature acceptance not verified | Medium |

**When to use**:
- `/gen-gaps` mid-development → §1 Discovery + §2 Gap Analysis + §6 Event Emission (forward)
- `/gen-postmortem` at release or retrospective → all sections + §6 Event Emission (both)
- Discovery is run once; gap analysis and postmortem are renderers over the same output

---

## Template

```
# [PROJECT_NAME] — Postmortem [vVERSION]

**Date**: [ISO 8601]
**Method version**: [genesis method version]
**Profile**: [standard | full | poc | spike | hotfix]
**Reconstruction source**: events.jsonl ([N] events), [N] feature vectors,
  project_constraints.yml, graph_topology.yml, release manifest
```

---

### 1. Discovery

*This section is the shared substrate. It feeds both §2 (Gap Analysis) and §3 (Postmortem). Run once — project both views from it.*

#### 1a. Event Stream Summary

| # | event_type | feature | edge | timestamp | Notes |
|---|-----------|---------|------|-----------|-------|
| 1 | project_initialized | | | | |
| … | … | | | | |

**Event counts by type**:

| event_type | count | Notes |
|-----------|-------|-------|
| edge_started | | |
| iteration_completed | | |
| edge_converged | | |
| intent_raised | | |
| feature_proposal | | |
| gaps_validated | | |
| release_created | | |

**Completeness flags**:
- [ ] Every `edge_started` has a matching `edge_converged`
- [ ] Every `edge_started` has at least one `iteration_completed`
- [ ] All feature code edges have events (not just feature vector state)
- [ ] Session breaks are detectable from timestamp gaps

#### 1b. Feature Vector State

| Feature | Requirements | Design | Code | Unit Tests | UAT Tests | Overall |
|---------|-------------|--------|------|-----------|----------|---------|
| REQ-F-* | converged / pending | | | | | |

**Dependency DAG**: [draw or describe topological order]

#### 1c. Coverage Map

| REQ Domain | Spec Keys | In Code | In Tests | In Telemetry | Status |
|-----------|----------|---------|---------|-------------|--------|
| [DOMAIN]  | N | N | N | N | COMPLETE / PARTIAL / MISSING |
| **TOTAL** | N | N (%) | N (%) | N (%) | |

**Orphan keys** (tagged in code/tests but not in spec): [list or NONE]
**Synthetic keys** (created during design, not in original spec): [list or NONE]

#### 1d. Constraint Surface

| Dimension | Status | Binding |
|-----------|--------|---------|
| ecosystem_compatibility | RESOLVED / UNRESOLVED | |
| deployment_target | | |
| security_model | | |
| build_system | | |
| [advisory dimensions] | ADVISORY | |

---

### 2. Gap Analysis

*Forward projection from §1. Equivalent to `/gen-gaps` output at the time of this snapshot.*

#### 2a. Layer 1 — REQ Tag Coverage

| Check | Type | Result | Required |
|-------|------|--------|---------|
| req_tags_in_code | deterministic | PASS / FAIL | yes |
| req_tags_in_tests | deterministic | PASS / FAIL | yes |
| req_tags_valid_format | deterministic | PASS / FAIL | yes |
| req_keys_exist_in_spec | agent | PASS / FAIL | yes |

Untagged files: [list or NONE]
Orphan keys: [list or NONE]

#### 2b. Layer 2 — Test Gaps

| Check | Type | Result | Required |
|-------|------|--------|---------|
| all_req_keys_have_tests | agent | PASS / FAIL | yes |

Test gaps (REQ keys with no Validates: tag): [list or NONE]

#### 2c. Layer 3 — Telemetry Gaps

| Check | Type | Result | Required |
|-------|------|--------|---------|
| code_req_keys_have_telemetry | agent | PASS / ADVISORY | at code→cicd |

Telemetry gaps: [list or ADVISORY — edge not yet traversed]

#### 2d. Open Proposals

| ID | Title | Severity | Source | Action |
|----|-------|---------|--------|--------|
| PROP-* | | high/medium/low | gap_analysis | pending / approved / dismissed |

---

### 3. Postmortem

*Backward projection from §1. Temporal reconstruction, performance analysis, root causes.*

#### 3a. Project Profile

| | |
|--|--|
| **Project** | |
| **Intent source** | |
| **Start event** | event N — project_initialized |
| **Release event** | event N — release_created |
| **Wall-clock elapsed** | |
| **Sessions** | N sessions (describe break pattern) |
| **Build approach** | manual / engine-assisted / autonomous |

#### 3b. Lifecycle Timeline

Reconstructed from event timestamps. One row per phase.

| Phase | Events | Start | End | Duration | Key Output |
|-------|--------|-------|-----|---------|-----------|
| Initialization | 1–N | | | | project_initialized, baseline gaps |
| Proposal generation | N–N | | | | N feature vectors created |
| Specification chain | N–N | | | | all shared edges converged |
| First code wave | N–N | | | | N features code+tests |
| Session break | — | | | | [reason if known] |
| Second code wave | N–N | | | | remaining features |
| Validation & release | N–N | | | | gaps_validated, release_created |

**Session structure** (gaps > 30 min between events):

| Session | Events | Start | End | Duration | Features touched |
|---------|--------|-------|-----|---------|-----------------|
| 1 | | | | | |
| [gap] | — | | | N hours | [reason if known] |
| 2 | | | | | |

#### 3c. Edge Performance

One row per edge traversed.

| Edge | Feature | Start | End | Iterations | Evaluators | Result |
|------|---------|-------|-----|-----------|-----------|--------|
| requirements→feature_decomp | all | | | 1 | N/N | CONVERGED |
| … | | | | | | |

**Re-iteration analysis**:
- Edges with > 1 iteration: [list or NONE]
- Root cause of each re-iteration: [compiler error class / evaluator failure type]
- Resolution pattern: [how each was fixed]

**Velocity signals**:
- Fastest edge: [edge name, duration]
- Slowest edge: [edge name, duration, why]
- Total active build time (excluding session gaps): [N hours]

#### 3d. What Worked

For each item: **observation** → **why it worked** → **methodology principle it validates**

1. [Observation]
   - Why: [mechanism]
   - Validates: [Bootloader §N / REQ-* / ADR-*]

#### 3e. What Didn't Work

For each item: **observation** → **root cause** → **impact** → **fix for next run**

1. [Observation]
   - Root cause: [RC-1, RC-2, etc.]
   - Impact: [what broke / what was invisible]
   - Fix: [concrete action for next run]

**Root cause taxonomy** (assign each finding to a category):

| Category | Count | Description |
|----------|-------|-------------|
| F_P gap | | Engine can evaluate but not autonomously construct |
| Event emission | | Required event not emitted |
| Human gate | | F_H blocked progression |
| Spec gap | | Underspecification discovered during construction |
| Evaluator miscalibration | | Convergence claimed before work was complete |
| Session discontinuity | | Context lost between sessions |
| False convergence | | delta=0 via skips, not via passing checks |

#### 3f. Methodology Version Delta

What changed in the methodology between this run and the prior comparable run.

| Aspect | Prior run | This run | Delta |
|--------|-----------|----------|-------|
| Method version | | | |
| Event count | | | +/- N |
| Re-iterations | | | +/- N |
| Coverage | | | +/- % |
| Build approach | | | |

#### 3g. Signals for Next Run

Derived from §3e findings + §2 gaps. Ordered by priority.

1. **[Signal title]** — [what to change, what to enable, what to measure]
   - Blocking: yes / no
   - Tracked as: [REQ-* / backlog item / proposal]

---

### 4. Release Assessment

| Gate | Criterion | Required | Result | Notes |
|------|-----------|---------|--------|-------|
| F_D compile | sbt compile / equivalent | yes | PASS/FAIL | |
| F_D tests | all tests pass | yes | N/N pass | |
| REQ coverage | threshold (e.g. ≥90%) | yes | N% | |
| Event log | complete (all edges instrumented) | yes | COMPLETE/PARTIAL | |
| UAT | all features | recommended | N/N | |
| Telemetry | req= tags in code | at code→cicd | N/A / PARTIAL | |

**Deferred scope** (explicitly excluded, not missed):

| REQ Key | Reason | Target release |
|---------|--------|---------------|
| | | |

**Known technical debt** (included but sub-optimal):

| Item | Description | Impact |
|------|-------------|--------|
| | | |

---

### 6. Event Emission — Homeostatic Loop Closure

*MANDATORY. This section is not optional documentation — it is the mechanism by which the sensor fires. Execute after §2 and §3 are complete.*

**Step 6a: Emit `gaps_validated`** (covers Layers 1–4):

```json
{
  "event_type": "gaps_validated",
  "timestamp": "{ISO 8601}",
  "project": "{project name}",
  "data": {
    "layers_run": [1, 2, 3, 4],
    "feature": "all",
    "total_req_keys": "{n}",
    "layer_results": {
      "layer_1": "pass|fail",
      "layer_2": "pass|fail",
      "layer_3": "pass|advisory",
      "layer_4": "pass|fail"
    },
    "methodology_compliance_flags": [
      {"feature": "{id}", "edge": "{edge}", "issue": "no_events|no_iteration_completed|built_outside_gen_iterate|session_gap_unrecorded|uat_not_per_feature"}
    ]
  }
}
```

**Step 6b: For each finding (gap analysis Layer 1–3 gap OR postmortem root cause OR Layer 4 compliance flag) — emit `intent_raised`**:

```json
{
  "event_type": "intent_raised",
  "timestamp": "{ISO 8601}",
  "project": "{project name}",
  "data": {
    "intent_id": "INT-{SEQ}",
    "trigger": "{what the discovery pass found}",
    "delta": "{specific missing artifact or compliance failure}",
    "signal_source": "gap|methodology_compliance|postmortem_root_cause",
    "vector_type": "feature|hotfix",
    "affected_req_keys": ["{REQ-*}"],
    "affected_features": ["{REQ-F-*}"],
    "severity": "high|medium|low",
    "layer": "1|2|3|4"
  }
}
```

**Clustering rules**:
- Group Layer 1/2/3 gaps by domain (all `REQ-F-AUTH-*` → one intent)
- Group Layer 4 compliance flags by failure type (all "no events" → one intent per feature; session gap → one intent)
- Postmortem root causes: one intent per distinct root cause category
- Severity: High = blocks audit trail or correctness; Medium = process compliance; Low = cosmetic

**Step 6c: For each `intent_raised` — emit `feature_proposal` and write to review queue**:

```json
{
  "event_type": "feature_proposal",
  "timestamp": "{ISO 8601}",
  "project": "{project name}",
  "data": {
    "proposal_id": "PROP-{SEQ}",
    "intent_id": "INT-{SEQ}",
    "title": "{short description}",
    "description": "{what the feature would fix — 2-3 sentences}",
    "affected_req_keys": ["{REQ-*}"],
    "severity": "high|medium|low",
    "vector_type": "feature|hotfix",
    "suggested_profile": "standard|hotfix|minimal",
    "status": "draft",
    "source": "gap_analysis|postmortem",
    "review_path": ".ai-workspace/reviews/pending/PROP-{SEQ}.yml"
  }
}
```

Write corresponding `.ai-workspace/reviews/pending/PROP-{SEQ}.yml` for each proposal.

**Step 6d: Summary**

After emitting all events, display:

```
═══ HOMEOSTATIC LOOP CLOSURE ═══
Layers run:        1, 2, 3, 4
Layer 4 flags:     {n} methodology compliance gaps found
intent_raised:     {n} events emitted
feature_proposals: {n} proposals written to review queue

Review queue: /gen-review-proposal to action pending proposals
Loop status:  {CLOSED — all findings have corresponding intents}
             | {PARTIAL — {n} findings could not be clustered}
             | {OPEN — event emission failed, loop not closed}
═══════════════════════════════
```

**Why this section is mandatory**: findings that stay in a document do not force iterate(). The homeostatic loop closes through events → proposals → feature vectors → iterate(), not through humans reading the report and manually deciding to act. The report is the human-readable rendering; the events are the machine-actionable signal. Both are required.

---

### 5. Appendix

#### 5a. Full Event Log

[paste or reference events.jsonl]

#### 5b. Feature Vector Summary

[condensed trajectory table — one row per feature, all edges]

#### 5c. Deferred Proposals

[any PROP-* not actioned, with disposition]
