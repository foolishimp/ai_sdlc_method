# ADR-S-035: Genesis Topology Language (GTL) — Python Library

**Status**: ACCEPTED
**Date**: 2026-03-14
**Supersedes**: ADR-S-035 v1 (Python DSL with custom text syntax — withdrawn, never implemented)
**Review**: Codex five-finding review accepted 2026-03-14; code updated to v0.2.1

---

## Decision

GTL is a Python library, not a custom text DSL.

Packages are defined as Python objects using `gtl.core`. The library is the canonical
authority surface. There is no parser, no custom syntax, no separate toolchain.

```python
from gtl.core import Package, Asset, Edge, Operator, Rule, Context, Overlay
from gtl.core import F_D, F_P, F_H, consensus
from gtl.core import Operative, PackageSnapshot
```

## Rationale

In AI-assisted development the author is the AI, not the human. The human reviews.

A custom text DSL requires: a parser, an LSP, a formatter, a syntax highlighter,
documentation, and a learning curve — all to replace a medium (Python) the AI already
writes fluently and the ecosystem already supports with types, tests, and tooling.

The Python library gives:
- **Zero learning curve** — AI knows Python; developers know Python
- **Free tooling** — mypy, pytest, black, import system, IDE support
- **Invariants at construction** — `ValueError` at import, not at a custom compile step
- **Audit via diagram** — LLM-generated Mermaid from `package.describe()` for documentation;
  `package.to_mermaid()` for deterministic review-grade projection when required

The prior direction (custom text DSL) was the right path to *find* the constitutional
object model. The design iteration with Claude and Codex sharpened every concept. But
the authoring surface that emerged from that process is Python.

## The Object Model

Seven authored constructs. Everything else is derived or runtime.

| Construct | Role |
|-----------|------|
| `Package` | Bounded constitutional world — validated at construction |
| `Asset` | Typed object class: identity, lineage, markov criteria, `Operative` condition |
| `Edge` | Typed transition: unary `A→B`, product `A×B→C`, co-evolution `A↔B` |
| `Operator` | Bound functional unit: `F_D`, `F_P`, or `F_H` with URI binding |
| `Rule` | Reusable governance: `consensus(n/m)`, dissent policy, provisional flag |
| `Context` | Externally-located constraint dimension: resolver URI + sha256 digest |
| `Overlay` | Lawful extension or restriction of a package (profiles are restriction overlays) |

Runtime-only (never authored):

| Construct | Role |
|-----------|------|
| `PackageSnapshot` | Point-in-time projection of package-definition events; law-binding surface |
| `context_snapshot_id` | Immutable artifact derived from `(locator + digest)`; replay anchor |

## Constitutional Bindings

### Context — multi-resolver, digest-anchored

`Context.locator` uses a typed URI scheme. `Context.digest` is the constitutional binding.
The floating URI is for discovery; the digest is law. The runtime derives an immutable
`context_snapshot_id` from `(locator, digest)`. Replay binds to `context_snapshot_id`.

Supported resolver schemes:

| Scheme | Source |
|--------|--------|
| `git://` | Versioned document in a git repository |
| `workspace://` | Loaded from local `.ai-workspace/` |
| `event://` | Derived from the package-definition event stream |
| `registry://` | From a shared Genesis context registry |

### PackageSnapshot — explicit law-binding

`PackageSnapshot` is the constitutional binding surface for work events. It is produced
by the runtime when an overlay activation event clears the governance pipeline.

Every work event must carry:
```json
{ "package_name": "...", "package_snapshot_id": "snap-genesis-obligations-v1.2.0" }
```

This is non-optional. Without it, historical replay cannot reconstruct the exact law
under which work was performed.

`PackageSnapshot.work_binding()` returns the minimal fields every work event must carry.

### `governing_snapshots[]`

Artifacts crossing package boundaries carry `governing_snapshots` — a list of all
upstream package snapshot IDs that materially shaped the artifact. Downstream work
traces full provenance across all constitutional surfaces, not just the immediate parent.

## Compiler Invariants (enforced at construction)

| Invariant | Enforced in | Error |
|-----------|-------------|-------|
| Closed operator surface | `Package._validate()` | operator not declared in package |
| `consensus(n, m)` ratio | `Consensus.__post_init__()` | n must be 1..m |
| Context digest prefix | `Context.__post_init__()` | must start with sha256: |
| Context locator scheme | `Context.__post_init__()` | must use known scheme |
| Operator URI scheme | `Operator.__post_init__()` | must use known scheme |
| `confirm` vocabulary | `Edge.__post_init__()` | must be question/markov/hypothesis |
| `co_evolve` consistency | `Package._validate()` | co_evolve requires list source |
| Overlay `approve` required | `Overlay.__post_init__()` | approve is required |
| Overlay restrict/add exclusion | `Overlay.__post_init__()` | mutually exclusive |

## Typed Operability — `Operative`

Asset operability is expressed as a typed `Operative` condition, not a free string.
Prime axes are `approved` and `not_superseded`. Conditions compose from them.

```python
from gtl.core import OPERATIVE_ON_APPROVED, OPERATIVE_ON_APPROVED_NOT_SUPERSEDED

# operative when approved (standard)
requirements = Asset(..., operative=OPERATIVE_ON_APPROVED)

# operative when approved AND not superseded by a later version
design = Asset(..., operative=OPERATIVE_ON_APPROVED_NOT_SUPERSEDED)

# custom condition
Operative(approved=True, not_superseded=True)   # same as above
Operative(approved=True, not_superseded=False)  # same as OPERATIVE_ON_APPROVED
```

The runtime evaluates `Operative` against the event stream at query time. The event
stream carries the supersession chain; operability is derived, not stored.

## Audit Surfaces — Topology vs Traversal

Two distinct surfaces; only one is primary for daily operation:

| Surface | What it shows | When to use |
|---------|--------------|-------------|
| **Topology** (`to_mermaid()`) | Static package structure — assets, edges, governance | Package review, onboarding, documentation |
| **Traversal** (runtime projection) | Where work is now relative to the topology | Daily operation, sprint review, human gate decisions |

Topology is background context. Traversal is the primary operational human surface.
Traversal is generated by the runtime from `PackageSnapshot × work_events` — it shows
which edges are converged, in-progress, or pending for active feature vectors.

`package.to_mermaid()` renders topology. For documentation, LLM-generated Mermaid from
`package.describe()` is acceptable. Deterministic `to_mermaid()` is warranted when
exact review-grade topology projection is required (e.g. CI gate for overlay approval).

## Technology Neutrality

The library is technology-neutral. `Operator` URIs are abstract bindings resolved at
runtime to actual infrastructure. The same package definition runs unchanged on any
runtime that implements the URI resolver registry.

| URI | Local / direct | AWS cloud |
|-----|---------------|-----------|
| `agent://provision_extraction` | Claude API direct | Bedrock + Claude |
| `exec://python -m pytest {path}` | Local subprocess | Lambda / CodeBuild |
| `metric://coverage >= 80` | Local coverage tool | CloudWatch metric check |
| `fh://single` | Claude Code interactive | Step Functions human task |
| `fh://consensus/3-4` | CONSENSUS engine | Step Functions + SNS approval |

Moving from direct API to Bedrock is a runtime configuration change, not a package
change. The constitutional model is fully portable.

## Implementation

```
imp_codex/code/gtl/
├── core.py                — all constructs; v0.2.1
└── examples/
    ├── obligations.py     — genesis_obligations (product arrow, F_H hard edge)
    └── sdlc.py            — genesis_sdlc + 4 profiles as restriction overlays
```

Both examples run and validate against v0.2.1 API. All invariants tested.

## Open Items

1. `Package.snapshot()` / serialisation format — JSON schema for `package_snapshot_activated`
   event payload. `PackageSnapshot.to_dict()` provides the structure; full schema deferred.

2. `governing_snapshots[]` on Asset *instances* — library defines the type; runtime
   populates the field on produced instances. Interface contract needs specification.

3. Named composition patterns — `tdd_cycle`, `poc_pattern` etc. Factory functions in
   Python are the likely mechanism; deferred to implementation spike.

4. Overlay conflict resolution — when two upstream governing snapshots conflict: later
   activation timestamp wins within a package; `supersedes=[snapshot_id]` field on
   `Overlay` for explicit cross-package conflict. Deferred.

## Reference Spec

GTL draft v0.2: `.ai-workspace/comments/claude/20260314T030000_SPEC_GTL-language-draft-v0.2.md`

Constitutional OS framing: `.ai-workspace/comments/codex/20260313T201904_STRATEGY_genesis-as-constitutional-os.md`

---

## Withdrawn Direction (v1)

The prior direction proposed a custom text DSL with `::=` edge notation, `rule`/`edge`/
`context` keywords, and a custom parser. That direction was used to derive the
constitutional object model during a design review cycle with Claude and Codex.
The model is preserved; the custom syntax is not adopted.

Text syntax reference: `.ai-workspace/comments/claude/20260314T020000_SPEC_GTL-language-draft-v0.1.md`
