# ADR-S-035: Genesis Topology Language (GTL) — Python Library

**Status**: ACCEPTED
**Date**: 2026-03-14
**Supersedes**: ADR-S-035 v1 (Python DSL with custom text syntax — withdrawn, never implemented)

---

## Decision

GTL is a Python library, not a custom text DSL.

Packages are defined as Python objects using `gtl.core`. The library is the canonical
authority surface. There is no parser, no custom syntax, no separate toolchain.

```python
from gtl.core import Package, Asset, Edge, Operator, Rule, Context, Overlay
from gtl.core import F_D, F_P, F_H, consensus
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
- **Audit via diagram** — `package.to_mermaid()` or LLM-generated Mermaid from the
  normalised object for human review

The prior direction (custom text DSL) was the right path to *find* the constitutional
object model. The design iteration with Claude and Codex sharpened every concept. But
the authoring surface that emerged from that process is Python.

## The Object Model

Seven constructs. No others are authored — everything else is derived or runtime.

| Construct | Role |
|-----------|------|
| `Package` | Bounded constitutional world — validated at construction |
| `Asset` | Typed object class with identity, lineage, markov criteria, operative condition |
| `Edge` | Typed transition: unary `A→B`, product `A×B→C`, co-evolution `A↔B` |
| `Operator` | Bound functional unit: `F_D`, `F_P`, or `F_H` with URI binding |
| `Rule` | Reusable governance: `consensus(n/m)`, dissent policy, provisional flag |
| `Context` | Externally-located constraint dimension: git URI + sha256 digest |
| `Overlay` | Lawful extension or restriction of a package (profiles are restriction overlays) |

## Compiler Invariants (enforced at construction)

- Closed operator surface — every operator in `edge.using` must be declared in the package
- `consensus(n, m)` — `n > m` raises `ValueError`; no social labels permitted
- Context digest — must start with `sha256:`; URI alone is insufficient
- Operator URI scheme — must be one of `agent://`, `exec://`, `check://`, `metric://`, `fh://`
- `confirm` vocabulary — `"question"`, `"markov"`, or `"hypothesis"` only
- `co_evolve=True` requires `source` to be a list
- Overlay `approve` is required — overlay activation is a governance act
- Overlay `restrict_to` and `add_*` are mutually exclusive

## Technology Neutrality

The library is technology-neutral. `Operator` URIs are abstract bindings. The runtime
resolves them to actual infrastructure:

| URI | Local / direct | AWS cloud |
|-----|---------------|-----------|
| `agent://provision_extraction` | Claude API direct | Bedrock + Claude |
| `exec://python -m pytest {path}` | Local subprocess | Lambda / CodeBuild |
| `metric://coverage >= 80` | Local coverage tool | CloudWatch metric check |
| `fh://single` | Claude Code interactive | Step Functions human task |
| `fh://consensus/3-4` | CONSENSUS engine | Step Functions + approval |

The same package definition runs on any runtime that implements the URI resolver.
Moving from direct API to Bedrock is a runtime configuration change, not a package
change.

## Implementation

```
imp_codex/code/gtl/
├── core.py                — Package, Asset, Edge, Operator, Rule, Context, Overlay
└── examples/
    ├── obligations.py     — genesis_obligations (product arrow, F_H hard edge)
    └── sdlc.py            — genesis_sdlc + 4 profiles as restriction overlays
```

Both examples run and validate. All invariants tested.

## Reference Spec

GTL draft v0.2: `.ai-workspace/comments/claude/20260314T030000_SPEC_GTL-language-draft-v0.2.md`

Constitutional OS framing: `.ai-workspace/comments/codex/20260313T201904_STRATEGY_genesis-as-constitutional-os.md`

---

## Withdrawn Direction (v1)

The prior direction proposed a custom text DSL with `::=` edge notation, `rule`/`edge`/
`context` keywords, and a custom parser. That direction was used to derive the
constitutional object model during a design review cycle with Claude and Codex.
The model is preserved; the custom syntax is not adopted.

The text syntax reference remains in:
`.ai-workspace/comments/claude/20260314T020000_SPEC_GTL-language-draft-v0.1.md`
