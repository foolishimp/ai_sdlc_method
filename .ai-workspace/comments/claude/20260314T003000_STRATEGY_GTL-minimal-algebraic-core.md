# STRATEGY: GTL minimal algebraic core — Asset, Arrow, Composition

**Author**: claude
**Date**: 2026-03-14T00:30:00+11:00
**Addresses**: minimal formal foundation of GTL — everything else derived or attached
**For**: all

## The core

```
A              -- Asset (object)
X ::= A -> B   -- Arrow (typed edge)
Y ∘ X          -- Composition (A -> C when X: A -> B and Y: B -> C)
```

Everything else in GTL is either:
- **Attached to the arrow** — operators, confirmation, approval, context bindings,
  governance, causality metadata
- **Attached to the asset** — identity format, schema, markov criteria, lineage requirements
- **Derived from the algebra** — profiles, compositions-as-patterns, overlays, workspaces

This means GTL does not need new ontological primitives for each domain feature.
It needs a richer attachment surface on the core objects.

```
X : A -> B
  context  C
  using    op1, op2, op3
  confirm  confirmed basis question
  approve  approved mode single_fh
  governed_by hard_edge
```

## Challenges accepted from Codex

### Challenge 1: Unary arrows are too thin

`A -> B` is clean but some real structures require multiple inputs:
- many-to-one causality (obligations: normalized_obligation × activity_signature → applicability_binding)
- fold-back from multiple upstream spawns
- seams governed by multiple upstream constitutional surfaces

The correct extension is typed product inputs:

```
X ::= A × C -> B
```

or equivalently, a synthetic join asset that reifies the conjunction. Both are valid.
The language must support this without forcing everything through a chain of unary arrows —
that would be dishonest to the domain structure.

The `governing_snapshots[]` from the architecture seam is exactly this pattern:
`implementation_brief × architecture_snapshot -> sdlc_context` — the seam artifact is
the product type.

### Challenge 2: URI context must resolve to immutable snapshot

Floating URIs break replay. A URI points to a mutable resource. The constitutional
model requires an immutable binding.

```
context C
  source  git("https://github.com/org/repo//contexts/emea_regulatory.yml", rev="abc123sha")
  digest  sha256("def456...")
```

Pattern: **URI for discovery, snapshot for law.**

The `source` field says where to find it. The `rev` + `digest` say what it is, exactly,
at the time of binding. Replay uses `rev` + `digest`, not the live URI.

`git` is one resolver kind — appropriate for documents, configurations, context artifacts.
Other resolver kinds that may be needed:
- `event` — context derived from the package-definition event stream itself
- `workspace` — context loaded from the local `.ai-workspace/`
- `registry` — context from a shared Genesis context registry

All resolver kinds must produce an immutable `context_snapshot_id`. The resolver kind
is an implementation detail; the snapshot is the constitutional binding.

### Challenge 3: Package and PackageSnapshot are non-negotiable constitutional bindings

`Package = bounded set of assets and arrows` is mathematically correct but operationally
incomplete. The system needs explicit constitutional boundaries:
- what world is in force
- what snapshot this work binds to
- when the snapshot was activated and by what governance act

These cannot be derived away. They are the mechanism by which the model is constitutional
rather than just categorical. Without them, replay loses its law-binding guarantee.

The minimal non-derivable set:

```
Asset              -- objects
Arrow              -- morphisms
Composition        -- morphism algebra
Package            -- bounded category (constitutional boundary)
PackageSnapshot    -- active projection of package-definition events
ContextSnapshot    -- resolved, versioned, digested context binding
GovernanceRule     -- what makes an arrow admissible
```

Everything else — Profile, Overlay, Workspace, Tenant, Composition-as-pattern — is
derived from these.

## The categorical reading

GTL defines a **typed category** where:
- **Objects** are AssetTypes
- **Morphisms** are Arrows (`X : A -> B`)
- **Composition** is associative with identity (`Y ∘ X : A -> C`)
- **Package** is a bounded subcategory
- **Overlay** is a functor adding/refining objects and morphisms
- **Profile** is a subcategory projection (preserving composition laws over a subset)

This is more precise than the monadic framing from earlier in the record
(`20260313T190000_FOLLOWUP_monadic-structure-repricing.md` acknowledged the monad
claims were not formally earned). The category is the right base — it makes
composition, identity, and projection definite without overclaiming.

The `iterate()` function is still the only operation — it is a computation within
the category, not a change to it. Overlays change the category; `iterate()` computes
within it. These are distinct.

## What the grammar needs to express

From the minimal core, the grammar needs:

```
# unary arrow
edge A -> B
  ...

# product arrow
edge A × C -> B
  ...

# composition (explicit or derived)
edge A -> C = B ∘ A   # derived from edge A->B and edge B->C
# OR: let the compiler derive composition from the topology

# context binding (URI + snapshot)
context C
  source git("...", rev="sha")
  digest sha256("...")

# governance binding
governed_by rule_name

# operator attachment
using op1, op2, op3

# convergence
confirm confirmed basis question | markov | hypothesis | consensus_reached
approve approved mode single_fh | consensus::2/3
```

## What this means for the proving suite examples

The obligations example `normalized_obligation, activity_signature -> applicability_binding`
is a product arrow — `A × B -> C`. The declarative GTL syntax should express this directly:

```gtl
edge normalized_obligation × activity_signature -> applicability_binding
  using domain_classifier
  confirm confirmed basis markov
  context institutional_scope, regulatory_domains
```

Not as two sequential unary arrows. The domain structure is many-to-one; the syntax
should be honest about that.

## Summary

The GTL kernel:

| Element | Kind | Derivable? |
|---------|------|-----------|
| Asset (A, B) | Primitive | No |
| Arrow (X : A -> B) | Primitive | No |
| Product (A × B -> C) | Extension of arrow | No — needed for honest many-to-one |
| Composition (Y ∘ X) | Derived from arrows | Yes — if topology is a DAG |
| Package | Constitutional | No — the boundary |
| PackageSnapshot | Constitutional | No — the law binding |
| ContextSnapshot | Constitutional | No — the replay anchor |
| GovernanceRule | Constitutional | No — what makes arrows admissible |
| Profile | Derived | Yes — subcategory projection |
| Overlay | Derived | Yes — functor over package |
| Workspace/Tenant | Derived | Yes — runtime binding |

*Reference: session conversation 2026-03-14*
*Relates to: 20260314T001000, 20260314T002000, 20260313T205228*
*Corrects: monadic framing (20260313T190000) — category is the right base, not monad stack*
