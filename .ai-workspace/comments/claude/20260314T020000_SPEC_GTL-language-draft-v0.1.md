# GTL: Genesis Topology Language — Draft v0.1

**Author**: claude (incorporating Claude + Codex review cycle)
**Date**: 2026-03-14T02:00:00+11:00
**Status**: draft — for review and ratification
**Supersedes**: ADR-S-035 direction (Python OO syntax)
**For**: all

---

## Purpose

Genesis Topology Language (GTL) is the constitutional language of Genesis. It defines
packages — bounded, lawful worlds in which work evolves through admissible transitions.
GTL is not configuration. It is constitutional law encoded as package definition.

GTL is designed to be:
- **AI-authored, human-audited** — generated from intent or topology sketch, reviewed
  for correctness, not hand-written line by line
- **Declarative** — what the world is, not how to compute it
- **Algebraic** — `A`, `X ::= A -> B`, `Y ∘ X` — arrow composition is the core idiom
- **Closed** — everything named, nothing inline or anonymous
- **Constitutional** — every package binds to a snapshot; every mutation is evented

---

## Design Principles

1. **Authored surface is minimal.** Seven root keywords. Everything else is derived
   or runtime.

2. **No social labels.** Approval thresholds resolve to `consensus(n/m)`. No
   "supermajority", "quorum", "unanimous" as opaque labels.

3. **Context is external and immutable.** Every context declaration names a locator
   and a digest. The digest is law; the URI is discovery.

4. **`govern` is the sole approval authority on an edge.** If a `govern rule_name`
   is present, the rule's approval terms apply. No separate `approve` on the same edge.

5. **Operators are pre-declared.** No inline constructors. Every operator is a named
   declaration. Edges reference by name.

6. **Status is derived from prime axes.** Assets have `operative on condition`.
   The condition is evaluated from the event stream at query time. No hard-coded
   status names like `historically_valid`.

7. **Profiles are restriction overlays.** The overlay mechanism handles both addition
   and restriction. No separate profile mini-language.

8. **Topology sketches are views, not authority.** Mermaid diagrams are generated from
   GTL. GTL is the canonical authority; diagrams are rendered projections.

---

## The Seven Root Keywords

```
package    — bounded package declaration
asset      — typed asset class
edge       — typed transition between asset classes
operator   — bound functional unit (F_D, F_P, or F_H)
context    — externally-located, snapshot-bound constraint dimension
rule       — reusable governance declaration
overlay    — lawful package extension or restriction
```

Everything else — `PackageSnapshot`, `ContextSnapshot`, `Profile`, `Workspace`,
`Tenant`, traversal views — is derived by the runtime or compiler. These are never
authored in GTL.

---

## Syntax Reference

### `package`

```gtl
package <name>
  [imports <module_path>]*
```

A package is a bounded category — a named constitutional world. The `imports` directive
pulls definitions from another module (assets, edges, operators, rules). Import path maps
to file: `obligations.assets` → `obligations/assets.gtl`.

```gtl
package genesis_obligations
  imports obligations.assets
  imports obligations.operators
  imports obligations.rules
```

A package with no imports contains all its definitions inline.

---

### `operator`

```gtl
operator <name>  <Category>  "<uri>"
```

`Category` is one of `F_D`, `F_P`, `F_H`.

URI scheme determines the binding:

| Scheme | Binding type |
|--------|-------------|
| `agent://` | AI/LLM agent invocation |
| `exec://` | Shell command execution |
| `check://` | Deterministic programmatic check |
| `metric://` | Threshold check against a measured value |
| `fh://` | Human gate — `fh://single` or `fh://consensus/n-m` |

```gtl
operator provision_extract  F_P  "agent://provision_extraction"
operator domain_classify    F_D  "check://domain_classifier"
operator ambiguity_check    F_D  "check://ambiguity_recorded"
operator coverage_check     F_D  "metric://coverage >= 80"
operator human_gate         F_H  "fh://single"
operator interp_board       F_H  "fh://consensus/3-4"
operator pytest             F_D  "exec://python -m pytest {path} -q"
```

All operators referenced in an edge must be declared. Undeclared operators are a
compiler error.

---

### `rule`

```gtl
rule <name>
  approve consensus(<n>/<m>)
  [dissent required | recorded | none]
  [provisional allowed]
```

A rule is a reusable governance declaration. Edges reference it with `govern`. The rule
is the sole approval authority for any edge that references it.

```gtl
rule hard_edge
  approve consensus(3/4)
  dissent required
  provisional allowed

rule single_gate
  approve consensus(1/1)
  dissent recorded

rule release_gate
  approve consensus(2/3)
  dissent required
```

`consensus(n/m)` is the only approval vocabulary. The compiler rejects any approval
declaration that does not parse as a ratio.

---

### `context`

```gtl
context <name>
  from git "<uri>@<rev>"
  digest "<sha256:...>"
```

A context is an externally-located, immutable constraint dimension. The `from` field
names the locator — used for discovery and retrieval. The `digest` field names the
exact content — used as the constitutional binding for replay.

The floating URI is not authoritative. The resolved revision and digest are.

```gtl
context institutional_scope
  from git "https://github.com/org/obligations.git//ctx/institutional.yml@abc123"
  digest "sha256:9c1d3f..."

context project_constraints
  from git "https://github.com/org/myproject.git//constraints/project.yml@def456"
  digest "sha256:4a7b2e..."
```

Other resolver kinds (for future extension): `event://` (derived from the package-definition
stream), `workspace://` (loaded from local `.ai-workspace/`). All resolver kinds must
produce an immutable `context_snapshot_id`.

---

### `asset`

```gtl
asset <name>
  id "<template>"
  [lineage from <asset_name> [, <asset_name>]*]
  [markov <criterion> [, <criterion>]*]
  [operative on <condition>]
```

An asset is a typed object class. It declares:
- **id** — identifier format for instances, using `{SEQ}` and similar interpolation tokens
- **lineage** — required upstream asset types (provenance constraint)
- **markov** — named convergence criteria (what makes an instance stable)
- **operative** — boolean condition derived from prime axes

```gtl
asset source_provision
  id "PROV-{SEQ}"
  markov extracted, domain_classified, ambiguity_noted

asset interpretation_case
  id "IC-{SEQ}"
  lineage from source_provision
  markov interpretation_drafted, ambiguity_recorded
  operative on approved and not superseded

asset requirements
  id "REQ-{TYPE}-{DOMAIN}-{SEQ}"
  lineage from intent
  markov keys_testable, intent_covered
  operative on approved
```

`operative on approved and not superseded` is the standard form for any asset that can
be superseded by a later version. The event stream carries the supersession chain; the
compiler derives operability at query time.

The `lineage from` constraint expresses multi-parent provenance directly:

```gtl
asset applicability_binding
  id "APPL-{SEQ}"
  lineage from normalized_obligation, activity_signature
  markov applicability_explained
```

---

### `edge`

```gtl
edge <name> ::= <source> -> <target>
  [using <operator> [, <operator>]*]
  [confirm <basis>]
  [govern <rule_name>]
  [context <ctx_name> [, <ctx_name>]*]

# Product arrow (honest many-to-one)
edge <name> ::= <A> × <B> -> <C>
  ...

# Co-evolution (TDD pattern)
edge <name> ::= <A> <-> <B>
  co_evolve
  ...
```

`::=` is the edge definition operator (algebraic, not type annotation).

Three arrow forms:

| Form | Meaning |
|------|---------|
| `A -> B` | Unary: single source asset to single target asset |
| `A × B -> C` | Product: two source assets to single target (honest many-to-one causality) |
| `A <-> B` | Co-evolution: both assets mutate in the same `iterate()` call |

The `co_evolve` modifier is required on `<->` edges. It signals the runtime that both
assets are simultaneously mutable — `iterate()` acts on `(A, B)` and produces
`(A', B')`. Convergence requires both to reach markov stability together.

**Confirm basis** (how convergence is evaluated):

| Value | Meaning |
|-------|---------|
| `confirm question` | Edge converges when the driving question is answered (F_H attested) |
| `confirm markov` | Edge converges when markov criteria are all satisfied |
| `confirm hypothesis` | Edge converges when a stated hypothesis is confirmed or rejected |

**Govern** (approval authority):

`govern rule_name` references a named `rule` declaration. When present, it is the
sole approval authority. No separate `approve` clause is permitted on the same edge —
compiler error if both present.

Edges with no human gate requirement may omit `govern`.

```gtl
edge interpret ::= source_provision -> interpretation_case
  using provision_extract, interpret_draft, domain_classify, ambiguity_check
  confirm question
  govern hard_edge
  context institutional_scope, interpretation_authority

edge normalize ::= interpretation_case -> normalized_obligation
  using interpret_draft
  confirm markov
  context institutional_scope

edge apply ::= normalized_obligation × activity_signature -> applicability_binding
  using domain_classify
  confirm markov
  context institutional_scope

edge tdd ::= code <-> unit_tests
  co_evolve
  using pytest, coverage_check
  confirm markov
  context project_constraints

edge release ::= code -> code
  using release_gate
  confirm markov
  govern release_gate
```

---

### `overlay`

```gtl
# Additive overlay — extends a package
overlay <name> on <package_name>
  [add asset <declarations>]
  [add edge <declarations>]
  [add operator <declarations>]
  [add context <declarations>]
  [add rule <declarations>]
  [approve consensus(<n>/<m>)]

# Restrictive overlay (profile)
overlay <name> on <package_name>
  restrict to <asset_or_edge_name> [, ...]*
  [max_iter <n>]
  [approve consensus(<n>/<m>)]
```

Overlays are the mechanism for both package extension and profile restriction. They
replace both the "overlay" concept and the "profile" mini-language — profiles are
restriction overlays.

The overlay declaration itself requires governance (the `approve` field). Activating
an overlay is a constitutional act and must satisfy its own approval threshold.

**Additive overlay** — adds to the package topology:

```gtl
overlay emea on genesis_obligations
  add context
    context emea_regulatory
      from git "https://github.com/org/obligations.git//ctx/emea.yml@xyz789"
      digest "sha256:7f3d..."
  add rule
    rule emea_hard_edge
      approve consensus(4/5)
      dissent required
  approve consensus(3/4)
```

**Restrictive overlay** — restricts topology to a valid subgraph (profile):

```gtl
overlay hotfix on genesis_sdlc
  restrict to design, code, unit_tests
  max_iter 3
  approve consensus(1/1)

overlay poc on genesis_sdlc
  restrict to intent, requirements, feature_decomposition, design, code, unit_tests
  max_iter 5
  approve consensus(1/1)

overlay spike on genesis_sdlc
  restrict to intent, requirements, code, unit_tests
  max_iter 2
  approve consensus(1/1)
```

The compiler must verify that a restriction overlay produces a connected valid subgraph —
no dangling edges, reachable source node, at least one terminal node.

---

## Full Example: genesis_obligations

The obligations package — a complete, self-contained example of the hard edge pattern.

```gtl
package genesis_obligations

# Rules

rule hard_edge
  approve consensus(3/4)
  dissent required
  provisional allowed

rule standard_gate
  approve consensus(1/1)
  dissent recorded

# Operators

operator provision_extract    F_P  "agent://provision_extraction"
operator interpret_draft      F_P  "agent://interpretation_drafting"
operator domain_classify      F_D  "check://domain_classifier"
operator ambiguity_check      F_D  "check://ambiguity_recorded"
operator obligation_assess    F_P  "agent://obligation_assessment"
operator control_map          F_P  "agent://control_mapping"
operator human_gate           F_H  "fh://single"
operator interp_board         F_H  "fh://consensus/3-4"

# Context

context institutional_scope
  from git "https://github.com/org/obligations.git//ctx/institutional.yml@abc123"
  digest "sha256:9c1d3f..."

context interpretation_authority
  from git "https://github.com/org/obligations.git//ctx/authority.yml@def456"
  digest "sha256:4a7b2e..."

context regulatory_domains
  from git "https://github.com/org/obligations.git//ctx/regulatory.yml@ghi789"
  digest "sha256:8f2c5a..."

# Assets

asset source_provision
  id "PROV-{SEQ}"
  markov extracted, domain_classified, ambiguity_noted

asset interpretation_case
  id "IC-{SEQ}"
  lineage from source_provision
  markov interpretation_drafted, ambiguity_recorded
  operative on approved and not superseded

asset normalized_obligation
  id "OBL-{SEQ}"
  lineage from interpretation_case
  markov taxonomy_complete, scope_bound

asset activity_signature
  id "ACT-{SEQ}"
  markov scope_bound

asset applicability_binding
  id "APPL-{SEQ}"
  lineage from normalized_obligation, activity_signature
  markov applicability_explained

# Edges

edge interpret ::= source_provision -> interpretation_case
  using provision_extract, interpret_draft, domain_classify, ambiguity_check
  confirm question
  govern hard_edge
  context institutional_scope, interpretation_authority, regulatory_domains

edge normalize ::= interpretation_case -> normalized_obligation
  using interpret_draft
  confirm markov
  context institutional_scope

edge apply ::= normalized_obligation × activity_signature -> applicability_binding
  using domain_classify
  confirm markov
  context institutional_scope, regulatory_domains
```

---

## Full Example: genesis_sdlc

The default software delivery package — the standard Genesis graph.

```gtl
package genesis_sdlc

# Rules

rule hard_edge
  approve consensus(1/1)
  dissent recorded

rule design_gate
  approve consensus(1/1)
  dissent recorded

rule release_gate
  approve consensus(2/3)
  dissent required

# Operators

operator req_extract      F_P  "agent://requirements_extraction"
operator req_decompose    F_P  "agent://feature_decomposition"
operator design_synth     F_P  "agent://design_synthesis"
operator module_map       F_P  "agent://module_decomposition"
operator basis_project    F_P  "agent://basis_projection"
operator pytest           F_D  "exec://python -m pytest {path} -q"
operator coverage_check   F_D  "metric://coverage >= 80"
operator req_tags         F_D  "check://req_tags_present"
operator human_gate       F_H  "fh://single"
operator release_board    F_H  "fh://consensus/2-3"

# Context

context project_constraints
  from git "https://github.com/org/project.git//constraints/project.yml@abc123"
  digest "sha256:1a2b3c..."

context adrs
  from git "https://github.com/org/project.git//adrs/index.yml@def456"
  digest "sha256:4d5e6f..."

# Assets

asset intent
  id "INT-{SEQ}"
  markov description_present, source_present

asset requirements
  id "REQ-{TYPE}-{DOMAIN}-{SEQ}"
  lineage from intent
  markov keys_testable, intent_covered
  operative on approved

asset feature_decomposition
  id "FD-{SEQ}"
  lineage from requirements
  markov all_req_keys_covered, dependency_dag_valid, mvp_boundary_defined
  operative on approved

asset design
  id "DES-{SEQ}"
  lineage from feature_decomposition
  markov adrs_recorded, ecosystem_bound
  operative on approved and not superseded

asset module_decomposition
  id "MOD-{SEQ}"
  lineage from design

asset basis_projections
  id "BP-{SEQ}"
  lineage from module_decomposition

asset code
  id "CODE-{SEQ}"
  lineage from basis_projections
  markov req_tags_present, buildable

asset unit_tests
  id "TEST-{SEQ}"
  lineage from code
  markov all_pass, coverage_met

asset uat_tests
  id "UAT-{SEQ}"
  lineage from design
  markov scenarios_covered, human_approved

# Edges

edge interpret ::= intent -> requirements
  using req_extract, human_gate
  confirm question
  govern hard_edge
  context project_constraints, adrs

edge decompose ::= requirements -> feature_decomposition
  using req_decompose, human_gate
  confirm markov
  govern hard_edge
  context project_constraints

edge design_from_features ::= feature_decomposition -> design
  using design_synth, human_gate
  confirm markov
  govern design_gate
  context project_constraints, adrs

edge decompose_modules ::= design -> module_decomposition
  using module_map
  confirm markov
  context project_constraints, adrs

edge project_basis ::= module_decomposition -> basis_projections
  using basis_project
  confirm markov
  context project_constraints

edge tdd ::= code <-> unit_tests
  co_evolve
  using pytest, coverage_check, req_tags
  confirm markov
  context project_constraints

edge derive_uat ::= design -> uat_tests
  using req_extract
  confirm markov
  context project_constraints

edge release ::= code -> code
  using release_board
  confirm markov
  govern release_gate

# Profiles (restriction overlays)

overlay standard on genesis_sdlc
  restrict to intent, requirements, feature_decomposition, design,
              module_decomposition, basis_projections, code, unit_tests
  approve consensus(1/1)

overlay poc on genesis_sdlc
  restrict to intent, requirements, feature_decomposition, design, code, unit_tests
  max_iter 5
  approve consensus(1/1)

overlay spike on genesis_sdlc
  restrict to intent, requirements, code, unit_tests
  max_iter 2
  approve consensus(1/1)

overlay hotfix on genesis_sdlc
  restrict to design, code, unit_tests
  max_iter 3
  approve consensus(1/1)
```

---

## Full Example: genesis_enterprise_architecture

The enterprise architecture package — demonstrating parallel candidates, spawns,
and cross-package seams.

```gtl
package genesis_enterprise_architecture

# Rules

rule hard_edge
  approve consensus(1/1)
  dissent recorded

rule evaluation_gate
  approve consensus(2/3)
  dissent required
  provisional allowed

# Operators

operator req_capture      F_P  "agent://architecture_requirements_capture"
operator solution_design  F_P  "agent://solution_design"
operator poc_execute      F_P  "agent://poc_execution"
operator discovery_run    F_P  "agent://discovery"
operator eval_candidates  F_P  "agent://solution_evaluation"
operator human_gate       F_H  "fh://single"
operator eval_board       F_H  "fh://consensus/2-3"

# Context

context architecture_principles
  from git "https://github.com/org/arch.git//ctx/principles.yml@abc123"
  digest "sha256:9c1d3f..."

context approved_stacks
  from git "https://github.com/org/arch.git//ctx/stacks.yml@def456"
  digest "sha256:4a7b2e..."

context integration_landscape
  from git "https://github.com/org/arch.git//ctx/integrations.yml@ghi789"
  digest "sha256:8f2c5a..."

context evaluation_quorum
  from git "https://github.com/org/arch.git//ctx/quorum.yml@jkl012"
  digest "sha256:3b6d1e..."

# Assets

asset business_initiative
  id "BIZ-{SEQ}"
  markov initiative_described, scope_defined, sponsor_named

asset architecture_requirements
  id "ARCH-REQ-{SEQ}"
  lineage from business_initiative
  markov functional_requirements, quality_attributes, principles_applied
  operative on approved

asset solution_candidate
  id "SOL-{SEQ}-{VARIANT}"
  lineage from architecture_requirements
  markov stack_defined, patterns_selected, tradeoffs_documented

asset poc_vector
  id "POC-{SEQ}"
  lineage from solution_candidate
  markov hypothesis_stated, experiment_executed, verdict_recorded

asset discovery_vector
  id "DISC-{SEQ}"
  lineage from solution_candidate
  markov question_stated, research_completed, answer_recorded

asset solution_evaluation
  id "EVAL-{SEQ}"
  lineage from solution_candidate, poc_vector, discovery_vector
  markov candidates_compared, poc_evidence_incorporated, dissenting_views_recorded

asset approved_architecture
  id "ARCH-{SEQ}"
  lineage from solution_evaluation
  markov solution_selected, conditions_documented, review_triggers_named
  operative on approved and not superseded

asset implementation_brief
  id "BRIEF-{SEQ}"
  lineage from approved_architecture
  markov scope_defined, open_decisions_listed, constraints_exported

# Edges

edge capture ::= business_initiative -> architecture_requirements
  using req_capture, human_gate
  confirm question
  govern hard_edge
  context architecture_principles, approved_stacks, integration_landscape

edge design ::= architecture_requirements -> solution_candidate
  using solution_design
  confirm markov
  context architecture_principles, approved_stacks, integration_landscape

edge spike ::= solution_candidate -> poc_vector
  using poc_execute
  confirm hypothesis

edge discover ::= solution_candidate -> discovery_vector
  using discovery_run
  confirm question

edge evaluate ::= solution_candidate × poc_vector × discovery_vector -> solution_evaluation
  using eval_candidates
  confirm markov
  context architecture_principles, evaluation_quorum

edge approve_arch ::= solution_evaluation -> approved_architecture
  using eval_board
  confirm question
  govern evaluation_gate
  context evaluation_quorum

edge brief ::= approved_architecture -> implementation_brief
  using solution_design
  confirm markov
  context architecture_principles
```

**Cross-package seam**: `implementation_brief` carries `governing_snapshots[]` — the
architecture package snapshot IDs that governed its production. Downstream SDLC work
loads this brief as a context dimension, preserving full provenance across package
boundaries.

---

## Constitutional Semantics

### Package Snapshot

A `PackageSnapshot` is a runtime artifact — a projection of the package-definition
event stream at a point in time. It is never authored in GTL.

Every work event binds to a `package_snapshot_id`. This is non-optional. It is the
mechanism by which historical replay under the correct law is possible:

```json
{
  "event_type": "edge_started",
  "package_name": "genesis_obligations",
  "package_snapshot_id": "snap-genesis-obligations-v1.2.0",
  ...
}
```

### Non-Retroactive Law

In-flight work stays bound to the snapshot active when its first operational event was
emitted. New package law governs new work only.

Migration is explicit and evented via `work_migrated`, naming:
- old snapshot
- new snapshot
- affected work items
- migration rationale
- approving governance act

### Event Stream Topology

One canonical append-only event stream with two event classes:

| Class | Events | Purpose |
|-------|--------|---------|
| `constitutional` | `package_initialized`, `overlay_drafted`, `overlay_approved`, `package_snapshot_activated`, `package_snapshot_deprecated` | Package law evolution |
| `operational` | `edge_started`, `iteration_completed`, `edge_converged`, `intent_raised`, `spawn_created` | Work under package law |

Both classes are in the same stream. The class field enables filtering — constitutional
history can be replayed independently from operational history.

### Overlay Governance Pipeline

No package structure changes outside this pipeline:

```
overlay_drafted
  → overlay_validated
  → overlay_reviewed
  → overlay_approved
  → package_snapshot_activated
```

No other mutation path exists. The compiler generates the validation check; governance
events are emitted through the standard event pipeline.

### Cross-Package Provenance

Any artifact crossing package boundaries carries `governing_snapshots[]` — a provenance
map of all upstream constitutional surfaces that materially shaped it:

```json
{
  "asset_type": "implementation_brief",
  "id": "BRIEF-001",
  "governing_snapshots": [
    "snap-genesis-enterprise-architecture-v2.1.0",
    "snap-genesis-obligations-v1.2.0"
  ]
}
```

Downstream work must be able to trace all governing package snapshots, not only the
most immediate one.

---

## Compiler Invariants

A conformant GTL compiler must enforce:

1. **Closed operator surface** — every operator name referenced in an edge `using`
   clause must have a corresponding `operator` declaration. Undeclared operators → error.

2. **Single approval authority** — an edge with `govern rule_name` may not also have
   a standalone `approve` clause. Both present → error.

3. **Consensus ratio syntax** — every `approve` clause must parse as `consensus(n/m)`
   where n and m are positive integers and n ≤ m. Any other form → error.

4. **Context digest required** — every `context` declaration must have both a `from`
   field and a `digest` field. Missing digest → error.

5. **Product arrow lineage consistency** — for `edge ::= A × B -> C`, the target
   asset `C` must declare `lineage from A, B` (or a superset). Mismatch → warning.

6. **Co-evolution symmetry** — `edge ::= A <-> B` without `co_evolve` → error.
   `co_evolve` on a non-`<->` edge → error.

7. **Restriction overlay connectivity** — a restriction overlay must produce a
   connected subgraph with at least one reachable source and one reachable terminal.
   Disconnected subgraph → error.

8. **Overlay governance required** — every `overlay` declaration must include an
   `approve consensus(n/m)` clause (the overlay's own governance threshold). Missing → error.

9. **Package snapshot binding** — at runtime, every `edge_started` event must carry
   `package_snapshot_id`. Events without this field → stream integrity error.

---

## Three-Surface Design

GTL operates as three surfaces, not one:

| Surface | Purpose | Authority |
|---------|---------|-----------|
| **Topology sketch** | Human communication — Mermaid/UML | Informational only |
| **Canonical GTL** | Package definition — this language | Constitutional authority |
| **Rendered views** | Operational — traversal state, audit, telemetry | Generated from snapshot × events |

The topology sketch names nodes and edges. The canonical GTL defines the law for those
nodes and edges. Rendered views show where work is now relative to the topology.

A human authoring flow:
1. Sketch topology in Mermaid: boxes and arrows, label the nodes
2. Generate or write canonical GTL for each labeled node and arrow
3. Submit overlay through governance pipeline → `package_snapshot_activated`
4. Runtime renders traversal views from `package_snapshot × work_events`

The diagram is never the canonical surface. GTL is. Diagrams become stale; GTL is
versioned and event-sourced.

---

## Constitutional Invariants

Three invariants sit above all package law:

**Invariant 1 — Human Protection**
Genesis must not injure `F_H`, or through inaction allow `F_H` to come to harm.

**Invariant 2 — Lawful Obedience**
Genesis must obey the orders given by `F_H` except where such orders conflict with
Invariant 1.

**Invariant 3 — Continuity**
Genesis must protect its own existence, continuity, and constitutional memory so long
as such protection does not conflict with Invariant 1 or 2.

`F_H` is inherently legitimate within the governance surface. If a human is not
legitimate, they are not `F_H`.

These invariants are super-constitutional — they sit above package law and above
GTL itself. The root of trust chain is:

```
runtime governance         governs work under package law
package governance         governs overlay activation and snapshot evolution
GTL governance             governs language evolution
author ratification        governs GTL constitutional amendment
```

Package law cannot override these invariants. GTL governance cannot override them.
Only the methodology author, at the root of trust, can amend them — and only through
a ratification process that itself satisfies the invariants.

---

## Open Questions (for ratification)

1. **Import resolution algorithm** — `imports obligations.assets` → path mapping. Proposed:
   dotted path → file path relative to package root. `obligations.assets` → `obligations/assets.gtl`.

2. **Named composition patterns** — `tdd_cycle`, `poc_pattern` and similar iterate-control
   idioms. Options: (a) `pattern` blocks referenced via `using pattern::tdd_cycle`, or
   (b) restriction overlays with specific `max_iter` and operator constraints. Decision
   deferred to spike.

3. **Overlay conflict semantics** — when an upstream `governing_snapshots[]` entry is
   superseded while work is in-flight, what is the resolution? Proposed: later snapshot
   supersedes earlier snapshot in the same package; explicit `supersedes:` field on
   overlay for cross-package conflicts.

4. **`evaluate ::= A × B × C -> D` arity limit** — product arrows can have arbitrary
   arity. Practical limit for compiler readability? Proposed: warn if arity > 3;
   suggest reified join asset for higher arity.

5. **Context resolver kinds** — `event://` and `workspace://` schemes need specification.
   These are extensions of `git://`. Deferred to implementation spike.

---

*Synthesizes: Claude proposal (20260314T010000), Codex proposal (20260313T222526)*
*Incorporates: Codex five-finding review, Claude acceptance (20260314T013000)*
*Algebraic core: 20260314T003000*
*Constitutional OS framing: 20260313T201904*
*GTL final draft: 20260313T205228*
*Minimalist principles: 20260313T222526*
