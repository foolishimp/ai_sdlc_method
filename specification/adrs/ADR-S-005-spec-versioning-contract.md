# ADR-S-005: Spec Versioning Contract

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-02
**Scope**: `specification/` version numbers and compatibility guarantees

---

## Context

The `specification/` directory carries a version number (currently v3.0.0-beta.1 on the Asset Graph Model). Implementations (`imp_*/`) build against a specific version of the spec. Without a versioning contract:

1. **Implementations don't know when to update.** A spec change is committed. Existing implementations are now building against a subtly different contract without knowing it.
2. **Breaking vs non-breaking changes are ambiguous.** A rewording of a requirement might be editorial (non-breaking) or semantic (breaking). Without rules, practitioners disagree.
3. **Deprecation is informal.** A REQ key is quietly removed from the spec. Tests in `imp_*/` that `Validates: REQ-F-REMOVED-001` are now testing something that no longer exists in the spec. No one notices.
4. **Implementations can't declare compatibility.** A practitioner wants to build a new implementation. Which version of the spec are they targeting? There is no way to state this explicitly.

---

## Decision

### Version scheme

The spec follows semantic versioning with explicit stability markers:

```
v{MAJOR}.{MINOR}.{PATCH}[-{STABILITY}]
```

| Segment | Increment when |
|---------|---------------|
| `MAJOR` | Any breaking change (see below) |
| `MINOR` | New content that is backward-compatible (new REQ keys, new documents, new sections) |
| `PATCH` | Editorial changes, typo fixes, clarifications that do not change meaning |
| `-{STABILITY}` | `alpha` (in flux), `beta` (stable enough for implementation), absent (released) |

### Breaking changes (require MAJOR bump)

A change is **breaking** if an implementation that was valid against version N could become invalid against version N+1 without any changes on its part:

| Change | Breaking? |
|--------|-----------|
| Removing a REQ key | Yes |
| Renaming a REQ key | Yes |
| Strengthening an acceptance criterion (e.g., adding a new MUST condition) | Yes |
| Changing a domain token in a REQ class (e.g., `REQ-F-AUTH-*` → `REQ-F-AUTHN-*`) | Yes |
| Renaming a core primitive or operation | Yes |
| Changing the semantics of a defined term | Yes |
| Moving a document to a different path | Yes (path references break) |

### Non-breaking changes (MINOR or PATCH)

| Change | Level |
|--------|-------|
| Adding a new REQ key | MINOR |
| Adding a new document | MINOR |
| Adding a new section to an existing document | MINOR |
| Adding an ADR-S-* entry | MINOR |
| Weakening an acceptance criterion (e.g., removing a MUST condition) | MINOR |
| Clarifying ambiguous wording without changing meaning | PATCH |
| Fixing a typo | PATCH |
| Updating cross-reference paths after a document move (ADR-S-001 type) | PATCH if the move is already captured in a MAJOR bump |

### Deprecation lifecycle

1. **Mark**: Add `[DEPRECATED v{N.M}]` to the REQ key entry in `requirements/`. State the replacement or reason.
2. **Grace period**: At least one MINOR version where the deprecated key still exists.
3. **Remove**: Only in a MAJOR version bump. All implementations must remove `Implements: REQ-*` and `Validates: REQ-*` tags for the removed key before upgrading.

### Implementation compatibility declaration

Each `imp_*/` design document declares the spec version it targets:

```yaml
# In imp_<name>/design/AISDLC_<NAME>_DESIGN.md header
spec_version: "3.0.0"   # semantic version; no stability marker needed
```

An implementation is "compatible" if it satisfies all MUST requirements for the declared version.

### Version file

The canonical version lives in `specification/VERSION` (plain text, one line):

```
3.0.0-beta.1
```

This file is the single source of truth. Document headers that display a version number derive from it.

---

## Consequences

**Positive:**
- Implementations can declare `spec_version: X.Y.Z` and know exactly what contract they are building against.
- A breaking change is unambiguous: does the change meet the criteria? If yes, bump MAJOR.
- Deprecation has a lifecycle. REQ keys are never silently removed.
- Automated tooling can check that `Implements: REQ-*` tags in code reference keys that still exist in the declared spec version.

**Negative / trade-offs:**
- MAJOR bumps require coordinated updates across all `imp_*/`. This is more process.
- The stability marker (`-beta`) creates ambiguity about when an implementation should update. Convention: implementations should track `-beta` for the current development cycle and pin to a release for production deployments.
- Document path changes (like the ADR-S-001 restructuring) are technically breaking under this contract. In practice, a cross-reference update script can be run automatically; whether to treat this as a MAJOR bump depends on whether the paths are part of the public contract (they are, given that implementations link to spec documents).

---

## Alternatives Considered

**Date-based versioning** (e.g., `2026-03-02`): Considered. Simple, but gives no compatibility signal. Two dates do not tell you whether the second is backward-compatible with the first.

**No versioning — just use git tags**: Rejected as insufficient. Git tags exist but have no semantic meaning about compatibility. A practitioner cannot determine from two git tags whether their implementation needs to change.

**Lock to a single "current" version — no compatibility contract**: What we have today implicitly. Rejected because it means implementations break silently on every spec change.

---

## References

- [ADR-S-001](ADR-S-001-specification-document-hierarchy.md) — structure changes that affect document paths (path changes are MAJOR under this contract)
- [ADR-S-003](ADR-S-003-req-key-format.md) — REQ key format; key renames are MAJOR changes
- [requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — the document where REQ key deprecation is recorded
