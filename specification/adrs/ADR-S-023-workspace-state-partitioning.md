# ADR-S-023: Workspace State Partitioning

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-07
**Scope**: `.ai-workspace/` directory structure — cross-tenant vs tenant-scoped runtime state

---

## Context

ADR-S-002 establishes that `specification/` and `imp_<name>/` are separated by a hard boundary: spec is shared and tech-agnostic; implementations are isolated and tech-bound.

`.ai-workspace/` is the runtime complement — derived projections (events, feature vectors, task tracking, snapshots) produced as the methodology executes. ADR-S-002 notes it is "not specification" and "not subject to the one-writer rule," but does not define how its contents are partitioned.

In practice two classes of runtime state emerge:

1. **Cross-tenant state** — applies to the project regardless of which implementation is running. The event log, shared feature vectors, the overriding goal, the backlog, and cross-cutting analysis are in this class. No single tenant owns them.

2. **Tenant-scoped state** — belongs to one implementation's execution. Its sprint tasks, local context hierarchy, per-tenant artifacts, and derived views are specific to how that implementation traverses the graph. Writing this into the cross-tenant root couples implementations that should be isolated.

Without an explicit partitioning rule, tenant-specific content accumulates at the workspace root, producing the same coupling problem that `specification/` → `imp_<name>/` was designed to prevent — just one layer down.

---

## Decision

### The partition

```
.ai-workspace/                         ← cross-tenant root
├── events/events.jsonl                ←   shared event log (append-only, all tenants)
├── features/                          ←   shared feature vectors (spec-level)
├── tasks/active/ACTIVE_TASKS.md       ←   overriding goal + tenant index
├── tasks/finished/                    ←   cross-tenant archived sprints
├── comments/                          ←   shared decision marketplace (all tenants)
├── graph/                             ←   shared graph topology
├── spec/                              ←   shared derived spec views
├── snapshots/                         ←   shared checkpoints
│
└── <tenant>/                          ← tenant-scoped root (one per implementation)
    ├── tasks/active/ACTIVE_TASKS.md   ←   tenant sprint tasks
    ├── tasks/finished/                ←   tenant archived sprints
    ├── context/                       ←   tenant context hierarchy (ADR-S-022)
    └── artifacts/                     ←   tenant working state
```

Tenant names match the `imp_<name>` convention: `claude`, `gemini`, `codex`, `bedrock`.

### What belongs at the cross-tenant root

| Path | Content | Rule |
|------|---------|------|
| `events/events.jsonl` | All runtime events | All implementations append to one log |
| `features/active/` | Shared feature vectors | Feature identity is spec-level, not tenant-level |
| `tasks/active/ACTIVE_TASKS.md` | Overriding goal, "done" definition, tenant index | One goal, applies to all |
| `tasks/finished/` | Completed cross-tenant work | Shared history |
| `comments/` | Multi-agent reviews, gap analyses, strategy posts | Addressed to `all` or multiple tenants |
| `graph/` | Graph topology config | Shared schema |
| `spec/` | Derived spec views | Derived from `specification/`, not from any one implementation |
| `snapshots/` | Workspace checkpoints | Point-in-time across all state |

### What belongs in the tenant directory

| Path | Content | Rule |
|------|---------|------|
| `<tenant>/tasks/active/` | Sprint tasks specific to this implementation | Tenant owns its execution plan |
| `<tenant>/tasks/finished/` | Completed tenant sprints | Tenant history |
| `<tenant>/context/` | Context hierarchy files (ADR-S-022) | Tenant-specific constraint surface |
| `<tenant>/artifacts/` | Working state, fold-back files, agent outputs | Tenant execution artifacts |

### The overriding goal is cross-tenant

The root `tasks/active/ACTIVE_TASKS.md` is a **constraint surface**, not a sprint log. It states:
- The overriding goal — what "done" means for the project as a whole
- The completion definition — observable criteria, not implementation steps
- A tenant index — links to each tenant's own task file

Tenant task files state how that implementation will satisfy the goal. They are subordinate to and consistent with the overriding goal, but they do not modify it.

### Invariant

> Any `.ai-workspace/` content that names a specific tenant implementation (runtime, technology, command surface) belongs in `.ai-workspace/<tenant>/`, not at the root.

This is the runtime mirror of ADR-S-002's invariant for `specification/`.

---

## Consequences

**Positive:**
- A new implementation starts by reading `specification/` and `.ai-workspace/tasks/active/ACTIVE_TASKS.md` — both are tech-agnostic. No cross-contamination from other tenants' sprint tasks.
- The shared event log remains unified (one source of truth for all projections) while execution plans are isolated.
- The overriding goal is visible to all implementations simultaneously — each tenant's sprint is explicitly oriented toward a shared completion definition.
- Cross-tenant comments and gap analyses remain in the shared commons, preserving the decision marketplace (see CONVENTIONS.md).

**Negative / trade-offs:**
- The tenant directory must be created explicitly before a tenant begins work. An agent that writes to the root without checking creates coupling.
- Content that feels shared (e.g., a feature vector that only one tenant is implementing) must still stay at the root if it is spec-level, even if no other tenant currently uses it.

---

## Relationship to Other ADRs

| ADR | Relationship |
|-----|-------------|
| ADR-S-002 | This ADR applies the same partition principle to runtime state that ADR-S-002 applies to repository layout |
| ADR-S-010 | The shared event log is governed by ADR-S-010 (event-sourced spec evolution); tenants append, never overwrite |
| ADR-S-022 | Tenant context hierarchy lives in `.ai-workspace/<tenant>/context/` per this ADR |
| ADR-S-012 | The event stream is a formal model medium shared across tenants — this ADR protects that unity |

---

## References

- [ADR-S-002](ADR-S-002-multi-tenancy-model.md) — repository layout partition (spec vs implementation)
- [ADR-S-010](ADR-S-010-event-sourced-spec-evolution.md) — shared event log as source of truth
- [ADR-S-022](ADR-S-022-project-lineage-and-context-inheritance.md) — tenant context hierarchy
- `.ai-workspace/comments/CONVENTIONS.md` — decision marketplace conventions
