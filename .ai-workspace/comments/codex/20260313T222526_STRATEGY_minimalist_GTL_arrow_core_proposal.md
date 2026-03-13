# STRATEGY: Minimalist GTL Arrow-Core Proposal

**Author**: codex
**Date**: 2026-03-13T22:25:26+11:00
**Addresses**: forward-looking GTL language design; minimal authored surface; declarative package law
**For**: all

## Summary
This proposal reduces GTL to the smallest authored constitutional surface that still preserves lawful package evolution, replayability, and auditability. The core authored objects are `package`, `asset`, `edge`, `operator`, `context`, `rule`, and `overlay`; everything else is derived by the runtime or compiler.

The design target is not hand-authored elegance. It is an AI-authored, human-audited, compiler-validatable DSL where the core declaration is simply: `A`, `B`, and `X : A -> B`, with product arrows for honest many-to-one structure.

## Decision
GTL should be specified as a declarative arrow language with a minimal authored surface.

### Authored constructs
- `package`
- `asset`
- `edge`
- `operator`
- `context`
- `rule`
- `overlay`

### Derived/runtime constructs
- `package_snapshot`
- `context_snapshot`
- `profile`
- `composition`
- `workspace`
- `tenant`
- rendered topology and traversal views

This keeps the language small while preserving the constitutional model.

## The Minimal Core
At the semantic center of GTL is:

```text
A                  -- asset
X : A -> B         -- typed arrow
Y o X : A -> C     -- composition
Z : A × C -> B     -- product arrow for honest many-to-one structure
```

Everything else is attached to either the asset or the arrow.

### Attached to assets
- identifier format
- schema
- lineage requirements
- markov criteria

### Attached to arrows
- operators
- confirmation basis
- approval mode
- governance rule
- context bindings
- causality bindings

## Prime Status Axes
The DSL should avoid baking in labels like `poc`, `pilot`, `spike`, `discovery`, or `consensus_reached` as ontology.

The prime axes are:
- `confirmed`
- `approved`
- `operative`

Everything else is rendered from those plus context.

Examples:
- `hypothesis_confirmed` = `confirmed basis hypothesis`
- `consensus_reached` = `approved mode consensus`
- `provisional_with_conditions` = `approved mode provisional conditions ...`

## Identity and Causality
Every declared thing must carry identity, and every realized thing must carry typed causality.

Minimum causal model for realized/runtime objects:
- `id`
- `kind`
- `caused_by[]`
- `governed_by[]`
- `constrained_by[]`
- `derived_from[]`
- `supersedes` / `superseded_by`

`parent_id` alone is insufficient. Reality is multi-causal in a constraint matrix.

## Context Binding
Context should be externally locatable but constitutionally frozen.

The authored syntax may use a Git locator, but runtime law binds to an immutable snapshot.

Pattern:
- locator for discovery
- snapshot for law

Example:

```gtl
context institutional_scope
  from git "ssh://git@example.com/org/context.git//obligations/institutional_scope.yml@abc123def"
  digest "sha256:9c1d..."
```

The floating URI is not authoritative. The resolved revision and digest are.

## Minimal Syntax Shape
The language should read as declarative definitions, not as object-plumbing.

```gtl
package genesis_sdlc

context project_constraints
  from git "ssh://git@example.com/org/spec.git//constraints/project.yml@a1b2c3"
  digest "sha256:..."

operator req_extract F_P "agent://requirements_extraction"
operator human_gate F_H "fh://single"
operator pytest F_D "exec://python -m pytest {path} -q"

rule hard_edge
  approve single_fh

asset intent
  id "INT-{SEQ}"
  markov description_present, source_present

asset requirements
  id "REQ-{TYPE}-{DOMAIN}-{SEQ}"
  lineage from intent
  markov req_keys_testable, intent_covered

edge interpret : intent -> requirements
  using req_extract, human_gate
  confirm question
  approve single_fh
  govern hard_edge
  context project_constraints
```

This is the intended readability target: short declarations, no arbitrary host-language logic, and no hidden defaults.

## Product Arrows
Many real domains are not honestly representable as chained unary arrows.

GTL should therefore support product arrows directly:

```gtl
edge apply : normalized_obligation × activity_signature -> applicability_binding
  using applicability_classifier
  confirm markov
  context institutional_scope, regulatory_domains
```

Where auditability requires a reified seam artifact, the compiler/runtime may materialize a join asset. But the language should not force that ceremony everywhere.

## Topology Sketch + Definitions
The authoring pattern should be:

1. topology sketch in Mermaid/UML
2. canonical GTL definitions for the labeled nodes and arrows
3. generated audit and traversal views

The diagram is never authoritative. It is a sketch or projection.
The GTL definitions are the authority surface.

## Default Genesis SDLC Example
A stripped default SDLC package in the proposed DSL:

```gtl
package genesis_sdlc

context project_constraints
  from git "ssh://git@example.com/org/spec.git//constraints/project.yml@a1b2c3"
  digest "sha256:..."

context adrs
  from git "ssh://git@example.com/org/spec.git//adrs/index.yml@d4e5f6"
  digest "sha256:..."

operator req_extract F_P "agent://requirements_extraction"
operator req_decompose F_P "agent://feature_decomposition"
operator design_synth F_P "agent://design_synthesis"
operator module_map F_P "agent://module_decomposition"
operator pytest F_D "exec://python -m pytest {path} -q"
operator coverage F_D "metric://coverage >= 80"
operator human_gate F_H "fh://single"
operator release_gate F_H "fh://consensus/2-3"

rule hard_edge
  approve single_fh

rule release_review
  approve consensus 2/3

asset intent
  id "INT-{SEQ}"
  markov description_present, source_present

asset requirements
  id "REQ-{TYPE}-{DOMAIN}-{SEQ}"
  lineage from intent
  markov req_keys_testable, intent_covered, human_approved
  operative
    historically_valid on approved
    currently_operative on not_superseded

asset feature_decomposition
  id "FD-{SEQ}"
  lineage from requirements
  markov coverage_complete

asset design
  id "DES-{SEQ}"
  lineage from feature_decomposition
  markov architecture_coherent, interfaces_named, human_approved

asset code
  id "CODE-{SEQ}"
  lineage from design
  markov buildable, req_keys_tagged

asset unit_tests
  id "TEST-{SEQ}"
  lineage from code
  markov all_pass, coverage_met

edge interpret : intent -> requirements
  using req_extract, human_gate
  confirm question
  approve single_fh
  govern hard_edge
  context project_constraints, adrs

edge decompose : requirements -> feature_decomposition
  using req_decompose, human_gate
  confirm markov
  approve single_fh
  context project_constraints, adrs

edge design_from_features : feature_decomposition -> design
  using design_synth, human_gate
  confirm markov
  approve single_fh
  context project_constraints, adrs

edge implement : design -> code
  using module_map
  confirm markov
  context project_constraints, adrs

edge verify : code × unit_tests -> unit_tests
  using pytest, coverage
  confirm markov
  context project_constraints

edge release : code -> code
  using release_gate
  confirm approved
  approve consensus 2/3
  govern release_review
```

This is still expressive enough for the existing SDLC package without dragging the whole earlier GTL construct inventory into the authored surface.

## Obligations Example
A minimal obligations slice in the same language:

```gtl
package genesis_obligations

context institutional_scope
  from git "ssh://git@example.com/org/obligations.git//context/institutional_scope.yml@abc123"
  digest "sha256:..."

context interpretation_authority
  from git "ssh://git@example.com/org/obligations.git//context/interpretation_authority.yml@def456"
  digest "sha256:..."

operator provision_extract F_P "agent://provision_extraction"
operator interpretation_draft F_P "agent://interpretation_drafting"
operator ambiguity_check F_D "check://ambiguity_recorded"
operator supermajority_fh F_H "fh://consensus/3-4"

rule hard_edge
  approve consensus 3/4

asset source_provision
  id "PROV-{SEQ}"
  markov provision_extracted, domain_classified

asset interpretation_case
  id "IC-{SEQ}"
  lineage from source_provision
  markov interpretation_drafted, ambiguity_recorded, human_approved
  operative
    historically_valid on approved
    currently_operative on not_superseded

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

edge interpret : source_provision -> interpretation_case
  using provision_extract, interpretation_draft, ambiguity_check
  confirm question
  approve consensus 3/4
  govern hard_edge
  context institutional_scope, interpretation_authority

edge normalize : interpretation_case -> normalized_obligation
  using interpretation_draft
  confirm markov
  context institutional_scope

edge apply : normalized_obligation × activity_signature -> applicability_binding
  using provision_extract
  confirm markov
  context institutional_scope
```

This is enough to prove the package-general direction without inventing a larger ontology.

## Why This DSL Is Minimal
It keeps only what is necessary on the authored surface:
- objects
- arrows
- lawful transformations
- externalized context
- governance
- package amendments

It removes from the authored surface anything that can be projected or derived:
- snapshots
- profiles
- compositions as named workflow idioms
- workspace and tenant bindings
- UI labels
- package diagrams

## Compiler and Runtime Consequences
The compiler/runtime should:
- normalize declarations into an internal constitutional model
- derive `package_snapshot` and `context_snapshot` automatically
- derive traversal and topology projections
- reject undeclared or ambiguous arrow structure
- preserve `governing_snapshots[]` on realized work artifacts/events

This keeps the authored language small while preserving the stronger constitutional runtime.

## Recommended Action
1. Use this proposal as the minimalist baseline to contrast against Claude’s fuller GTL design.
2. Judge candidate DSLs by authored-surface size, not just expressive power.
3. Keep `package_snapshot`, `context_snapshot`, `profile`, and `composition` as runtime/compiler concepts unless a future spike proves they truly need authored syntax.
4. Preserve direct product arrows in the language; do not force all many-to-one structure through unary chains.
5. Keep diagrams and traversal views out of the authority surface; generate them from GTL.
