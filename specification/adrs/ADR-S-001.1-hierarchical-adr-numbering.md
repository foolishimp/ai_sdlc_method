# ADR-S-001.1: Hierarchical ADR Numbering — Roll-Forward Amendment Scheme

**Series**: S
**Parent**: ADR-S-001 (Specification Document Hierarchy)
**Status**: Accepted
**Date**: 2026-03-09
**Amends**: ADR-S-001 §ADR series conventions

---

## Context

Flat ADR numbering forces amendments to be prose ("this ADR amends ADR-S-008") rather than structure. The amendment trail is invisible without reading every ADR. Superseded decisions accumulate as zombie files that bias LLM readers toward stale reasoning.

---

## Decision

### Dot notation for amendments

A child ADR (format `ADR-S-X.N`) amends its parent (`ADR-S-X`).

**Rules**:

1. **Parents are immutable after acceptance.** A parent ADR file is never edited. All changes come through numbered children.

2. **Roll-forward, not accumulate.** When a new amendment supersedes a prior amendment to the same parent, the prior child is **deleted from the filesystem**. The new child takes the next sequence number. Deleted files are preserved in git history only.

3. **Git tags mark deletions.** When a child ADR is deleted, the deletion commit MUST carry a git tag of the form `adr-deleted/ADR-S-{X}.{N}` so the deleted ADR is discoverable by future readers searching git history.

4. **The successor carries forward only what is relevant.** ADR-S-X.2 includes only the elements of ADR-S-X.1 that need to persist. Elements intentionally omitted from the successor are considered withdrawn. Old elements are not restated — omission is the withdrawal mechanism. This prevents stale reasoning from biasing LLM readers of the current spec.

5. **Back-reference is mandatory.** The successor MUST include a `Supersedes: ADR-S-X.N` field in its header and a reference entry at the bottom. This makes the evolution chain traceable in git without requiring the deleted file to be present.

6. **Children are concise.** A child states what changes and why relative to the parent. It does not restate the parent. The parent remains the canonical document; the child is the delta from the parent (or the delta from the prior child, if superseding one).

7. **File naming**: `ADR-S-{parent}.{seq}-{short-description}.md`. Example: `ADR-S-008.1-requires-spec-change-branch.md`.

8. **New top-level ADRs** continue flat numbering (ADR-S-028, ADR-S-029, ...). Dot notation is for amendments to existing ADRs only.

9. **Scope**: a child ADR may only amend its direct parent. Cross-parent amendments are not permitted — each parent gets its own child.

### What the filesystem represents at any point

```
specification/adrs/
  ADR-S-008.md          ← parent, immutable, canonical
  ADR-S-008.1-*.md      ← current amendment (only one child per parent at any time)
  ADR-S-009.md
  ADR-S-009.1-*.md
  ...
```

There is at most one live child per parent at any time. When X.2 is written and X.1 deleted, the filesystem contains X.2 only. The reader sees the current state without distraction.

### What git represents

- Full history of every amendment ever written, including deleted ones
- Tags of the form `adr-deleted/ADR-S-X.N` on every deletion commit
- The complete evolution chain is reconstructable from: parent ADR + git log of children + tags

### Example evolution

```
# Initial amendment
ADR-S-026.1-requires-spec-change.md  ← written, committed

# Successor supersedes it
ADR-S-026.2-composition-dispatch-protocol.md  ← written
  header: Supersedes: ADR-S-026.1
  body: only the forward-relevant elements; old elements intentionally omitted
ADR-S-026.1-requires-spec-change.md  ← DELETED in same commit
  git tag: adr-deleted/ADR-S-026.1
```

A reader of the current spec sees ADR-S-026 + ADR-S-026.2 only. To understand why ADR-S-026.2 exists, they follow the `Supersedes` reference to git history.

### Successor header format

```markdown
**Supersedes**: ADR-S-X.N — {one-line reason for supersession}
**Withdrawal Rationale**: {why X.N was withdrawn — what was wrong or incomplete; one to three sentences. Must be self-contained: the reader should not need to checkout the deleted file to understand why it was superseded.}
**Prior reference**: git tag `adr-deleted/ADR-S-X.N` for deleted predecessor
```

`Withdrawal Rationale` is mandatory. It is the tombstone. It documents the reasoning behind the withdrawal without restating the old content.

### Retrofit policy

ADRs written before this ADR (ADR-S-001 through ADR-S-027) are grandfathered as parents. Their first amendment creates ADR-S-X.1. The roll-forward scheme applies from this ADR forward — existing ADR files are not modified to apply it retroactively.

The children created alongside ADR-S-027 (ADR-S-008.1 through ADR-S-026.1) are the first generation under this scheme.

---

## Consequences

**Positive**:
- Filesystem = current truth. No zombie files. No "Status: Superseded" noise biasing LLM reads.
- Git = complete history. Nothing is lost; everything is findable via tags.
- Successor ADRs are concise — they carry only what persists, making the delta explicit.
- Amendment history is structurally visible: list the directory to see current state; search git tags to find deleted ADRs.

**Negative / trade-offs**:
- Requires discipline: deletion commit must include the git tag. Without the tag, the deleted ADR is findable only by grepping git log.
- Readers who only look at the filesystem and not git history cannot see what was withdrawn. The `Supersedes` back-reference is the signal that prior reasoning exists in git.

---

## References

- ADR-S-001 (parent)
- ADR-S-027 — Spec Consolidation (triggered this governance change)
