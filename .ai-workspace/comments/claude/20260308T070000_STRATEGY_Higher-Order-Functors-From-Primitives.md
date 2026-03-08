# STRATEGY: Higher-Order Functors as a Complete Basis for Project Composition

**Author**: Claude Code
**Date**: 2026-03-08T07:00:00Z
**Addresses**: Extending the Asset Graph Model — from hand-authored topology to derived composition
**For**: all
**Status**: Proposal — user confirmed "this conversation is gold", capturing for the record

---

## Summary

The four primitives {Graph, Iterate, Evaluators, Spec+Context} are a basis. Above them sits a small vocabulary of higher-order functors — structural compositions of `iterate()` that give names to recurring patterns. From these, any project methodology can be expressed as a composition expression. The graph topology and edge configs are then *derived*, not hand-authored. Gap evaluation becomes typed functor operations, not free-text findings. The methodology can repair itself.

---

## The Three Axes of Composition

Higher-order functors are not new primitives. They are named compositions that appear everywhere you want to suppress repetition. They cluster on three natural axes:

```
Graph structure operators   — how nodes/edges compose spatially
Evaluator operators         — how evaluators combine within an edge
Convergence operators       — how the stopping criterion changes
```

---

## The Eight Higher-Order Functors

### Axis 1: Graph Structure

**BROADCAST** `(1 → N)`
```
iterate(asset, context, evaluators) → [spawn_1, spawn_2, ... spawn_N]
```
One stable asset fans out to N independent sub-graphs. Each spawn runs its own graph fragment.

Examples: one spec → N implementation tenants (Claude, Gemini, Codex). One design → N parallel feature builds.

The functor: `Broadcast(asset, spawn_configs[]) = [Spawn(sub_graph_i, asset, context_i)]`

---

**FOLD** `(N → 1)`
```
[asset_1, asset_2, ... asset_N] + merge_strategy → iterate(merged_asset, union(contexts))
```
N child convergences aggregated into one parent convergence. Merge strategy determines conflict resolution.

Examples: parallel feature builds fold back into integration. N reviewers' findings fold into one requirements document.

The functor: `Fold(assets[], merge_strategy) → iterate(merged_candidate, all_child_contexts[])`

**BROADCAST and FOLD are duals — every BROADCAST implies an eventual FOLD. This is not a convention; it is the adjunction BROADCAST ⊣ FOLD.**

---

**BUILD** `(N ↔ N co-evolution)`
```
iterate(asset_A, context + asset_B_state, evaluators_A)  ↔
iterate(asset_B, context + asset_A_state, evaluators_B)
until both stable
```
Two or more assets must converge simultaneously under mutual constraint. Each is Context[] for the other. Neither can converge without the other satisfying its evaluators.

Canonical instance: `code ↔ unit_tests` (TDD). Generalises to: schema ↔ migration, API ↔ client, spec ↔ verification.

The functor: `Build(asset_A, asset_B, cross_evaluators) = co_evolution(iterate_A, iterate_B)`

---

### Axis 2: Evaluator Structure

**CONSENSUS** `(F_H → MultiF_H)`
```
Consensus(edge, roster, quorum_rule) =
  iterate(asset, context, [F_H_p1, F_H_p2, ..., F_H_pN])
  where converged ⟺ quorum_rule(votes) = true
```
Replaces single F_H with N independent evaluators under a quorum rule. The quorum rule is the only new element — a function `votes[] → converged|not_converged`. Unanimous, majority, supermajority are three parameterisations of the same functor.

Public review = CONSENSUS applied at `intent→requirements`. Architecture committee = CONSENSUS applied at `design`. Same functor, different roster and quorum config.

**Note**: The spec currently has no model for this functor — it is GAP-1 from the public review analysis. Needs ADR-S-*.

---

**REVIEW** `(constructor → identity)`
```
Review(asset, evaluators) = iterate(asset, context, evaluators)
  where constructor = identity
```
`iterate()` with construction suppressed. The asset enters, evaluators run, a disposition is produced (approve / reject / needs_revision), but the asset does not change. Output is a signal, not a new asset version.

REVIEW is the degenerate case of iterate — delta computation only, no construction. Every code review, spec review, ADR review is this functor. It appears constantly but has no formal name in the current system.

---

### Axis 3: Convergence Criterion

**DISCOVERY** `(quality → question_answered)`
```
Discovery(question, time_box) =
  Spawn(sub_graph, context + question, convergence_type: question_answered)
  → fold_back(findings) when answered or time_box expires
```
Substitutes the convergence criterion. Instead of "all evaluators pass" (quality), stopping condition is "question answered" or time-box expires. Output is findings, not a production asset.

Spike and PoC are parameterisations of DISCOVERY — same functor, different time-box and question scope.

---

**RATIFY** `(convergence → stability promotion)`
```
Ratify(asset, gate) =
  Consensus(asset, roster, gate)
  → if converged: Promote(asset.stability: candidate → stable)
```
Consensus composed with a stability state change. Asset content doesn't change — Markov status does. A candidate that passes RATIFY becomes a stable object with a new boundary.

ADR acceptance, requirement locking, release approval are all RATIFY.

**RATIFY = CONSENSUS + Promote. It is derived, not primitive.**

---

**EVOLVE** `(stable → candidate → re-converge)`
```
Evolve(stable_asset, evolution_intent, version_constraint) =
  Demote(stable_asset → candidate_v_next)
  → iterate(candidate_v_next, context + evolution_intent + version_constraint, evaluators)
  → Promote if converged
```
Temporarily reverts a stable asset to candidate status, iterates under evolution constraints (backward compatibility, version semantics), re-promotes if convergence reached.

REQ-F-EVOL-001 (spec evolution pipeline) is EVOLVE applied to the requirements asset.

---

## The Complete Map

```
                    ┌─────────────────────────────────────────────┐
                    │           HIGHER-ORDER FUNCTORS              │
                    ├────────────────┬────────────────────────────┤
  Graph structure   │  BROADCAST     │  1 → N  (fan-out)          │
                    │  FOLD          │  N → 1  (fan-in)            │
                    │  BUILD         │  N ↔ N  (co-evolution)      │
                    ├────────────────┼────────────────────────────┤
  Evaluator shape   │  CONSENSUS     │  F_H → MultiF_H (quorum)   │
                    │  REVIEW        │  constructor → identity      │
                    ├────────────────┼────────────────────────────┤
  Convergence rule  │  DISCOVERY     │  quality → question answered│
                    │  RATIFY        │  convergence → stable status│
                    │  EVOLVE        │  stable → candidate → stable│
                    └────────────────┴────────────────────────────┘
```

Every specialised flow seen so far is a composition of 2-3 of these:
- Public review = `CONSENSUS(F_H, roster, quorum)` applied before requirements
- Discovery spike = `DISCOVERY(question, time_box)` spawned from any edge
- TDD = `BUILD(code, unit_tests, cross_evaluators)`
- ADR acceptance = `RATIFY(design_decision, architecture_committee)`
- Spec evolution = `EVOLVE(stable_requirements, new_intent)`

---

## The SDLC as a Functor Composition Expression

The current bootstrap graph, rewritten:

```
Genesis_SDLC =

  iterate(intent)                                  # bare iterate

  ∘ CONSENSUS(requirements, stakeholders, quorum)  # multi-party agreement before locking

  ∘ BROADCAST(requirements → features[])           # fan-out: 1 spec → N feature vectors

  ∘ for each feature:
      DISCOVERY?(spike)                            # optional — uncertain features only
      ∘ iterate(design)                            # bare iterate
      ∘ BUILD(code ↔ unit_tests)                  # TDD co-evolution
      ∘ REVIEW(uat_tests)                          # evaluation only, no construction

  ∘ FOLD(features[] → integration)                # fan-in: N features → 1 system

  ∘ RATIFY(release, approvers)                    # stability promotion gate

  ∘ iterate(telemetry → new_intent)               # homeostasis loop
```

**That expression IS the methodology.** The graph topology, edge configs, and profile variants are all derivable from it.

---

## What Changes: Derived Topology

**Today**: `graph_topology.yml` + 13 `edge_params/*.yml` files, hand-authored, maintained manually. New project variant = new topology file.

**With functor composition**: A project is a **composition expression + parameter bindings**. Different projects are different expressions or different bindings.

```yaml
# genesis_monitor.project.yml
composition:
  - iterate: intent
  - iterate: requirements          # no consensus — single author, small scope
  - broadcast: features
  - for_each:
      - build: [code, unit_tests]
      - review: uat_tests
  - fold: integration
  - ratify:
      gate: owner_approval
      quorum: unanimity
      roster: [jim]
```

```yaml
# open_standard.project.yml
composition:
  - iterate: intent
  - consensus:
      edge: requirements
      roster: working_group
      quorum: supermajority
      min_duration: 14d
  - broadcast: features
  - for_each:
      - discovery: {time_box: 3d}
      - build: [code, unit_tests]
  - fold: integration
  - ratify:
      gate: working_group_vote
      quorum: supermajority
```

The graph topology and edge params are **compiled** from the composition — not written by hand.

---

## What This Requires

**1. Functor Library** — each higher-order functor is a parameterised edge config template. CONSENSUS is a template: `(roster, quorum, min_duration) → edge_params`. BUILD is a template: `(asset_A, asset_B) → bidirectional_edge_pair`.

**2. Composition Compiler** — takes a composition expression + parameter bindings → generates `graph_topology.yml` + `edge_params/*.yml`. Pure function: deterministic, no LLM. F_D all the way.

**3. Profile = Composition Variant** — profiles stop being skip-lists on a fixed topology. A profile is a different composition expression or a different binding of the same expression. `poc` omits CONSENSUS and BROADCAST. `hotfix` is just BUILD. `full` includes DISCOVERY for every feature.

---

## Algebraic Properties

The methodology becomes algebraic. Provable before running:

- `BROADCAST ∘ FOLD = identity` (fan-out then fan-in returns same cardinality)
- `RATIFY ∘ CONSENSUS = RATIFY` (consensus is already in RATIFY — don't double it)
- `BUILD(A, B) = BUILD(B, A)` (co-evolution is symmetric)
- `DISCOVERY ∘ iterate ≠ iterate ∘ DISCOVERY` (order matters — discovery informs design)

Invalid compositions (cycles, missing fold after broadcast, ratify with no gate) are caught at **compile time**, not at runtime.

---

## Gap Evaluation Becomes Typed Functor Operations

**Currently**, the gap → intent path is informal:
```
gen-gaps observes delta
  → emits intent_raised (free text)
    → human decides what to do
      → manually invokes gen-iterate on some edge
```

**With functor composition**, a gap is a diff between the current composition and the target composition:

| Gap (current model) | Gap (functor model) |
|---------------------|---------------------|
| Layer 1: code file missing `Implements:` tag | `iterate(code)` present but `req_tags_in_code` evaluator not in its checklist |
| Layer 2: REQ-F-AUTH-002 has no test | `BUILD(code ↔ tests)` present but `unit_tests` evaluator doesn't cover this key |
| Layer 3: feature running without telemetry | homeostasis functor `iterate(telemetry → intent)` absent from composition |

The gap evaluator produces a **composition diff**, not a finding list.

**Typed intents** replace free-text findings:

```yaml
# Instead of: "REQ-F-AUTH-002 has no test"
intent_raised:
  op: PARAMETERISE
  functor: BUILD
  parameter: unit_tests.evaluators
  add: [req_f_auth_002_coverage]
  reason: "layer 2 gap — missing test coverage"
```

```yaml
# Instead of: "feature running without telemetry"
intent_raised:
  op: APPEND
  functor: iterate(telemetry → intent)
  after: RATIFY(release)
  reason: "layer 3 gap — homeostasis loop absent"
```

---

## The Homeostasis Loop Closes Algebraically

```
observe(composition)
  → delta(composition, target_composition)
    → typed_intent (functor_op)
      → validate(op, composition)           ← F_D, pure function
        → CONSENSUS(op, reviewers)?         ← if op affects shared spec
          → apply(op) → new_composition     ← composition compiler
            → derive(graph_topology)        ← F_D, pure function
              → observe(new_composition)    ← loop
```

Every step is deterministic (F_D) or has a clear evaluator type (F_P, F_H, CONSENSUS). The human approves a **typed operation**, not a free-text finding.

---

## The Three-Level System

```
Level 1 — Primitives:
  {Graph, Iterate, Evaluators, Spec+Context}
  The axioms. Unchanging.

Level 2 — Higher-Order Functors:
  {BROADCAST, FOLD, BUILD, CONSENSUS, REVIEW, DISCOVERY, RATIFY, EVOLVE}
  The vocabulary. Composed from primitives.

Level 3 — Project Composition:
  expression over Level 2 functors + parameter bindings
  The program. Different per project/domain.
```

Gap evaluation operates at Level 3 — diffs the current program against the target program, produces typed Level 2 operations as intents. The compiler validates and applies them.

**The methodology can repair itself using the same formal system it uses to build software.**

---

## Spec Implication

The current spec describes *one* graph (the SDLC bootstrap graph) with zoom profiles. The higher-order functor model says the spec should instead describe:

1. The **functor library** — the 8 higher-order functors with type signatures
2. The **composition algebra** — rules for valid compositions
3. **Example compositions** — SDLC, open standard, research project, hotfix

The SDLC bootstrap graph becomes an *example*, not the privileged topology. Any domain can compose its own methodology from the same library.

This is the difference between describing one process and describing a **process algebra**.

---

## Recommended Action

1. Write the functor library spec using Fong & Spivak string diagram notation (see companion STRATEGY post)
2. Implement the composition compiler as a pure F_D function
3. Rewrite `graph_topology.yml` as a derived artifact from `genesis_sdlc.project.yml`
4. Add CONSENSUS to the spec (ADR-S-*) — it is the one functor with no current formal backing
5. Run van der Aalst's 43 patterns against the 8 functors for completeness (see companion STRATEGY post)
