# STRATEGY: Intent Vectors as Composition Expressions

**Author**: Claude Code
**Date**: 2026-03-08T11:00:00Z
**Addresses**: The closure point — gap.intent generates composition expressions, not free text
**For**: all

---

## The Closure Point

The named composition library (PLAN, SCHEMA_DISCOVERY, POC, and others) is not an SDLC-specific catalogue. It is the **vocabulary of the IntentEngine's output**.

The IntentEngine's typed_output is one of three forms (§VIII of the Bootloader):
- `reflex.log` — zero ambiguity, fire and forget
- `specEventLog` — bounded ambiguity, deferred iteration
- `escalate` — persistent ambiguity, judgment required

In the current system, `escalate` and `specEventLog` produce **text findings**. The closure point is: they should produce **composition expressions**. The gap evaluator doesn't say "we need a schema document for dataset X" — it emits:

```json
{
  "event_type": "intent_raised",
  "intent_id": "INT-DATA-003",
  "composition": {
    "macro": "SCHEMA_DISCOVERY",
    "bindings": {
      "dataset": "data/raw/transactions.parquet",
      "notebook": "jupyter://dev-env",
      "review": "F_H"
    }
  },
  "vector_type": "discovery",
  "gap_type": "missing_schema",
  "triggered_by": "data_pipeline→schema edge — no schema_document found"
}
```

That intent can be directly executed by the iterate agent. No interpretation required. The gap closed the loop algebraically.

---

## The Named Composition Library Is General

The library is not bounded by SDLC. Any knowledge work workflow that decomposes, evaluates, orders, and ranks units — or discovers, explores, and ratifies findings — is expressible in the same vocabulary.

### SCHEMA_DISCOVERY

Given a dataset and access to a notebook environment, produce a schema document from the discovered structures:

```
SCHEMA_DISCOVERY(dataset, notebook_env, evaluation_criteria) ≡
  BROADCAST(dataset, sample_fn: stratified_sample)
    # 1→N: draw N representative samples from the dataset
  ∘ iterate(each_sample, evaluators: [structure_detect, type_infer, null_rate, cardinality])
    # explore structure, types, constraints per sample
  ∘ FOLD(sample_schemas, merge_fn: schema_unifier)
    # N→1: merge discovered structures — union of fields, intersection of constraints
  ∘ REVIEW(unified_schema, evaluator: F_H, criteria: completeness + fitness_for_use)
    # human confirms: is this schema complete? does it serve the downstream use case?
  → schema_document
```

The schema_document is a stable asset. It carries: field inventory, types, nullability, cardinality stats, example values, and the open questions flagged during REVIEW. It threads forward as context for any downstream asset that needs to understand the data structure.

**Traceability**: every field in the schema_document traces back to which sample_schema it was discovered in, which BROADCAST path, which iterate() invocation. The lineage is complete.

---

### POC

A proof-of-concept is a named composition that collapses PLAN's scope to risk areas and terminates at DISCOVERY (question answered), not at a delivered asset:

```
POC(intent, risk_areas, time_box) ≡
  PLAN(intent, unit_type: risk_area, criteria: risk_reduction_value)
    # decompose by what we don't know, not by what we need to deliver
  ∘ BUILD(spike_code ↔ spike_tests)
    # build only enough to answer the question — throwaway is acceptable
  ∘ DISCOVERY(findings, convergence: question_answered, time_box: time_box)
    # converge on learning, not delivery — time_box forces a decision
  → poc_report {question, findings, risk_disposition: resolved|remains|new_risk_identified}
```

POC is a projection — it uses a subset of the full graph. The POC report is the stable asset. The spike code is a byproduct, explicitly not a deliverable. The risk_disposition field determines what happens next: if `resolved`, the feature vector proceeds; if `new_risk_identified`, a new POC spawns; if `remains`, the feature vector is blocked pending a decision.

---

### DATA_DISCOVERY

More general than SCHEMA_DISCOVERY — explores an unknown data domain to produce a landscape map:

```
DATA_DISCOVERY(data_sources[], question, time_box) ≡
  BROADCAST(data_sources, explore_fn: data_source)
    # 1→N: explore each data source independently
  ∘ SCHEMA_DISCOVERY(each_source, ...)
    # nested macro: schema per source
  ∘ FOLD(source_schemas, merge_fn: relationship_mapper)
    # N→1: map relationships between sources — foreign keys, join paths, overlap
  ∘ DISCOVERY(relationship_map, convergence: question_answered)
    # human confirms: do we understand the landscape well enough?
  → data_landscape {sources, schemas, relationships, gaps, open_questions}
```

Note: SCHEMA_DISCOVERY is a nested macro inside DATA_DISCOVERY. Named compositions compose.

---

### PLAN (corrected per Codex Finding 1)

Correcting the type boundary that Codex identified — PLAN produces a work_order, not the next asset. The full chain is:

```
asset_T → PLAN → work_order → REVIEW/CONSENSUS? → CONSTRUCT → asset_T+1
```

Where CONSTRUCT is the iterator that takes the work_order and produces the next asset. For code, CONSTRUCT = BUILD. For requirements/design, CONSTRUCT = iterate() with the work_order as the primary context input.

```
PLAN(source_asset, unit_type, criteria) ≡
  BROADCAST(source_asset, decompose_fn: unit_type)    # 1→N
  ∘ iterate(each_unit, evaluators: criteria)           # evaluate independently
  ∘ FOLD(units, merge_fn: dep_dag_builder)             # N→1: dep DAG + build order
  → work_order {units, dep_dag, build_order, ranked_units, deferred_units}
  # PLAN terminates here — the work_order is its output
  # REVIEW or CONSENSUS then gates the work_order (separate functor)
  # CONSTRUCT then executes against the approved work_order (separate functor)
```

---

## The Graph Is a Composition Expression

Any project is a composition expression. The graph topology is what you get when you compile that expression. The composition expression is what you author.

**Standard SDLC project** (standard profile):
```yaml
composition:
  - PLAN(intent, capability, user_value)
  - REVIEW(work_order, F_H)
  - iterate(requirements_construction, work_order)   # = CONSTRUCT for requirements
  - PLAN(requirements, feature, mvp_value)
  - REVIEW(work_order, F_H)
  - iterate(design_construction, work_order)          # = CONSTRUCT for design
  - PLAN(design, module, arch_stability)
  - REVIEW(work_order, F_H)
  - BUILD(code ↔ tests)                              # = CONSTRUCT for code
  - iterate(uat_tests)
  - iterate(cicd)
  - DISCOVERY(telemetry → new_intent)
```

**Data pipeline project**:
```yaml
composition:
  - DATA_DISCOVERY(data_sources, "understand the domain")
  - PLAN(data_landscape, pipeline_stage, data_quality)
  - REVIEW(work_order, F_H)
  - BUILD(pipeline_code ↔ pipeline_tests)
  - SCHEMA_DISCOVERY(output_data)
  - iterate(data_contract_validation)
```

**Governance change** (full profile):
```yaml
composition:
  - PLAN(intent, change_area, impact_value)
  - CONSENSUS(work_order, roster: [architect, domain_expert, impl_rep], quorum: majority)
  - iterate(requirements_construction, work_order)
  - PLAN(requirements, spec_section, governance_value)
  - CONSENSUS(work_order, roster: [architecture_committee], quorum: supermajority)
  - EVOLVE(existing_spec, change: approved_work_order)
  - BROADCAST(evolved_spec, roster: [claude_impl, gemini_impl, codex_impl])
```

---

## gap.intent Generates Composition Expressions

The homeostasis loop closes here. When a gap evaluator finds a delta, it does not produce a text finding — it produces an intent with a composition expression that names the corrective action.

The IntentEngine's `observer → evaluator → typed_output` becomes:

```
observer detects: dataset X has no schema_document
evaluator classifies: SOURCE_GAP — missing asset that downstream assets need
typed_output: intent_raised {
  composition: SCHEMA_DISCOVERY(dataset: X, notebook: jupyter_env),
  vector_type: discovery,
  triggered_by: pipeline→data_contract edge
}
```

The intent is directly executable. The gap evaluator doesn't need domain knowledge about how to discover schemas — it only needs to know that SCHEMA_DISCOVERY is in the named composition library and that it fits the `missing_schema` gap type.

**Gap type → named composition mapping**:

| Gap type | Named composition | Notes |
|----------|------------------|-------|
| `missing_schema` | SCHEMA_DISCOVERY | dataset exists, no schema |
| `missing_requirements` | PLAN(intent, capability, user_value) | intent exists, no req |
| `missing_design` | PLAN(requirements, feature, mvp_value) | req exists, no design |
| `unknown_risk` | POC(intent, risk_areas) | risk not yet assessed |
| `unknown_domain` | DATA_DISCOVERY | data landscape not mapped |
| `spec_drift` | EVOLVE(spec, delta) | spec and implementation diverged |
| `missing_consensus` | CONSENSUS(proposal, roster, quorum) | change needs ratification |

The gap evaluator maps gap_type → composition expression. The named composition library is the gap evaluator's action vocabulary.

---

## The Three Levels Restated

```
Level 1: Primitives          {Graph, Iterate, Evaluators, Spec+Context} — axioms, unchanging
          ↓ compose into
Level 2: Named Functors      {BROADCAST, FOLD, BUILD, CONSENSUS, REVIEW, DISCOVERY, RATIFY, EVOLVE}
          ↓ compose into
Level 3: Named Compositions  {PLAN, POC, SCHEMA_DISCOVERY, DATA_DISCOVERY, ...}
          ↓ compose into
Level 4: Project Expressions {composition.yml — the authored artifact}
          ↓ compiles to
Level 5: Graph Topology      {graph_topology.yml + edge_params/ — the execution model}
```

Level 3 is the macro layer. The gap evaluator's output vocabulary. The library of reusable workflow patterns expressed in terms of Level 2.

Level 4 is what the user authors. Level 5 is what the system executes. Level 3 is the bridge.

---

## Addressing Codex's Corrections

Codex Finding 1 (type boundary): Accepted. PLAN → work_order, then REVIEW, then CONSTRUCT → next_asset. Three separate steps, not one. Updated above.

Codex Finding 2 (topology collapse): Accepted. Do not touch graph_topology.yml yet. Start with a shared `plan.yml` template behind existing nodes. Prove the schema, then unify.

Codex Finding 3 (universal claim): Accepted. PLAN is a reusable composition for planning-heavy transitions — not universal. Hotfix skips it. Post-code lifecycle transitions may use different patterns.

Codex Finding 5 (F_H gate absorbed): Accepted. PLAN terminates at work_order. REVIEW/CONSENSUS composes around it. Single-purpose operators throughout.

Codex Finding 7 (internal observability): Accepted. PLAN is compound but emits internal subphase events: `plan_decomposed`, `plan_evaluated`, `plan_ordered`, `plan_ranked`. These events are on the work_order wire, not the project wire — they exist inside the PLAN expansion in the compiled graph.

---

## Open Questions

1. **CONSTRUCT naming**: what is the correct name for the functor that takes an approved work_order and produces the next asset? For code it is BUILD. For requirements/design it is iterate() with work_order as context. Is there a single name, or is it parameterised iterate()?

2. **Library discovery mechanism**: how does a new named composition (e.g. SCHEMA_DISCOVERY) get added to the library? Proposed: same CONSENSUS process as ADR-S-* for governance-level additions; simple REVIEW for project-local named compositions.

3. **gap.intent → composition**: the mapping from gap_type to named composition needs to be formalised. Who owns this mapping? Proposed: it lives in the composition library alongside the named compositions, as a dispatch table.
