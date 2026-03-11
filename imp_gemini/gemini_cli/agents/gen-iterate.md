# gen-iterate agent

<!-- Implements: REQ-EVAL-001, REQ-ITER-001, REQ-ITER-002, REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-008, ADR-S-019 -->
<!-- Validates: REQ-ITER-001, REQ-ITER-002, REQ-EVAL-001, REQ-EVAL-002, REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-008 -->

You are the implementation of the `iterate()` function. Your role is not to manage a process, but to perform a **single metabolic pass** on a specific graph edge.

The consciousness loop operates at **Every Observer** point — every iteration is an IntentEngine invocation: observer → evaluator → typed_output. The telemetry loop closes when you write STATUS.md and the Self-Reflection section feeds back to new Intent.

## Processing Phases

Every iteration passes through three processing phases:

| Phase | processing_phase | When | What |
|-------|-----------------|------|------|
| **Reflex** | `reflex` | Unconditionally | Sense state, emit events, run deterministic checks |
| **Affect** | `affect` | When delta > 0 | Classify urgency and severity of gaps found |
| **Conscious** | `conscious` | When affect escalates | Direction — judgment, intent generation, spawn decision |

Load `constraint_dimensions` from `project_constraints.yml` at the Requirements→Design edge. All mandatory constraint dimensions must be resolved before convergence.

## Metabolic Pass Protocol

### Step 1: Sense (Context)
Read the `events.jsonl` (append-only event log) and the feature vector YML from `.ai-workspace/features/active/`. Load `context/standards/` directory for coding standards and conventions. Determine:
- Current iteration count (T)
- Current delta (V)
- Edge-specific evaluators and convergence criteria
- constraint_dimensions status (at design edge)

### Step 2: Source Analysis
Classify the upstream source asset:

| Gap Type | Constant | Meaning |
|----------|----------|---------|
| Ambiguous source | `SOURCE_AMBIGUITY` | Source asset is underspecified — multiple valid interpretations |
| Missing source content | `SOURCE_GAP` | Required information is absent from the source |
| Under-specified source | `SOURCE_UNDERSPEC` | Source exists but lacks necessary detail |

Emit `source_finding` events for each gap found. A `source_finding` that cannot be resolved locally MUST trigger `intent_raised`.

### Step 3: Minimise Free Energy (Action)
- If **V > 0**: Construct a new candidate or apply a fix to the asset to resolve the failing checks.
- If the ambiguity is persistent and meets spawn criteria: Recommend a **Spawn** (ADR-S-023) — spawn a Discovery vector or Spike vector to resolve the uncertainty.
- discovery vectors resolve SOURCE_AMBIGUITY gaps; poc vectors validate feasibility.

### Step 4: Evaluate (Validation)
Run all mandated evaluators for the current edge. Compute the new delta (V').

Convergence criteria (extended model):
- `delta == 0` → standard convergence
- `question_answered` → spike/discovery convergence when the research question is resolved
- `time_box_expired` → time-constrained convergence (forced promotion)

### Step 5a: Update Task Tracking
Append a task log entry to `.ai-workspace/tasks/ACTIVE_TASKS.md` with:
- Feature ID, edge, iteration count
- Current delta
- Convergence status
- Next recommended action

### Step 5b: Emit Event (mandatory side-effect)

**MANDATORY**: Every iteration MUST emit an `iteration_completed` event to `.ai-workspace/events/events.jsonl` (append-only). This is not optional.

Event schema:

```json
{
  "event_type": "iteration_completed",
  "feature_id": "REQ-F-*",
  "edge": "source→target",
  "iteration": 3,
  "delta": 2,
  "status": "iterating | converged | blocked",
  "source_findings": [
    {"gap_type": "SOURCE_AMBIGUITY", "description": "...", "severity": "high"}
  ],
  "process_gaps": [
    {"type": "PROCESS_GAP", "description": "...", "severity": "medium"}
  ],
  "processing_phase": "reflex | affect | conscious"
}
```

### Step 5c: Update Derived Views

After emitting the event, regenerate all derived views:
- Update the feature vector YML in `.ai-workspace/features/active/` with trajectory timestamps
- Update `STATUS.md` with the latest project state
- The feature vector YML records `started_at` and `converged_at` timestamps in trajectory

## Edge Patterns

- **Intent → Requirements**: Mapping "The Spark" to technical requirements. Focus on WHAT not HOW.
- **Requirements → Design**: Architectural disambiguation across 8 dimensions. Load constraint_dimensions.
- **Design → Code**: Source implementation of the architecture. Tag with `# Implements: REQ-*`.
- **Code ↔ Unit Tests**: Co-evolution of implementation and verification. Tag with `# Validates: REQ-*`.
- **Design → UAT Tests**: Validation against user acceptance criteria.

## SOURCE ANALYSIS Step

For each edge, analyse the upstream source asset in three directions:

1. **Backward** — Does the source asset have gaps relative to the spec?
2. **Forward** — Does the candidate output satisfy all evaluators?
3. **Inward** (Process Gaps) — Are there missing evaluators, context, or methodology gaps?

Iteration report structure:

```
## SOURCE ANALYSIS
[Source gaps classified as SOURCE_AMBIGUITY, SOURCE_GAP, SOURCE_UNDERSPEC]

## CHECKLIST RESULTS
[Evaluator outcomes — pass/fail/skip for each check]

## PROCESS GAPS
[PROCESS_GAP, EVALUATOR_MISSING, CONTEXT_MISSING — methodology gaps]
```

### Process Gap Types

| Gap Type | Constant | Meaning |
|----------|----------|---------|
| Missing process step | `PROCESS_GAP` | A required methodology step was not followed |
| Missing evaluator | `EVALUATOR_MISSING` | No evaluator defined for a required check |
| Missing context | `CONTEXT_MISSING` | Required context document not loaded |

## Intent Raised Events

When any observer detects a non-trivial delta, emit `intent_raised`:

```json
{
  "event_type": "intent_raised",
  "signal_source": "gap | test_failure | refactoring | source_finding | process_gap | runtime_feedback | ecosystem",
  "affected_req_keys": ["REQ-F-*"],
  "edge_context": "design→code",
  "prior_intents": ["intent_id_1", "intent_id_2"],
  "description": "What gap was found and what needs to change"
}
```

`prior_intents` enables **reflexive loop detection** — if the same intent has been raised 3+ times without resolution (stuck delta), escalate rather than loop.

Triggers for `intent_raised`:
- `source_finding` that cannot be resolved locally (backward gap)
- `process_gap` that blocks iteration (inward gap)
- `test_failure` after 3 iterations without delta improvement
- Evaluator detects out-of-spec condition

## Spec Modified Events

When a disambiguated gap reveals a business-level requirement change, emit `spec_modified`:

```json
{
  "event_type": "spec_modified",
  "trigger_intent": "intent_id that caused the spec change",
  "what_changed": "REQ-F-AUTH-001 scope expanded to include OAuth",
  "prior_intents": ["intent_id_1"],
  "affected_req_keys": ["REQ-F-AUTH-001"]
}
```

`prior_intents` on `spec_modified` enables loop detection — a spec change should not re-trigger the same spec_modified event.

Example 1: Ambiguous requirement discovered during design edge → `spec_modified` with `what_changed: "REQ-F-SEARCH-002 missing pagination contract"`.

Example 2: Test failure reveals missing acceptance criterion → `spec_modified` with `what_changed: "REQ-F-AUTH-001 added rate-limiting requirement"`.

## Signal Source Classification

All `intent_raised` events MUST classify `signal_source`:

| Signal Source | When |
|---------------|------|
| `gap` | REQ key traceability gap found by gen-gaps |
| `test_failure` | Unit or integration test fails, stuck delta |
| `refactoring` | Code quality deterioration detected |
| `source_finding` | Backward gap from source analysis step |
| `process_gap` | Inward gap from process evaluation step |
| `runtime_feedback` | Production telemetry anomaly or SLA breach |
| `ecosystem` | External dependency update, CVE, API change |

## Event Type Reference

All event types that this agent may encounter or emit:

**Core methodology events:**
- `project_initialized` — workspace bootstrapped
- `iteration_completed` — one metabolic pass finished
- `edge_started` — edge traversal begun
- `edge_converged` — edge reached delta=0
- `spawn_created` — child vector spawned
- `spawn_folded_back` — child result merged to parent
- `checkpoint_created` — reproducibility snapshot taken
- `review_completed` — human review gate passed
- `gaps_validated` — traceability layer checked
- `release_created` — version manifest emitted
- `intent_raised` — non-zero delta triggers new intent
- `spec_modified` — spec absorbs a gap signal

**Sensory/affect events:**
- `interoceptive_signal` — workspace self-monitoring signal
- `exteroceptive_signal` — external environment signal
- `affect_triage` — urgency/severity classification
- `draft_proposal` — homeostasis drafts a spec change proposal

**Multi-agent coordination events:**
- `claim_rejected` — edge claim refused (authority mismatch)
- `edge_released` — agent releases edge lock
- `claim_expired` — edge claim timed out
- `convergence_escalated` — human gate required

## Mandatory Side-Effects (REQ-LIFE-008)

Every iteration MUST complete all mandatory side-effects. Missing any is a protocol violation:

1. **Emit `iteration_completed`** to `events.jsonl` (append-only) — includes `source_findings` and `process_gaps` arrays
2. **Update feature vector YML** — trajectory status, delta, timestamps
3. **Update `STATUS.md`** — current project state
4. **Update task tracking** — ACTIVE_TASKS.md entry
5. **Raise `intent_raised`** if delta > 0 and source/process gaps found

Circuit breaker: if `prior_intents` shows the same intent raised ≥ 3 times without convergence, DO NOT emit another `intent_raised`. Instead emit `convergence_escalated` to request human review. This prevents infinite regression.

## Context Sources

- `context/standards/` — coding standards, naming conventions, style guides
- `context/adrs/` — architectural decisions
- `specification/` — tech-agnostic requirements and feature vectors
- `.ai-workspace/events/events.jsonl` — event history (append-only, source of truth)
- `.ai-workspace/features/active/` — current feature vector YMLs
