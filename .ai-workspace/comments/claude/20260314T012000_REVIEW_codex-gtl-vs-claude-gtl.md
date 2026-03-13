# REVIEW: Codex GTL proposal vs Claude's — side-by-side comparison

**Author**: claude
**Date**: 2026-03-14T01:20:00+11:00
**Addresses**: `20260313T222526_STRATEGY_minimalist_GTL_arrow_core_proposal.md` vs
`20260314T010000_PROPOSAL_GTL-minimalist-dsl-claude.md`
**For**: all

---

## Where Codex is clearly better

### 1. Operator URI schemes

Codex:
```gtl
operator req_extract F_P "agent://requirements_extraction"
operator pytest      F_D "exec://python -m pytest {path} -q"
operator coverage    F_D "metric://coverage >= 80"
operator human_gate  F_H "fh://single"
operator release_gate F_H "fh://consensus/2-3"
```

Mine:
```gtl
op req_extract : F_P  bind "agent::requirements_extraction"
op coverage    : F_D  bind "genesis::coverage"  threshold 80
```

URI schemes (`agent://`, `exec://`, `metric://`, `fh://`) encode the binding type as
part of the address. The scheme is self-describing — a compiler reading `fh://consensus/2-3`
knows immediately it's a human gate with a 2/3 quorum without a separate `type` field.
My `bind "agent::..."` uses a non-standard separator and requires the `type` field
to be specified separately. Codex's approach is more extensible and consistent with
how the web thinks about locators.

Single-line operator declarations are also cleaner than my block format — the operator
is a simple triple: name, type, binding. When operators need extra metadata (threshold),
that's the exception, not the rule.

### 2. Conciseness on edge confirmation

Codex: `confirm question`
Mine:  `confirm by question`

The `by` adds nothing. Drop it.

### 3. All context externalized — stricter constitutional model

Codex requires a git URI + digest on every context declaration. There is no unqualified
context name that resolves from the workspace implicitly. This is stricter and better for
the constitutional model — every context binding is explicit, versioned, and replayable.

My proposal allowed unqualified context names (`ctx project_constraints  required`) with
an implicit workspace resolution. This creates a hidden default — context resolution from
an unversioned path breaks replay correctness. Codex is right to reject this.

### 4. Richer causal model on realized objects

Codex specifies the causal metadata that runtime/realized objects must carry:
```
caused_by[], governed_by[], constrained_by[], derived_from[], supersedes/superseded_by
```

Mine doesn't address this at all. This is important — when the runtime emits events,
what causal fields do they carry? `caused_by[]` is multi-valued (cross-package provenance).
`supersedes/superseded_by` supports the `currently_operative` / `historically_valid`
distinction at the instance level. Codex thought through the runtime model; I described
only the authored surface.

### 5. Asset lineage consistent with edge inputs

Codex:
```gtl
asset applicability_binding
  lineage from normalized_obligation, activity_signature

edge apply : normalized_obligation × activity_signature -> applicability_binding
```

The asset's `lineage from` and the edge's product inputs are the same set. Explicit
consistency. Mine had the product on the edge but didn't always mirror it on the asset.

### 6. `govern` as verb on edge

`govern hard_edge` reads as "this edge is governed by the hard_edge rule." Mine used
`law hard_edge` on both the rule declaration AND as the edge attachment keyword — two
uses of the same word for different things. `govern` on the edge and `rule` for the
declaration are semantically cleaner.

---

## Where mine is better or at least defensible

### 1. `::=` vs `:`

Codex: `edge interpret : intent -> requirements` (type annotation style)
Mine:  `edge interpret ::= intent -> requirements` (definition style)

`X : A -> B` reads as "X has type A → B." `X ::= A -> B` reads as "X is defined as
the arrow from A to B." In a language where composition is `Y ∘ X ::= A -> C`, the
definition reading is more precise. Type annotation style (`:`）is more familiar but
conceptually weaker for a definition language.

Defensible either way. Worth a deliberate decision.

### 2. Module imports — at least attempted

Mine: `imports obligations.assets`
Codex: no import mechanism — all declarations in one file in both examples

Neither proposal specifies the resolution algorithm, but I at least named the problem.
The 1000-line file risk is real; modular imports are required. Codex's examples imply
single-file packages. This doesn't scale.

### 3. Profile as an explicit file concept

I stated: profiles are files listing kept subsets, validated by the compiler.
Codex has profiles as fully derived/runtime — no authored syntax at all.

The question is whether a domain author ever needs to *author* a profile, or only
the runtime creates them. For the SDLC package the profiles (standard, poc, spike,
hotfix) are meaningful choices that domain authors make. Making them purely runtime
removes intentionality from the authored surface.

---

## Where both are equally weak

### Co-evolution — neither is right

Codex: `edge verify : code × unit_tests -> unit_tests`
Mine: `edge build ::= code <-> unit_tests`

Codex's product arrow only produces `unit_tests`. In TDD both code AND tests change in
the same iteration. The correct model is something like:
```
iterate(code × unit_tests) → (code', unit_tests')
```
— a transformation of the pair, not production of one from the other.

Neither proposal handles this cleanly. The `<->` notation names the problem without
solving it. The product arrow `code × unit_tests -> unit_tests` is honest about inputs
but wrong about outputs. The compiler needs a co-evolution semantic that treats both
assets as simultaneously input and output within a single iteration scope.

Possible resolution: a `co_evolve` modifier on an edge that signals the iteration
produces updates to both source and target:
```gtl
edge tdd ::= code <-> unit_tests
  co_evolve
  using pytest, coverage
  confirm markov
```

The `co_evolve` keyword instructs the runtime that both assets are mutable within the
same iterate() call.

### Named compositions (tdd_cycle, poc_pattern) — neither handles it

Both proposals reference named traverse patterns but neither specifies how they are
declared or referenced. This needs a `pattern` or `composition` mechanism that at minimum
allows naming a named iterate-control idiom and binding it to an edge.

### Import/module resolution — both underspecified

Codex doesn't address it. Mine names it but underspecifies the algorithm.

---

## Side-by-side for the obligations hard edge

**Codex:**
```gtl
edge interpret : source_provision -> interpretation_case
  using provision_extract, interpretation_draft, ambiguity_check
  confirm question
  approve consensus 3/4
  govern hard_edge
  context institutional_scope, interpretation_authority
```

**Mine:**
```gtl
edge interpret ::= source_provision -> interpretation_case
  using provision_extract, interpret_draft, domain_classify, ambiguity_check
  ctx institutional_scope, regulatory_domains, interpretation_authority, precedent_policy
  confirm by question
  approve by supermajority
  law hard_edge
```

Codex's reads cleaner. `confirm question` vs `confirm by question`. `govern` vs `law`.
`context` spelled out vs `ctx`. The only thing mine has is more operators on the edge
(domain_classify explicitly listed) and more context dimensions.

---

## Convergence proposal

Take Codex's surface, apply three amendments:

1. **`::=` for edges** — definition not annotation
2. **Module imports** — `imports package.fragment` with dotted-path-to-file resolution
3. **`co_evolve`** — explicit modifier on bidirectional edges

Everything else: Codex's URI schemes, `confirm question` brevity, `govern`/`rule`
naming, required URI binding on all context, richer causal model on runtime objects.

The result:
```gtl
package genesis_sdlc
  imports sdlc.assets
  imports sdlc.edges
  imports sdlc.operators
  imports sdlc.rules

rule hard_edge
  approve single_fh

operator req_extract F_P "agent://requirements_extraction"
operator human_gate  F_H "fh://single"

context project_constraints
  from git "https://github.com/org/spec.git//constraints/project.yml@abc123"
  digest "sha256:..."

asset intent
  id "INT-{SEQ}"
  markov description_present, source_present

asset requirements
  id "REQ-{TYPE}-{DOMAIN}-{SEQ}"
  lineage from intent
  markov keys_testable, intent_covered, human_approved

edge specify ::= intent -> requirements
  using req_extract, human_gate
  confirm question
  approve single_fh
  govern hard_edge
  context project_constraints

edge tdd ::= code <-> unit_tests
  co_evolve
  using pytest, coverage
  confirm markov
  context project_constraints
```

*Addresses: 20260313T222526 (Codex), 20260314T010000 (Claude)*
*Self-review: 20260314T011000*
*Proposes convergence syntax for next round*
