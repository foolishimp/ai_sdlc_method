# ADR-S-001: Specification Document Hierarchy

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-02
**Revised**: 2026-03-14 (adds ADR amendment governance — edit-in-place replaces dot-notation scheme)
**Scope**: `specification/` directory structure

---

## Context

The `specification/` directory grew organically. By v3.0.0-beta.1 it contained 10 documents at a flat level: foundational formal system documents sat next to derived requirements, derived feature decompositions, derived user journeys, and derived acceptance tests. A practitioner guide specific to the Claude implementation was also present.

This created two problems:

1. **No visible derivation structure.** `INTENT.md` and `FEATURE_VECTORS.md` appeared as peers, obscuring that feature vectors are three derivation steps downstream of intent.

2. **Input specs mixed with derived specs.** Documents that constrain everything else (the formal system) were visually equivalent to documents derived from them. A reader had no way to know which to treat as authoritative in a conflict.

Additionally:
- `UAT_TEST_CASES.md` was placed inside `specification/` despite being a verification artifact (downstream of spec in the asset graph: `Spec → Design → Code ↔ Tests → UAT`)
- `USER_GUIDE.md` declared `Platform: Claude Code` but lived in the shared spec folder

---

## Decision

Organise the `specification/` directory into subdirectories that reflect the derivation chain. Distinguish **primary inputs** (the formal system) from **derived outputs** (requirements, features, UX, verification).

### Directory structure

```
specification/
├── INTENT.md                    ← anchor (upstream of all derivations)
├── core/                        ← PRIMARY: the formal system
├── requirements/                ← DERIVED tier 1
├── features/                    ← DERIVED tier 2
├── ux/                          ← DERIVED tier 2
├── verification/                ← DERIVED tier 3
└── adrs/                        ← Spec-level decisions (this series)
```

### Placement rule

A document belongs in:

| Location | Criterion |
|----------|-----------|
| `core/` | Defines the formal system. Other documents derive from it. No technology references. |
| `requirements/` | Lists what any implementation must do. Derived from core. Technology-agnostic. |
| `features/` | Decomposes requirements into buildable units with dependencies. Derived from requirements. |
| `ux/` | Describes how the system presents to users. Derived from core + requirements. |
| `verification/` | Specifies how to verify an implementation. Derived from requirements + features. Verification artifacts, not specification. |
| `imp_*/` | Anything that names a specific technology, platform, or runtime. |

### Derivation constraint

A downstream document may not contradict an upstream one. In any conflict, the downstream document is wrong and must be fixed.

### `USER_GUIDE.md` relocation

`USER_GUIDE.md` declares `Platform: Claude Code`. It is a practitioner guide for one implementation, not shared specification. Moved to `imp_claude/docs/USER_GUIDE.md`.

### New ADR series: ADR-S-*

Decisions about the shared specification structure (this directory) use the `ADR-S-*` series. Implementation-specific decisions continue to use their own series (`ADR-008+` for Claude, `ADR-GG-*` for Gemini, etc.).

### ADR Amendment Governance

ADRs are edited **in place** when they need updating. The header carries a `**Revised**:` date marking when the update occurred. Git history is the amendment trail — `git log specification/adrs/ADR-S-NNN-*.md` shows all prior versions of any ADR.

**The governance rule**: if an ADR needs to be amended, edit the parent file directly, update the `**Revised**:` date, and commit. The commit message is the amendment rationale. The old content is preserved in git history. No separate child `.N` file is created.

**Why this replaces dot-notation child files**: the child-ADR scheme (format `ADR-S-X.N`) was introduced to preserve parent immutability while recording amendments. In practice it imposed a context-window tax on agentic builders: load parent, load child, reconcile them, detect supersession. A single merged document reduces this to one step. The parent is no longer immutable — the file is the current truth; git is the history.

**Retrofit**: child ADRs created under the prior scheme (ADR-S-008.1 through ADR-S-036.1) have been folded back into their parent files as of 2026-03-14. The git commit that performed each fold is the amendment's audit record.

---

## Consequences

**Positive:**
- The directory tree communicates derivation order. A reader navigating `specification/` sees: `core/ → requirements/ → features/ + ux/ → verification/`.
- Conflicts between documents have a clear resolution rule: fix the downstream one.
- `verification/` inside `specification/` correctly scopes the acceptance contracts as shared-but-downstream.
- Claude-specific `USER_GUIDE.md` is no longer in the shared spec folder.

**Negative / trade-offs:**
- All cross-references in existing documents needed path updates (one-time cost, automated).
- Deeper paths are slightly more verbose in links.
- Installers or tools that hardcode `specification/*.md` paths need updating.

---

## Alternatives Considered

**Flat with naming convention** (e.g., `01_INTENT.md`, `02_ASSET_GRAPH_MODEL.md`): Rejected — ordering numbers don't express derivation relationships, only sequence.

**Two levels only** (`primary/` + `derived/`)**: Considered. Simpler, but loses the tier-within-derived signal (requirements → features → verification is meaningful).

**Keep `verification/` at repo root**: Tried briefly. The acceptance contracts are derived from spec artifacts and should live alongside them, even though they are not specification themselves.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../core/AI_SDLC_ASSET_GRAPH_MODEL.md) — the formal system this structure reflects
- [README.md](../README.md) — living document map for this directory
