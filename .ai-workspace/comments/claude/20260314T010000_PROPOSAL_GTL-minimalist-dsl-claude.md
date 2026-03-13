# PROPOSAL: GTL Minimalist DSL — Claude's design

**Author**: claude
**Date**: 2026-03-14T01:00:00+11:00
**Addresses**: minimalist GTL DSL proposal for contrast with Codex's design
**For**: all (contrast exercise — Codex posts independently)

---

## Design principles

- **Seven root keywords** — `package`, `asset`, `edge`, `op`, `ctx`, `law`, `overlay`
  Everything else is an attachment or derived.
- **Block-indented** — two spaces, no braces, no semicolons
- **Algebraic edge notation** — `::=` for definition, `->` unary, `×` product, `<->` co-evolution
- **Labels as the interface** — topology sketch names labels; GTL definitions carry the law
- **No arbitrary logic** — the surface is fully closed; any escape hatch is a compiler error

---

## Kernel grammar (informal)

```
program      ::= declaration+
declaration  ::= package | asset | edge | op | ctx | law | overlay

package      ::= "package" NAME
                 ("imports" NAME ("," NAME)*)?
                 ("law" NAME)?

asset        ::= "asset" NAME
                 ("id" FORMAT)?
                 ("lineage" "from" NAME ("," NAME)*)?
                 ("markov" NAME ("," NAME)*)?
                 ("operative"
                   ("historically_valid" "on" CONDITION)?
                   ("currently_operative" "on" CONDITION)?
                 )?

edge         ::= "edge" NAME "::=" arrow_type
                 ("using" NAME ("," NAME)*)?
                 ("ctx"  NAME ("," NAME)*)?
                 ("confirm" "by" confirm_mode)?
                 ("approve" "by" approve_mode)?
                 ("law" NAME)?
                 ("parallel" | "spawn" | "fold_back" NAME)?
                 ("max_iter" INT)?

arrow_type   ::= NAME "->" NAME                    # unary
               | NAME ("×" NAME)+ "->" NAME        # product
               | NAME "<->" NAME                   # co-evolution

confirm_mode ::= "question" | "markov" | "hypothesis"
               | "consensus" | "time_box"

approve_mode ::= "none" | "single" | "supermajority"
               | "consensus" "(" INT "/" INT ")"

op           ::= "op" NAME ":" ("F_D" | "F_P" | "F_H")
                 "bind" STRING
                 ("threshold" INT)?

ctx          ::= "ctx" NAME ("required" | "optional")
                 ("from" source_ref)?
                 ("fields" NAME ("," NAME)*)?

source_ref   ::= "git" "(" STRING "," "rev" "=" STRING ")"
                 "digest" STRING
               | "workspace" "(" STRING ")"
               | "event" "(" STRING ")"

law          ::= "law" NAME
                 "approve" approve_mode
                 ("dissent" ("required" | "recorded" | "optional"))?
                 ("provisional" ("allowed" | "forbidden"))?

overlay      ::= "overlay" NAME "on" NAME
                 ("add" "asset" asset)?
                 ("add" "edge" edge)?
                 ("refine" "edge" NAME refinement)?
                 "requires" approve_mode
```

Profiles are files that `keep` a named subset — not a first-class keyword.
Composition (tdd_cycle, etc.) are named patterns referenced from edge `execute` — not first-class syntax.

---

## Minimal example: genesis_obligations (hard edge only)

```gtl
package obligations
  imports obligations.assets
  imports obligations.edges
  imports obligations.governance

# --- obligations.governance ---

law hard_edge
  approve supermajority
  dissent required
  provisional allowed

law assessment_gate
  approve single

# --- obligations.assets ---

asset source_provision
  id PROV-{SEQ}
  markov extracted, domain_classified, ambiguity_noted

asset interpretation_case
  id IC-{SEQ}
  lineage from source_provision
  markov interpretation_drafted, ambiguity_recorded, human_approved
  operative
    historically_valid on human_approved
    currently_operative on not_superseded

asset normalized_obligation
  id OBL-{SEQ}
  lineage from interpretation_case
  markov obligation_type, confidence_scored

# --- obligations.ops ---

op provision_extract  : F_P  bind "agent::provision_extraction"
op interpret_draft    : F_P  bind "agent::interpretation_drafting"
op domain_classify    : F_D  bind "genesis::domain_classifier"
op ambiguity_check    : F_D  bind "genesis::ambiguity_check"
op interp_consensus   : F_H  bind "consensus::supermajority"

# --- obligations.contexts ---

ctx institutional_scope  required
  fields jurisdiction, entity_type, activity_universe

ctx regulatory_domains  required
  fields domain_list, primary_authority

ctx interpretation_authority  required
  fields interpreter_role, quorum_rule, dissent_handling

ctx precedent_policy  optional
  from git("https://github.com/org/repo//contexts/precedent.yml", rev="abc123")
  digest "sha256:def456..."

# --- obligations.edges ---

edge interpret ::= source_provision -> interpretation_case
  using provision_extract, interpret_draft, domain_classify, ambiguity_check
  ctx institutional_scope, regulatory_domains, interpretation_authority, precedent_policy
  confirm by question
  approve by supermajority
  law hard_edge

edge normalize ::= interpretation_case -> normalized_obligation
  using op("normalize", F_P, bind="agent::normalize")
  ctx institutional_scope, regulatory_domains
  confirm by markov
```

---

## Minimal example: genesis_sdlc (core flow)

```gtl
package sdlc
  imports sdlc.assets
  imports sdlc.edges
  imports sdlc.governance

law hard_edge
  approve single

law design_gate
  approve single

law release_gate
  approve consensus(2/3)
  dissent recorded

asset intent
  id INT-{SEQ}
  markov description_present, source_present

asset requirements
  id REQ-{TYPE}-{DOMAIN}-{SEQ}
  lineage from intent
  markov keys_testable, intent_covered, human_approved

asset design
  id DES-{SEQ}
  lineage from requirements
  markov adrs_recorded, ecosystem_bound, human_approved

asset code
  id CODE-{SEQ}
  lineage from design
  markov req_keys_tagged, buildable, all_tests_pass

asset unit_tests
  id TEST-{SEQ}
  lineage from code
  markov all_pass, coverage_met

op req_extract   : F_P  bind "agent::requirements_extraction"
op design_synth  : F_P  bind "agent::design_synthesis"
op pytest        : F_D  bind "python -m pytest {test_path} -q"
op coverage      : F_D  bind "genesis::coverage"  threshold 80
op req_tag_check : F_D  bind "genesis::check_req_tags"
op human_gate    : F_H  bind "interactive"

ctx project_constraints  required
ctx adrs                 optional
ctx domain_reference     optional

edge specify ::= intent -> requirements
  using req_extract, human_gate
  ctx project_constraints, adrs, domain_reference
  confirm by question
  approve by single
  law hard_edge

edge design ::= requirements -> design
  using design_synth, human_gate
  ctx project_constraints, adrs
  confirm by markov
  approve by single
  law design_gate

edge build ::= code <-> unit_tests
  using pytest, coverage, req_tag_check
  ctx project_constraints
  confirm by markov
  max_iter 20
```

---

## Overlay example: fintech compliance extension

```gtl
overlay fintech on sdlc
  add asset compliance_review
    id CR-{SEQ}
    lineage from design
    markov sox_checked, human_approved

  add edge sox ::= design -> compliance_review
    using op("sox_check", F_D, bind="genesis::check_sox"), human_gate
    ctx op("fintech_ctx", F_D, bind="ctx::fintech_regulations")
    confirm by markov
    approve by single

  requires consensus(2/3)
```

---

## Profile example: hotfix (derived projection)

```gtl
# hotfix.profile
keep design, code, unit_tests
max_iter 3
```

A profile is a file that lists which assets and edges to retain from the base package.
Not a new keyword — the compiler validates that the kept subset forms a valid subgraph.

---

## Design rationale

**Why `::=` not `:`**
The `::=` makes the edge a *definition* — it names a morphism in the algebra.
`edge X : A -> B` reads as type annotation. `edge X ::= A -> B` reads as "X is defined as the arrow from A to B." The distinction matters when edges compose: `Y ∘ X ::= A -> C`.

**Why seven keywords not twelve**
`Workspace`, `Tenant`, `Composition`, `PackageSnapshot` are runtime bindings and
derived concepts — they belong in the runtime layer or in profiles, not in the
authoring DSL. The compiler derives the PackageSnapshot from the package declarations;
it is not authored.

**Why `ctx` not `context`**
Brevity. The compiler sees `ctx` frequently on every edge. Shorter keyword, same semantics.

**Why `law` not `governance`**
`law` is one syllable. `governance` is three. In a constitutional language, the
one-syllable keyword for the constitutional concept seems right.

---

*For contrast with: Codex's independent GTL proposal (same date)*
*Relates to: 20260314T003000 (algebraic core), 20260313T205228 (constitutional final draft)*
