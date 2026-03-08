# Higher-Order Functors: Named Compositions Above the Primitives

**Version**: 0.1.0 (provisional — pending peer review and ADR-S-025 ratification)
**Status**: Draft — under CONSENSUS review
**Date**: 2026-03-08
**Series**: Core specification — extension of `AI_SDLC_ASSET_GRAPH_MODEL.md`

---

## 1. The Three-Level System

The formal system has three levels:

```
Level 1: Primitives          {Graph, Iterate, Evaluators, Spec+Context}
          ↓ parameterised by
Level 2: Higher-Order Functors   {BROADCAST, FOLD, BUILD, CONSENSUS, REVIEW,
                                  DISCOVERY, RATIFY, EVOLVE}
          ↓ composed into
Level 3: Project Composition     {composition expression + parameter bindings}
```

**Level 1 — Primitives** are the axioms. Unchanging. Four primitives, one operation (`iterate()`). Everything else emerges from them.

**Level 2 — Higher-Order Functors** are named compositions above the primitives that recur across domains and projects. They are not new primitives — each one is a parameterisation or composition of `iterate()` + evaluators + graph structure. They are the vocabulary of a methodology algebra.

**Level 3 — Project Composition** is how a specific project is expressed. A project is a composition expression in the functor vocabulary, plus parameter bindings. The graph topology is a derived output of compiling the composition expression — not a hand-authored artifact.

---

## 2. Why Higher-Order Functors

The SDLC graph is one domain-specific instantiation of the formal system. Without named compositions, every project is a hand-authored graph, and recurring patterns (parallelism, review gates, co-evolution loops, multi-party evaluation) are re-invented each time with inconsistent semantics.

The functor library solves this by naming the patterns:
- Recurring structures become first-class, reusable, composable
- Projects are expressed as composition expressions, not graphs
- Gap evaluation over composition expressions produces typed intents (not free text)
- A methodology compiler can generate graph topology and edge params from a composition expression

**The composition expression is the authored artifact.** The graph is compiled output.

---

## 3. The Provisional Library

The following eight functors are a **provisional working library** — not a claimed complete basis. They cover the principal recurring structures identified across SDLC workflows, governance patterns, and cross-domain process spaces. The library will be presented as provisional until:
- Cancellation and unknown-N fan-out are tighter
- Output typing for REVIEW is finalised
- CONSENSUS semantics are ratified (ADR-S-025)
- The relationship between RACE and BROADCAST+FOLD+CONSENSUS is formally established

---

## 4. Functor Definitions

For each functor, the ordering is: **operational semantics first → type signature → categorical interpretation (where explicitly constructed, otherwise labelled as conjecture)**.

This ordering is required: algebraic laws depend on objects, morphisms, and side conditions being fixed first. Claims stated before that work is done are intuitions, not laws. Intuitions are marked `[conjecture]`.

---

### 4.1 BROADCAST — Fan-Out Coordinator

**Operational semantics**:
BROADCAST takes one asset and distributes it to N parallel evaluation/construction paths. Each path runs an independent `iterate()` invocation. The invoker holds the roster (N is known at invocation time). BROADCAST does not complete until all N paths emit results — it is a synchronous fan-out, not a fire-and-forget.

```
BROADCAST(asset, roster: [path_1, ..., path_N], context) →
  parallel: [iterate(asset, context, evaluators_i) for each path_i in roster]
  returns: N result assets (one per path)
```

Convergence: all N paths have converged. Partial convergence (some paths done, others not) is a waiting state — not failure.

**Type signature** (wire count):
```
BROADCAST : 1 → N
```
One asset wire in, N asset wires out.

**Parameter bindings**:
- `roster`: list of N paths, each with its own evaluator config
- `context`: shared standing constraints (the same context is passed to all N)
- `sync_mode`: `all` (default, wait for all N) or `any` (first-past-gate, see RACE)

**Categorical interpretation**: BROADCAST is a co-product operation — one object maps to a product of N objects. In string diagram notation, BROADCAST is a "splitting" box with one input wire and N output wires. `[conjecture: BROADCAST ⊣ FOLD forms an adjunction — every BROADCAST implies a corresponding FOLD; this requires the fold to be loss-free with respect to the broadcast's output type for the adjunction to hold.]`

---

### 4.2 FOLD — Fan-In Collector

**Operational semantics**:
FOLD takes N result assets (from N parallel paths) and merges them into one. The merge operation is parameterised — it can be union, intersection, first-wins, or evaluation-weighted. FOLD is the complement of BROADCAST.

```
FOLD(results: [asset_1, ..., asset_N], merge_fn, context) →
  single merged asset
```

Convergence: merge_fn produces a single stable asset that passes the FOLD evaluator. If merge_fn cannot produce a coherent merge (conflicting outputs), FOLD fails and requires human resolution (escalate to F_H).

**Type signature**:
```
FOLD : N → 1
```
N asset wires in, one asset wire out.

**Parameter bindings**:
- `merge_fn`: union | intersection | first_wins | consensus_weighted | custom
- `evaluator`: convergence criteria on the merged output

**Note on merge failure**: A FOLD that cannot merge is not a BROADCAST fault — it is a signal that the parallel paths produced incompatible outputs. The typed failure is `fold_conflict`, which escalates to F_H with the conflicting outputs presented for human resolution.

**Categorical interpretation**: FOLD is a product operation — N objects map to one object via a chosen merging morphism. `[conjecture: BROADCAST∘FOLD = identity only under a lossless fold with no semantically relevant branch-local mutation. Not generally true. Side condition required.]`

---

### 4.3 BUILD — Co-Evolution Loop

**Operational semantics**:
BUILD is the TDD pattern. Two assets co-evolve: each `iterate()` invocation evaluates one asset against the other, producing a new candidate for the other. The loop continues until both assets simultaneously satisfy their evaluators.

```
BUILD(asset_A, asset_B, evaluators_A, evaluators_B, context) →
  loop until stable(A) ∧ stable(B):
    A_candidate = iterate(A, context ∪ {B}, evaluators_A)
    B_candidate = iterate(B, context ∪ {A}, evaluators_B)
    A ← A_candidate
    B ← B_candidate
  return (stable_A, stable_B)
```

The key property: each asset is part of the context for the other's evaluation. This creates a feedback loop, not a sequential dependency.

**Type signature**:
```
BUILD : 2 → 2     (two assets with feedback — each is context for the other)
```

**String diagram**: The feedback structure is explicit in string diagrams — two parallel wires with crossing feedback connections. This eliminates the ambiguity of textual notation ("code tests" vs "code then tests").

**Canonical application**: Code ↔ Unit Tests. Code is evaluated against test outcomes; tests are evaluated against code coverage and correctness. Both converge simultaneously.

**Deadlock freedom**: BUILD is deadlock-free if the evaluators of A are responsive to B's output and vice versa. `[conjecture: this is a session type property — A and B have dual types in the sense of multiparty session types (Honda et al. 2008). The dual session typing property, if it holds, gives a proof of deadlock freedom. Side conditions on the evaluator types need explicit construction.]`

**Parameter bindings**:
- `evaluators_A`: convergence criteria for asset A
- `evaluators_B`: convergence criteria for asset B
- `max_co_iterations`: bound on the co-evolution loop (prevents runaway)

---

### 4.4 CONSENSUS — Multi-Stakeholder Evaluator

**Operational semantics**:
CONSENSUS is a parameterisation of F_H, not a new evaluator type. It extends F_H with a roster (N participants) and a quorum rule. The formal evaluator model remains {F_D, F_P, F_H}. CONSENSUS is `F_H(roster: N, quorum: rule)`.

```
CONSENSUS(asset, roster: [participant_1, ..., participant_N], quorum_rule, min_duration, context) →
  Phase 1: Publish asset to roster, open review window
  Phase 2: Collect comments (each requiring disposition before convergence)
  Phase 3: Collect votes (approve | reject | abstain)
  Phase 4: Evaluate quorum (deterministic gate — F_D)
  → consensus_reached (if quorum satisfied) | consensus_failed (typed failure)
```

**Type signature**:
```
CONSENSUS : (1 + N) → 1
```
One proposal wire + N participant wires → one decision wire (approved asset or typed failure result).

**Full operational semantics**: See ADR-S-025 for complete specification, including:
- Quorum formulas (neutral vs counts_against abstention models)
- Veto semantics (named role — overrides quorum arithmetic)
- Late comment handling
- `consensus_failed` as a first-class typed outcome with `failure_reason` and `available_paths`
- Three recovery paths: `re_open`, `narrow_scope`, `abandon` (F_H decision by proposer)
- 6 new OL event types: `proposal_published`, `comment_received`, `vote_cast`, `consensus_reached`, `consensus_failed`, `recovery_path_selected`

**Status**: ADR-S-025 ratified 2026-03-08. See `specification/adrs/ADR-S-025-consensus-functor.md` for full normative semantics.

**Relationship to RATIFY**: `RATIFY = CONSENSUS + Promote(stability)`. CONSENSUS is the multi-party evaluation; RATIFY is CONSENSUS composed with a stability state change. They are separable — CONSENSUS without RATIFY is evaluation without promotion.

---

### 4.5 REVIEW — Single-Evaluator Gate

**Operational semantics**:
REVIEW is a single F_H evaluation gate — one evaluator (human or agent) examines an asset and produces a disposition. Unlike CONSENSUS (which requires quorum), REVIEW is satisfied by one evaluator.

```
REVIEW(asset, evaluator, criteria, context) →
  evaluator examines asset against criteria
  → approved (asset + review status) | rejected (asset + rejection rationale) | revision_requested (asset + change list)
```

REVIEW is not annihilation — it produces output. The asset carries its review status forward.

**Type signature**:
```
REVIEW : 1 → 1     (asset + review status on the output wire)
     or : 1 → 2    (asset + review artifact as separate output)
```

The 1→2 form applies when the review produces a separate artifact (e.g., review record, gate certificate) that becomes its own asset in the graph. The 1→1 form applies when review status is carried as metadata on the original asset. Which form applies is determined by whether the review artifact needs its own convergence lifecycle.

**Parameter bindings**:
- `evaluator`: F_H (human) or F_P (agent) — the reviewer
- `criteria`: convergence checklist for this review
- `output_form`: `status_on_asset` (1→1) | `separate_artifact` (1→2)

**Distinction from CONSENSUS**: REVIEW is singular — one evaluator, binary decision. CONSENSUS is plural — N evaluators, quorum decision. A CONSENSUS with roster size 1 and unanimity threshold is operationally identical to REVIEW.

---

### 4.6 DISCOVERY — Question-Answering Convergence

**Operational semantics**:
DISCOVERY reframes convergence from "evaluator passes" to "question answered". The iteration loop runs until a human confirms the research question has been sufficiently answered — not until a fixed evaluator set passes.

```
DISCOVERY(question, context, time_box) →
  iterate until human confirms: "question answered" | time_box_expired
  → answered (findings asset) | time_box_expired (partial findings asset)
```

The convergence criterion is a human judgment ("has enough been learned?"), not a deterministic checklist. This makes DISCOVERY inherently F_H-terminated.

**Type signature**:
```
DISCOVERY : 1 → 1     (question wire in → findings wire out)
```

The internal structure changes: unlike standard `iterate()` where a fixed evaluator set determines convergence, DISCOVERY has a mutable convergence criterion that evolves as the research matures.

**Parameter bindings**:
- `question`: the research question (drives context loading)
- `time_box`: max_duration + min_duration (optional)
- `convergence_mode`: `question_answered` (F_H confirms) | `time_box_expired` (automatic)

**Vector type correspondence**: DISCOVERY maps to the `discovery` vector type in the feature vector model. The `convergence_type: question_answered` event field captures this.

---

### 4.7 RATIFY — Stability Promotion

**Operational semantics**:
RATIFY takes a converged asset and promotes it to `stability: ratified` — a higher stability level than standard convergence. RATIFY = CONSENSUS + stability state change. The evaluation phase is CONSENSUS; the promotion phase is deterministic.

```
RATIFY(asset, roster, quorum_rule, min_duration, context) →
  result = CONSENSUS(asset, roster, quorum_rule, min_duration, context)
  if result = consensus_reached:
    → promote(asset, stability: ratified)
  if result = consensus_failed:
    → consensus_failed (no promotion)
```

**Type signature**:
```
RATIFY : 1 → 1     (same asset, higher stability status on the output wire)
```

**Stability levels** (for reference):
```
candidate → stable (single-evaluator convergence) → ratified (RATIFY/CONSENSUS)
```

**Use cases**: Spec-level ADR acceptance, methodology version promotion, release gates requiring multi-party sign-off.

**Relationship to CONSENSUS**: RATIFY is CONSENSUS composed with promotion. They are separable — a CONSENSUS result can be used without promotion (evaluation without state change), and promotion can follow CONSENSUS independently.

---

### 4.8 EVOLVE — Versioned Re-Entry

**Operational semantics**:
EVOLVE takes a ratified/stable asset and re-opens it for another convergence cycle under modified context or requirements. The asset transitions from `stability: stable/ratified` back to `candidate`, carrying its lineage, then converges again to a new stable state.

```
EVOLVE(stable_asset, change_intent, context, evaluators) →
  candidate = derive(stable_asset, change_intent)    # carry lineage, increment version
  iterate(candidate, context, evaluators) until stable
  → new_stable_asset (with incremented version and lineage pointing to prior)
```

**Type signature**:
```
EVOLVE : 1 → 1     (stable asset in → new stable asset out, same type, new version)
```

**Critical property**: EVOLVE preserves lineage — the new stable asset knows what it evolved from. This enables spec evolution traceability: `EVOL-001 at version 3 was derived from EVOL-001 at version 2, which was derived from version 1`.

**Relationship to spec stability**: A spec section under EVOLVE is temporarily a candidate — downstream assets built against it are in flux. The `spec_modified` event (REQ-EVOL-004) signals this state to dependent feature vectors.

**Distinction from creating a new asset**: EVOLVE preserves identity across versions. A new asset has no prior stable state. EVOLVE is versioning; creating is inception.

---

## 5. Wire Count Summary (Prop Structure)

In the Fong & Spivak string diagram formalism (Ch. 6: signal flow graphs as props), objects in the category are natural numbers representing wire count. A valid composition has no dangling wires and no type mismatches.

```
BROADCAST  : 1 → N     (fan-out: one wire splits to N parallel wires)
FOLD       : N → 1     (fan-in: N parallel wires merge to one)
BUILD      : 2 → 2     (two wires with feedback — not sequential, co-evolving)
CONSENSUS  : (1+N) → 1 (proposal wire + N participant wires → one decision wire)
REVIEW     : 1 → 1     (or 1 → 2 when review artifact is a separate output)
DISCOVERY  : 1 → 1     (question wire → findings wire)
RATIFY     : 1 → 1     (asset wire → ratified asset wire)
EVOLVE     : 1 → 1     (stable asset → new stable asset)
iterate()  : 1 → 1     (loops internally until stable — the base operation)
```

**Composition validity**: A well-formed methodology is a wiring diagram with no dangling wires and no wire-count mismatches. `BROADCAST(n) ∘ FOLD(n) = iterate()` is only true under a lossless fold with no branch-local mutation `[conjecture — requires explicit side conditions]`.

---

## 6. Named Compositions (Macros)

> **Authority**: [ADR-S-026](../adrs/ADR-S-026-named-compositions-and-intent-vectors.md) is the ratified specification for this layer. This section is an operational summary. For the formal definitions, five-level stack, gap.intent output contract, intent vector tuple, and project convergence vocabulary, see the ADR.

Named compositions are **not additional functors**. They are named shorthand for recurring compositions of the 8 primitive functors — macros in the composition language. The functor library stays at 8. Named compositions expand into it.

A named composition is defined once, parameterised, and invoked by name in project composition expressions. The composition compiler expands it into the constituent functor graph at compile time. The wire-count signature at the call site is simple; the internal expansion carries the full complexity.

**Named compositions serve two roles**:
1. **Reusable workflow templates** — reduce duplication across projects and transitions
2. **gap.intent action vocabulary** — when a gap evaluator detects a delta, it emits an intent whose corrective action is a named composition expression, not free text. The intent is directly executable.

---

### 6.1 PLAN

PLAN is a reusable composition for planning-heavy transitions — wherever a source asset must be decomposed into an ordered work plan before construction begins. It is **not universal**: `hotfix` skips it entirely; post-code lifecycle stages may use different patterns.

**Composition** (per Codex Finding 1 — type boundary preserved):
```
PLAN(source, unit_type, criteria) ≡
  BROADCAST(source, decompose_fn: unit_type)         # 1→N: split into candidate units
  ∘ iterate(each_unit, evaluators: criteria)          # evaluate each independently
  ∘ FOLD(units, merge_fn: dep_dag_builder)            # N→1: ordered dependency structure
  → work_order {units, dep_dag, build_order, ranked_units, deferred_units}
```

**PLAN terminates at work_order.** The work_order is then gated separately (REVIEW or CONSENSUS) and consumed by a construction step (iterate() or BUILD). These are three separate composition steps — PLAN does not absorb the gate or the constructor:

```
asset_T → PLAN → work_order → REVIEW/CONSENSUS → CONSTRUCT → asset_T+1
```

**Wire count**:
```
PLAN : 1 → 1    (source asset → work order)
```
Internally 1→N→N→1. The work_order is a stable asset with its own convergence lifecycle.

**Parameterisation across transitions**:

| Transition | unit_type | criteria |
|-----------|-----------|---------|
| intent → requirements | capability / problem area | user value, scope clarity |
| requirements → design | feature (REQ-F-* group) | feasibility, dependency, MVP value |
| design → code | module / component | architectural stability, test surface |
| code → deployment | deployment unit | environment fitness, rollback safety |

**Internal observability** (compound — does not split into graph nodes, but emits subphase events):
```
plan_decomposed    — units[] produced from source asset
plan_evaluated     — each unit assessed against criteria
plan_ordered       — dep_dag and build_order derived
plan_ranked        — MVP/deferred scope assigned
```

**Note on existing graph nodes**: `feature_decomposition` and `design_recommendations` in the current graph_topology.yml are candidates for unification as PLAN instances. They are not yet proven to be fully equivalent — `feature_decomposition` carries ADR-S-013 invariants (REQ coverage checks, visibility projections) that must be explicitly preserved in any PLAN parameterisation before the collapse is valid. Start with a shared `plan.yml` template behind existing nodes; prove the common schema; then unify. Do not modify graph_topology.yml prematurely.

---

### 6.2 SCHEMA_DISCOVERY

Given a dataset and access to an execution environment (e.g. Jupyter notebook), produce a schema document from the structures discovered in the data.

```
SCHEMA_DISCOVERY(dataset, exec_env, criteria) ≡
  BROADCAST(dataset, sample_fn: stratified_sample)
    # 1→N: draw representative samples from the dataset
  ∘ iterate(each_sample, evaluators: [structure_detect, type_infer, null_rate, cardinality])
    # explore structure, types, constraints per sample
  ∘ FOLD(sample_schemas, merge_fn: schema_unifier)
    # N→1: union of fields, intersection of constraints, open questions surfaced
  ∘ REVIEW(unified_schema, evaluator: F_H, criteria: completeness + fitness_for_use)
    # human confirms: complete? fit for downstream use?
  → schema_document {fields, types, nullability, cardinality, examples, open_questions}
```

**Wire count**: `SCHEMA_DISCOVERY : 1 → 1` (dataset → schema_document)

**Traceability**: every field in the schema_document traces to the sample_schema it was discovered in, which BROADCAST path, which iterate() invocation. Full lineage is in the event log.

**Nests inside**: DATA_DISCOVERY (see §6.3).

---

### 6.3 DATA_DISCOVERY

Explore an unknown data domain across multiple sources to produce a landscape map.

```
DATA_DISCOVERY(data_sources[], question, time_box) ≡
  BROADCAST(data_sources, explore_fn: data_source)
    # 1→N: explore each source independently
  ∘ SCHEMA_DISCOVERY(each_source, exec_env, criteria)
    # nested composition: schema per source
  ∘ FOLD(source_schemas, merge_fn: relationship_mapper)
    # N→1: map relationships — foreign keys, join paths, overlap, gaps
  ∘ DISCOVERY(relationship_map, convergence: question_answered, time_box: time_box)
    # human confirms: do we understand the landscape well enough?
  → data_landscape {sources, schemas, relationships, gaps, open_questions}
```

**Wire count**: `DATA_DISCOVERY : 1 → 1` (data_sources → data_landscape)

Note: SCHEMA_DISCOVERY is a nested named composition inside DATA_DISCOVERY. Named compositions compose — the library is closed under composition.

---

### 6.4 POC

A proof-of-concept: decompose by risk rather than feature, build only enough to answer the question, converge on learning not delivery.

```
POC(intent, risk_areas, time_box) ≡
  PLAN(intent, unit_type: risk_area, criteria: risk_reduction_value)
    # decompose by what we don't know — not by what we need to deliver
  ∘ REVIEW(work_order, evaluator: F_H)
    # human approves: are these the right risks to probe?
  ∘ BUILD(spike_code ↔ spike_tests)
    # build only enough to answer — throwaway is acceptable
  ∘ DISCOVERY(findings, convergence: question_answered, time_box: time_box)
    # converge on learning — time_box forces decision even if question partially answered
  → poc_report {question, findings, risk_disposition: resolved|remains|new_risk_identified}
```

**Wire count**: `POC : 1 → 1` (intent → poc_report)

The `risk_disposition` field determines the fold-back: `resolved` → feature proceeds; `new_risk_identified` → spawn new POC; `remains` → blocked, human decides.

---

### 6.5 gap.intent → Named Composition Dispatch

The gap evaluator's action vocabulary is the named composition library. When a gap is detected, the IntentEngine emits an intent whose corrective action is a named composition expression — directly executable, not free text:

```json
{
  "event_type": "intent_raised",
  "intent_id": "INT-DATA-003",
  "composition": {
    "macro": "SCHEMA_DISCOVERY",
    "bindings": { "dataset": "data/raw/transactions.parquet", "exec_env": "jupyter://dev" }
  },
  "vector_type": "discovery",
  "gap_type": "missing_schema"
}
```

**Gap type → named composition dispatch table** (grows with the library):

| Gap type | Named composition | Trigger condition |
|----------|------------------|-------------------|
| `missing_schema` | SCHEMA_DISCOVERY | dataset exists, no schema_document |
| `missing_requirements` | PLAN(intent, capability) | intent exists, no requirements asset |
| `missing_design` | PLAN(requirements, feature) | requirements exist, no design asset |
| `unknown_risk` | POC(intent, risk_areas) | risk not yet assessed |
| `unknown_domain` | DATA_DISCOVERY | data landscape not mapped |
| `spec_drift` | EVOLVE(spec, delta) | spec and implementation diverged |
| `needs_ratification` | CONSENSUS(proposal, roster) | change needs multi-party agreement |

The dispatch table is owned by the composition library. The gap evaluator reads it; it does not hard-code gap→composition mappings.

---

### 6.6 Defining New Named Compositions

Rules for adding a named composition:

1. **Defined in terms of Level 2 functors only** — may nest other named compositions
2. **Explicit parameters** — what varies across invocations is declared
3. **Single wire-count signature** at the call site — internal complexity is hidden
4. **Expansion known to the compiler** — the compiler can substitute it into the graph
5. **gap_type → composition mapping** added to the dispatch table if the composition is a corrective action for a gap type

Governance: project-local named compositions need only a REVIEW (single F_H). Cross-tenant or library-level named compositions go through CONSENSUS. No ADR-S-* required unless a new constraint type or new event taxonomy is introduced.

---

## 7. Project Composition Expressions

A project is a composition expression in the functor vocabulary. The graph topology and edge params are derived outputs of compiling this expression.

### 6.1 Standard SDLC Composition

```yaml
# genesis_sdlc.project.yml
composition:
  - iterate(intent → requirements)
  - iterate(requirements → feature_decomp)
  - REVIEW(feature_decomp, evaluator: F_H, criteria: "scope and feasibility")
  - iterate(feature_decomp → design)
  - BROADCAST(design, roster: [feature_1, feature_2, ..., feature_N])
    - BUILD(code ↔ unit_tests)
  - FOLD(features → integrated_code, merge_fn: union)
  - iterate(integrated_code → uat_tests)
  - REVIEW(uat_tests, evaluator: F_H, criteria: "acceptance")
  - iterate(uat_tests → cicd)
  - iterate(running_system → telemetry)
  - DISCOVERY(telemetry → new_intent)
```

### 6.2 Governance Composition (Spec Evolution)

```yaml
# spec_evolution.project.yml
composition:
  - iterate(draft → proposal)
  - CONSENSUS(
      proposal,
      roster: [architect, domain_expert, implementer_rep],
      quorum: majority,
      min_duration: P14D
    )
  - RATIFY(
      proposal,
      roster: [architecture_committee],
      quorum: supermajority,
      min_duration: P7D
    )
  - EVOLVE(existing_spec, change: ratified_proposal)
  - BROADCAST(evolved_spec, roster: [claude_impl, gemini_impl, codex_impl])
```

### 6.3 The Composition Compiler

A **composition compiler** is a pure F_D function:

```
compile(composition_expression, parameter_bindings) →
  {graph_topology.yml, edge_params/*.yml}
```

It expands each functor into its constituent graph fragments and wiring. The graph topology is the intermediate representation — it is the execution model the runtime already knows how to execute.

**Compiler direction** (per Codex Finding 4 — partially accepted):
The graph stays as the canonical execution model (agreed). Composition compiles *down* to graph topology; composition does not replace the graph as runtime representation. The derived topology concept is valid; the IR layer between composition and graph as a separate checkable artifact is not needed — the gap evaluator serves that function at runtime.

**Composition validation**: A valid composition has no dangling wires. The gap evaluator detects wiring violations at runtime (orphaned feature vectors, asymmetric BUILD, missing FOLD after BROADCAST). This is runtime type-checking, not static compilation — appropriate for a living system where the composition mutates mid-run.

---

## 8. Gap Evaluation Over Composition

When gap analysis identifies a missing or broken functor, the finding is expressed as a typed operation on the composition, not free text:

```
GAP TYPE         INTENT TYPE           EXAMPLE
─────────────    ──────────────────    ─────────────────────────────────────────
Missing functor  INSERT(functor)        INSERT(REVIEW) between code and uat_tests
Wrong parameter  PARAMETERISE(functor) PARAMETERISE(CONSENSUS, quorum: supermajority)
Missing edge     APPEND(edge)          APPEND(iterate(telemetry → new_intent))
Broken wire      REWIRE(src → tgt)     REWIRE(FOLD.output → cicd.input)
Excess functor   REMOVE(functor)       REMOVE(REVIEW) — now handled by CONSENSUS
```

This makes gap evaluation **algebraically precise**: every gap is a diff on the composition expression. The intent is the composition diff. The `iterate()` loop on the methodology itself uses these typed intents as work.

---

## 9. Provisional Status and What Remains Open

The eight-functor library is presented as provisional for these specific reasons:

1. **Cancellation (RACE)**: A `(N→1, first-wins)` functor is backlogged. The complex parallel case (all paths evaluated, outcomes federated through CONSENSUS) is expressible as `BROADCAST∘FOLD∘CONSENSUS`. The degenerate case (first-past-gate with cancel) is niche. RACE is not needed for the common cases, but the library cannot claim completeness without accounting for it.

2. **Unknown-N fan-out**: Modelled as the observer/publish pattern (observers self-register on the immutable event log; publisher has zero coupling to consumer count). This works for the Genesis architecture. Whether the observer pattern fully subsumes BROADCAST with dynamic roster in all cases is not yet formally established.

3. **REVIEW output typing**: 1→1 vs 1→2 depends on whether the review artifact needs its own convergence lifecycle. Both forms are valid; the choice is parameterised. The library treats this as a parameter, not a single correct answer.

4. **CONSENSUS**: ADR-S-025 ratified 2026-03-08. Veto role deferred to ADR-S-026; agent-as-participant left explicitly open. The functor library entry at §4.4 is stable.

5. **Algebraic laws**: All categorical claims (adjunctions, commutativity, identity laws) are labelled `[conjecture]`. They require explicit construction of objects, morphisms, and side conditions before they can be stated as laws. The direction of travel is correct; the proofs are not yet in hand.

---

## 10. Relationship to the Bootloader

This document is an extension of `AI_SDLC_ASSET_GRAPH_MODEL.md`. It does not modify the four primitives or the single operation (`iterate()`). Everything in this document is emergence from those primitives.

The Genesis Bootloader (§VI, §VIII) describes the evaluator types (F_D, F_P, F_H) and the IntentEngine composition law. This document adds Level 2 — named compositions — which sit between the primitives and project-level composition expressions.

**The four-primitive model is unchanged.** Higher-order functors are compositions, not new primitives.

---

## 11. Key Literature

| Work | Relevance to This Document |
|------|---------------------------|
| Fong & Spivak, *Seven Sketches in Compositionality* (2019) | String diagram notation, monoidal categories, prop structure for wire counting |
| van der Aalst et al., *Workflow Patterns* (2003) | 43-pattern completeness pressure test — confirmed 8 functors cover the principal structures |
| Honda et al., *Multiparty Session Types* (2008) | BUILD deadlock freedom conjecture — dual session typing |
| Bergstra & Klop, *ACP* (1984); Milner, *CCS* (1989) | Process algebra correlations: iterate() as recursive process, BUILD as parallel composition |
| Waters & Bassler, *Quorum Sensing Review* (2005) | Biological validation of CONSENSUS — convergent evolution in unrelated bacterial lineages |
| Girard, *Linear Logic* (1987) | REVIEW as resource consumption — asset consumed and transformed, not duplicated |

---

## 12. References

- `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md` — the four primitives, §5.3 (constraint tolerances, lower-bound type added)
- `specification/core/GENESIS_BOOTLOADER.md` — §VI (evaluators), §VIII (IntentEngine)
- `specification/adrs/ADR-S-024-consensus-decision-gate.md` — marketplace consensus decision gate (separate concern from CONSENSUS functor)
- `specification/adrs/ADR-S-025-consensus-functor.md` — CONSENSUS full operational semantics (pending ratification)
- `.ai-workspace/comments/claude/20260308T070000_STRATEGY_Higher-Order-Functors-From-Primitives.md` — origin post
- `.ai-workspace/comments/codex/20260308T165500_REVIEW_Claude-March-8-functor-library-sequence.md` — mathematical corrections accepted
- `.ai-workspace/comments/gemini/20260308T054700_REVIEW_Process-Algebra-and-Functor-Library-Formalization.md` — IR layer proposal (rejected with rationale)
- `.ai-workspace/comments/claude/20260308T080000_REVIEW_Response-to-Gemini-and-Codex.md` — accepted corrections and rejections documented
