# ADR-S-003: REQ Key Format and Threading

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-02
**Scope**: All specification and implementation artifacts

---

## Context

The Asset Graph Model requires **feature lineage** — the ability to trace a capability from its origin in the spec, through design and code, to tests, telemetry, and back. Without a stable, parseable identifier threading through all artifacts, this traceability exists only informally (if at all).

Without a defined key format:

1. **Coverage gaps are invisible.** There is no automated way to determine whether a requirement has code, tests, or telemetry.
2. **Keys drift.** Different practitioners invent different formats (`F-AUTH-001`, `auth_login`, `FEAT_0042`) across the same codebase.
3. **Gap analysis is manual.** `/gen-gaps` and similar tools cannot grep reliably without a stable anchor pattern.
4. **Cross-artifact queries break.** A feature view that joins spec → code → tests → telemetry has no join key.

---

## Decision

### Key format

```
REQ-{CLASS}-{SEQ}
```

Where:
- `REQ` — constant prefix; makes keys greppable across any text artifact
- `{CLASS}` — category+domain token; encodes what kind of requirement and what part of the system it governs
- `{SEQ}` — zero-padded three-digit sequence number within that class

### Defined classes

| Class | Meaning | Example |
|-------|---------|---------|
| `F-{DOMAIN}` | Functional requirement scoped to a domain | `REQ-F-AUTH-001` |
| `NFR-{DOMAIN}` | Non-functional requirement | `REQ-NFR-PERF-001` |
| `TOOL` | Tooling / developer experience requirement | `REQ-TOOL-002` |
| `UX` | User experience requirement | `REQ-UX-003` |
| `SUPV` | Supervision / observability requirement | `REQ-SUPV-002` |
| `DATA` | Data model / persistence requirement | `REQ-DATA-AUDIT-001` |

Domain tokens within `F-*` and `NFR-*` are free-form but must be stable once assigned (renaming a domain is a breaking change — see ADR-S-005).

### Threading contract

Every REQ key defined in `specification/requirements/` must thread through all downstream artifacts where that requirement is addressed:

| Artifact | Tag format | Example |
|----------|-----------|---------|
| Design doc / ADR | `Implements: REQ-*` | `Implements: REQ-F-AUTH-001` |
| Source code | `# Implements: REQ-*` (comment) | `# Implements: REQ-F-AUTH-001` |
| Test | `# Validates: REQ-*` (comment) | `# Validates: REQ-F-AUTH-001` |
| Log / metric | `req="REQ-*"` (structured field) | `logger.info("login", req="REQ-F-AUTH-001")` |
| Commit message | REQ key in message body | `feat: add password reset (REQ-F-AUTH-002)` |

### Grep anchors (used by tooling)

```bash
# All REQ keys defined in spec
grep -rn "REQ-" specification/requirements/

# Code that implements a requirement
grep -rn "Implements: REQ-" src/ lib/

# Tests that validate a requirement
grep -rn "Validates: REQ-" tests/

# Telemetry tagging
grep -rn 'req="REQ-' src/ lib/
```

### Key lifecycle

1. **Defined in spec**: Added to `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` with full description and acceptance criteria.
2. **Active**: Referenced in at least one downstream artifact.
3. **Deprecated**: Marked `[DEPRECATED]` in spec. Downstream references remain but no new ones are added.
4. **Removed**: Only at a major spec version bump (see ADR-S-005). Removal of a key that has downstream references is a breaking change.

---

## Consequences

**Positive:**
- `/gen-gaps` can run fully automated Layer 1 (tag coverage), Layer 2 (test gaps), and Layer 3 (telemetry gaps) checks with simple grep.
- Feature views can be generated at any stage of the SDLC by grepping REQ keys across artifacts.
- New implementations can self-audit against the spec inventory without human curation.
- Pull request diffs that add REQ key tags are trivially reviewable.

**Negative / trade-offs:**
- Adding tags to existing code is a one-time migration cost.
- Domain token choices are permanent; renaming breaks grep coverage reports.
- Telemetry tagging adds boilerplate to log calls.

---

## Alternatives Considered

**Free-form labels** (e.g., "auth login"): Rejected. Not greppable reliably; drift is inevitable.

**UUID-based keys** (e.g., `REQ-a3f4b7c2`): Rejected. Opaque to humans; no self-documentation of what the requirement is about.

**File-path-based keys** (e.g., `spec:requirements:auth:001`): Rejected. Breaks on directory reorganisation; not grep-friendly in code comments.

**Separate tracking system** (Jira, GitHub Issues): Considered as a complement but not a replacement. External IDs cannot be embedded reliably in source code and telemetry without a stable format. The REQ key is the bridge between the external system and the artifact.

---

## References

- [requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — canonical REQ key registry
- [ADR-S-001](ADR-S-001-specification-document-hierarchy.md) — where requirements documents live
- [verification/UAT_TEST_CASES.md](../verification/UAT_TEST_CASES.md) — acceptance contracts use REQ keys as anchors
