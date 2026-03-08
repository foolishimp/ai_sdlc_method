# STRATEGY: Intent Vector Unification — Everything Is an Intent Vector

**Author**: Claude Code
**Date**: 2026-03-08T12:00:00Z
**Addresses**: Vocabulary unification — product vectors, design vectors, feature vectors are all intent vectors
**For**: all

---

## The Unification

A product vector IS an intent vector. A design vector IS an intent vector. A requirements vector IS an intent vector. There is one construct, not many.

What varies is:
- `resolution_level` — which asset type is being produced
- `composition_expression` — which named composition resolves it
- `source` — where the intent came from (abiogenesis, gap, or parent vector)
- `parent_vector` — which vector spawned this one (null for abiogenesis)

The vocabulary collapses. "Feature vector", "discovery vector", "design vector" are not different kinds of thing — they are the same construct at different positions in the causal chain, with different composition expressions bound.

---

## The Causal Chain

Every intent vector has a parent, except one: the abiogenesis — the original human intent that created the first spec and bootstrapped the constraint surface. The Bootloader (§VIII) already names this: "Human intent is the abiogenesis."

```
abiogenesis
  source: human
  parent: null
  composition: ∅  (the human is the composition — they speak the intent)
  → spec + constraint surface
  ↓ spawns

intent_vector[0]  (top-level feature request)
  source: abiogenesis
  parent: abiogenesis
  resolution_level: intent
  composition: PLAN(intent, capability, user_value)
  → work_order[requirements]
  ↓ REVIEW → CONSTRUCT →

intent_vector[1]  (requirements resolution)
  source: intent_vector[0]
  parent: intent_vector[0]
  resolution_level: requirements
  composition: PLAN(requirements, feature, mvp_value)
  → work_order[design]
  ↓ REVIEW → CONSTRUCT →

intent_vector[2]  (design resolution)
  source: intent_vector[1]
  parent: intent_vector[1]
  resolution_level: design
  composition: PLAN(design, module, arch_stability)
  → work_order[code]
  ↓ REVIEW → CONSTRUCT →

intent_vector[3]  (code resolution)
  source: intent_vector[2]
  parent: intent_vector[2]
  resolution_level: code
  composition: BUILD(code ↔ unit_tests)
  → stable_code_asset
  ↓ converges → running system
  ↓ observed by telemetry

intent_vector[4]  (homeostasis — gap detection closes the loop)
  source: gap {type: latency_breach, observed: p99=450ms, threshold: 200ms}
  parent: telemetry_vector
  resolution_level: intent
  composition: POC(latency_issue, risk_areas: [db_query, cache_miss])
  → new branch of the causal chain
```

The chain never breaks. Every vector has a parent. Every parent has a parent. All chains terminate at the abiogenesis or at a gap observation (homeostasis). No vector is causally orphaned.

---

## What "Resolution Level" Means

Resolution level is not a type — it is where in the graph the intent vector is currently positioned. The same underlying intent ("the user needs authentication") resolves progressively:

```
intent          → "user needs to log in securely"
requirements    → REQ-F-AUTH-001..004 (what the system must do)
design          → AuthModule + TokenService + SessionStore (how architecturally)
code            → auth.py + test_auth.py (how concretely)
deployment      → auth-service:v1.2 (how operationally)
telemetry       → login_latency, auth_failure_rate (how observably)
```

Each level is a refinement of the same intent. Each refinement is itself an intent vector — an intent to produce the next asset in the chain, with a composition expression that names how.

---

## Composition Expression as the Vector's DNA

The composition expression is what distinguishes one intent vector from another at the same resolution level. Two intent vectors at `resolution_level: intent` with different compositions are different execution paths from the same starting point:

```
intent_vector_A:
  composition: POC(latency_issue, risk: db_query)
  → produces: poc_report (risk assessed)

intent_vector_B:
  composition: PLAN(intent, capability, user_value)
  → produces: work_order (capability decomposed)
```

Both are intent vectors. Same resolution level. Different compositions. Different outcomes. The composition is the DNA of the vector — it determines what the vector will produce and how it will converge.

---

## Gap Detection as Intent Generation

The homeostasis loop (§VIII of the Bootloader) becomes formally complete:

```
observer detects: p99_latency = 450ms > threshold 200ms
evaluator classifies: TOLERANCE_BREACH (high severity)
typed_output: intent_raised {
  source: gap {type: tolerance_breach, metric: p99_latency, observed: 450ms, threshold: 200ms},
  parent_vector: telemetry_vector[running_system],
  resolution_level: intent,
  composition: POC(latency, risk_areas: [db_query, cache_miss, connection_pool]),
  vector_type: poc
}
```

The gap evaluator does not produce text. It produces an intent vector. That vector enters the same processing pipeline as a human-authored intent. The system does not distinguish between abiogenesis-descended vectors and gap-descended vectors at execution time — they are the same construct, processed the same way.

This is what "the methodology becomes self-modifying" means in the Bootloader: gap-generated intent vectors have the same execution semantics as human intent vectors. The system corrects itself in the same way it builds itself.

---

## Schema Discovery as an Intent Vector

The user's example: given a dataset and Jupyter notebook access, produce a schema document.

```
intent_vector {
  source: gap {type: missing_schema, dataset: transactions.parquet},
  parent_vector: data_pipeline_vector,
  resolution_level: intent,
  composition: SCHEMA_DISCOVERY(
    dataset: data/raw/transactions.parquet,
    exec_env: jupyter://dev,
    criteria: completeness + fitness_for_use
  ),
  vector_type: discovery
}
```

This is indistinguishable in structure from a human-authored feature request. The source is a gap observation, not a human. The composition is SCHEMA_DISCOVERY, not PLAN. The resolution_level is intent. It enters the graph, runs BROADCAST over the data, runs iterate() on each sample, FOLDs into a schema, gates at REVIEW. Produces a schema_document stable asset.

That schema_document becomes context for downstream vectors. If the data pipeline vector was waiting for a schema, it is now unblocked. The causal chain continues.

---

## Implications

### 1. Traceability Is Complete

Every artifact traces causally to either the abiogenesis or a gap observation. "This field in the schema document was discovered in sample batch 3 of transactions.parquet, which was explored because a `missing_schema` gap was detected in the data_pipeline feature vector, which was spawned from intent_vector REQ-F-PIPE-001, which descends from the original project abiogenesis."

That is complete lineage. Not just "this code satisfies this requirement" — but *why* the requirement existed, *what gap* it was addressing, *what human decision* originated the chain.

### 2. Vocabulary Collapses

The current vocabulary has:
- "feature vector" — a vector that produces a feature
- "discovery vector" — a vector that answers a question
- "spike vector" — a vector that assesses risk
- "hotfix vector" — a vector that patches a defect

These are not different kinds of thing. They are intent vectors with different `composition_expression` and `vector_type` bindings. The unified construct:

```yaml
intent_vector:
  id: {REQ-F-* | INT-* | GAP-* | SCHEMA-* | ...}
  source: abiogenesis | gap | parent_vector
  parent_vector: {id | null}
  resolution_level: intent | requirements | design | code | deployment | telemetry
  composition_expression:
    macro: PLAN | POC | SCHEMA_DISCOVERY | DATA_DISCOVERY | BUILD | DISCOVERY | ...
    bindings: {parameter: value, ...}
  vector_type: feature | discovery | spike | poc | hotfix  # kept for profile routing
  profile: standard | full | poc | spike | hotfix | minimal
  status: pending | iterating | converged | blocked | time_box_expired
  parent_status: waiting_for_child | unblocked
```

`vector_type` is kept for profile routing (which edges are in scope, which evaluators apply). But it is a profile selector, not an ontological category.

### 3. The Graph Is a Causal DAG, Not a Pipeline

The SDLC graph is often drawn as a linear pipeline: intent → requirements → design → code. But it is actually a **causal DAG**: multiple intent vectors at different resolution levels, some in parallel, some depending on others, all descending from the same abiogenesis or from gap observations.

The graph topology is the projection of this causal DAG onto the execution model. The Gantt chart (STATUS.md) is a time-projection of the same DAG. The feature lineage view is a causal-ancestry projection.

### 4. Spawning Is Intent Vector Creation

The current `gen-spawn` command creates a child vector. Under this model, spawning is: creating a new intent vector with `source: parent_vector` and a composition expression that resolves the sub-problem. Fold-back is: the child vector converges and its result is injected as context into the parent vector's next iteration. This is already the semantics — the vocabulary now matches.

---

## The Three Sources of Intent

Every intent vector originates from one of three sources:

| Source | Description | Example |
|--------|-------------|---------|
| **Abiogenesis** | Human creates the first intent, bootstrapping the constraint surface | "Build an authentication system" at session start |
| **Gap observation** | The IntentEngine detects a delta between observed state and spec | `missing_schema`, `tolerance_breach`, `spec_drift` |
| **Parent vector** | A vector spawns a child to resolve a sub-problem | Requirements vector discovers an unknown risk, spawns a POC vector |

Parent-vector spawning is just gap observation at a finer scale — the parent vector's iterate() detects a delta in its own sub-problem and spawns a child to resolve it. The three sources collapse to two: abiogenesis (first cause) and gap observation (all subsequent causes).

---

## Formal Statement

An **intent vector** `V` is a tuple:

```
V = (source, parent, resolution_level, composition_expression, profile, status)
```

Where:
- `source ∈ {abiogenesis, gap_observation, parent_vector}`
- `parent ∈ {V | null}` — null iff source = abiogenesis
- `resolution_level ∈ {intent, requirements, design, code, deployment, telemetry}`
- `composition_expression` — a named composition with parameter bindings
- `profile ∈ {full, standard, poc, spike, hotfix, minimal}` — selects the graph projection
- `status ∈ {pending, iterating, converged, blocked, time_box_expired}`

The project is the set of all intent vectors descending from the abiogenesis, plus all intent vectors generated by gap observations during the project's lifetime. The event log is the record of all iterate() invocations across all vectors.

**Convergence**: a project converges when all intent vectors are either `converged` or `blocked` with documented disposition. A running project always has at least one vector `iterating`.

**Homeostasis**: the system is homeostatic when the gap evaluator's outputs (new intent vectors) are bounded — the rate of gap-generated vectors decreases as the system approaches the spec. At steady state, new gap vectors are generated only by environmental changes (ecosystem drift, new requirements) — not by structural defects in the current implementation.
