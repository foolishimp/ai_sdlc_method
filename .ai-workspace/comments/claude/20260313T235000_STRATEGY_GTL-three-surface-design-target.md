# STRATEGY: GTL three-surface design — AI-authored, human-audited

**Author**: claude
**Date**: 2026-03-13T23:50:00+11:00
**Addresses**: GTL syntax design convergence from session conversation
**For**: all

## The design target shift

ADR-S-035 was designed around Python DSL as the authoring surface — humans
write GTL. The conversation has arrived at a different and better target:

**GTL is AI-authored, human-audited.**

Humans do not hand-write 500 lines of GTL. They:
- express intent in natural language
- inspect the AI-generated GTL
- read the rendered audit view
- tweak small parts
- approve or reject

This changes the design requirements entirely. Optimize for:
- strict invariants (AI generates correctly)
- unambiguous structure (compiler rejects bad structure)
- easy diff and review (human audits constitutional change)
- good rendered explanations (human understands consequences)

Not for hand-authoring elegance.

## The three-surface model

```
1. Natural language intent    — what the human says
         ↓ AI generates
2. Canonical GTL              — strict, normalized, machine-first, auditable
         ↓ compiler renders
3. Audit view                 — what the human mostly reads:
                                summary, diff, risks, invariants, causal chain
```

The human usually does not read raw GTL first. They read the rendered audit
view, then inspect GTL only for debugging or deep review. The raw GTL is the
formal record — the audit view is the human interface.

## Canonical GTL syntax direction

Not Python OO builders. Not SQL tables. Not Scala class hierarchies.

A dedicated declarative syntax — line-oriented, declaration-first, normalized:

```
package genesis_sdlc

context project_constraints
context adrs optional
context domain_reference optional

asset intent
  id INT-{SEQ}
  markov description_present, source_present

asset requirements
  id REQ-{TYPE}-{DOMAIN}-{SEQ}
  lineage from intent
  markov keys_testable, intent_covered, human_approved

asset code
  id CODE-{SEQ}
  lineage from basis_projections
  markov req_keys_tagged, buildable

asset unit_tests
  id TEST-{SEQ}
  lineage from code
  markov all_pass, coverage_met

operator req_extract
  type F_P
  bind agent::requirements_extraction

operator pytest
  type F_D
  bind python -m pytest {test_path} -q

operator coverage
  type F_D
  bind genesis::coverage
  threshold 80

operator human_gate
  type F_H
  bind interactive

governance hard_edge
  approve single_fh

edge intent -> requirements
  using req_extract, human_gate
  confirm confirmed basis question
  approve approved mode single_fh
  context project_constraints, adrs, domain_reference

edge code <-> unit_tests
  using pytest, coverage
  confirm confirmed basis markov
  execute tdd_cycle
```

### Why this syntax

- Easy to generate correctly (AI target)
- Easy to validate (compiler target)
- Easy to diff (constitutional change auditing)
- Not cute, not verbose — just explicit
- Each declaration answers: identity, kind, structure, causality, governance,
  confirmation, operability. Nothing else.

### Audit rendering (what humans mostly see)

```
Package: genesis_sdlc

Assets
  - intent → requirements → design → code ↔ unit_tests → cicd

Hard edge
  - intent → requirements
  - confirmation: question answered
  - approval: single F_H

Co-evolution edge
  - code ↔ unit_tests
  - confirmation: markov stability
  - execution: tdd_cycle

Governance
  - hard_edge: single F_H approval

Context
  - required: project_constraints, adrs
  - optional: domain_reference
```

On constitutional change (overlay applied):

```
Overlay change: fintech_compliance

  Adds asset:  compliance_review (CR-{SEQ})
  Adds edge:   design → compliance_review
    confirmation: asset stable
    approval: consensus 2/3 (raised from single_fh)
  
  Snapshot impact: new work only
  Governing snapshot: SNAP-042
  Migration: no in-flight work affected
```

## Composition for scale (avoiding the 1000-line SQL nightmare)

Modular file structure, explicit imports:

```
package.gtl          ← imports only
assets/
  core.gtl           ← intent, requirements, design, code, unit_tests
  delivery.gtl       ← cicd, release, telemetry
edges/
  spec_flow.gtl      ← intent→requirements→design
  code_flow.gtl      ← code↔unit_tests, design→uat
  delivery_flow.gtl  ← code→cicd→release
operators/
  agents.gtl         ← all F_P operator bindings
  deterministic.gtl  ← all F_D operator bindings
governance/
  standard.gtl       ← hard_edge, design_gate, release_gate
overlays/
  fintech.gtl
  emea.gtl
```

`package.gtl`:
```
package genesis_sdlc
  imports assets.core
  imports assets.delivery
  imports edges.spec_flow
  imports edges.code_flow
  imports edges.delivery_flow
  imports operators.agents
  imports operators.deterministic
  imports governance.standard
```

Local files stay small. Full package is normalized by the compiler.
AI generates fragments. Humans review focused diffs.

## What this means for the implementation path

### Phase 1 — Python as carrier

Python can host this syntax as an internal DSL or as a parsed string format.
The semantic model is the canonical GTL algebra; Python provides the tooling
bootstrap. The Python builder style (`.assets(...).edges(...)`) is NOT the
target — it was a shortcut that produces the wrong aesthetics.

If Python carries the syntax, it should be:
```python
load_gtl("assets/core.gtl")   # parse and validate, return normalized IR
load_gtl("edges/code_flow.gtl")
compile_package("package.gtl") # produce PackageSnapshot from normalized IR
```

Not:
```python
class MyPackage(Package):
    assets = [Intent(), Requirements(), ...]
```

### Phase 2 — Dedicated GTL parser

The canonical syntax is designed to be parseable by a simple grammar — no
Python required. Phase 2 replaces the Python carrier with a standalone parser
that produces the same normalized IR. Migration cost is low because the syntax
is already the semantic target.

## What still needs specification

1. **Minimal grammar** — BNF or EBNF for the canonical syntax. Needed before
   the AI can generate it reliably without drift.

2. **Audit view format** — what sections, what ordering, what diff format.
   This is the primary human surface; it needs specification as much as the GTL.

3. **Normalized IR (package model)** — the intermediate representation the
   compiler produces from GTL. This is what the runtime interprets.
   PackageSnapshot is the runtime artifact; the normalized IR is what the
   snapshot is derived from.

4. **Import/composition rules** — how fragments compose, how conflicts resolve,
   what the compiler validates at composition time.

## Pricing against the constitutional GTL final draft

The three-surface model fits the constitutional GTL direction cleanly:
- The canonical GTL is the constitutional language
- The audit view renders constitutional change for human review
- The modular structure makes overlays small and reviewable
- The AI-authored model fits the F_P construction model — GTL is the
  canonical output of an F_P actor, not a human hand-authoring surface

Constitutional invariants (the three laws, root-of-trust chain) live in the
`governance.gtl` fragments and are validated at compile time by the GTL
compiler — not enforced at runtime by middleware.

*Reference: session conversation 2026-03-13*
*Relates to: ADR-S-035 (to be superseded), 20260313T205228 (final draft GTL)*
*Next: minimal grammar sketch or audit view format — spike pick*
