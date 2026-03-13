# ADR-GM-001 — Human-Readable Context is Mandatory at Every Rendering Surface

**Date**: 2026-03-14
**Status**: Accepted
**Traces To**: REQ-F-OVR-001, REQ-F-NAV-001, UX Principle 2
**Applies To**: Every page, every component, every view model

---

## Context

genesis_manager repeatedly renders technical identifiers — REQ keys, feature IDs, edge names,
run IDs, event types — as the **primary** or **only** label for an entity. Examples observed:

- Overview in-progress table: shows `REQ-F-FSNAV-001` with no title
- Feature detail header: shows `REQ-F-FSNAV-001` alone until detail loads
- Evidence event list: shows `iteration_completed` with no human summary
- Supervision feature list: shows status and edge but no feature description

A user seeing `REQ-F-AUTH-001` on the overview has no idea what that feature is unless they
already know. This directly violates the product goal: *"a customer should be comfortable
glancing at this page daily."*

UX Principle 2 already names this: *"Identifiers are never the only label shown. A row that
shows only REQ-F-*, run_id, or edge names has failed the product goal."*

The problem recurs because the constraint lives in the UX doc but is not enforced by the
domain model or view models. Components are built from view models that omit description
fields, so there is nothing to render even when the developer wants to comply.

---

## Decision

**Every view model that includes a technical identifier MUST also include its human-readable
description at the point of construction on the server, not as an optional field.**

This is a server-side contract. The client must not need to make a second request to fetch
the description for an entity it already knows the ID of.

### Rule 1 — Feature identifiers carry title + description

Any view model that references a `featureId` must also carry:
- `title: string` — the feature vector's `title:` field (short, one-line)
- `description: string` — the feature vector's `description:` field (may be empty string,
  but must be present so the client can decide how to handle it)

This applies to: `InProgressFeature`, `SupervisionFeature`, `FeatureDetail`, every gate card,
every blocked-feature entry, every child vector reference.

### Rule 2 — Edge names carry human labels

Edge identifiers (`code↔unit_tests`, `requirements→design`) must be accompanied by a
human-readable label and phase description wherever they appear in lists or tables.

Edge label table (canonical):

| Edge identifier | Human label | Phase |
|----------------|-------------|-------|
| `intent→requirements` | "Capture requirements" | Spec |
| `requirements→feature_decomposition` | "Decompose into features" | Spec |
| `feature_decomposition→design_recommendations` | "Design recommendations" | Spec/Design |
| `design_recommendations→design` | "Architecture design" | Design |
| `design→module_decomposition` | "Module decomposition" | Design |
| `module_decomposition→basis_projections` | "Basis projections" | Design |
| `basis_projections→code` | "Code construction" | Build |
| `code↔unit_tests` | "Code + unit tests (TDD)" | Build |
| `design→uat_tests` | "UAT test cases" | Verify |
| `unit_tests→cicd` | "CI/CD integration" | Deploy |

This table belongs in `domain/EDGE_LABELS.md` and is the canonical source for all
renderings of edge names in the UI.

### Rule 3 — Event types carry human summaries

Event type strings (`iteration_completed`, `edge_converged`, etc.) must be accompanied
by a one-line human summary wherever they appear in lists. Mapping:

| Event type | Human summary |
|-----------|--------------|
| `iteration_completed` | "Iteration finished" |
| `edge_converged` | "Edge converged ✓" |
| `edge_started` | "Edge started" |
| `review_approved` | "Human approved" |
| `review_rejected` | "Human rejected" |
| `spawn_created` | "Child vector spawned" |
| `spawn_folded_back` | "Spawn result folded back" |
| `intent_raised` | "New intent raised" |
| `gaps_validated` | "Gap analysis run" |
| `health_checked` | "Workspace health checked" |
| `bug_fixed` | "Bug fixed" |
| `auto_mode_set` | "Auto-mode changed" |

### Rule 4 — Empty descriptions have a fallback

When `description` is an empty string (the feature author did not write one), the UI
renders a fallback derived from `title`:

```
[title] — no description yet.
```

It does **not** render an empty space, hide the field, or show only the identifier.

### Rule 5 — View models are the enforcement layer

The server must not return a view model with a `featureId` field unless that same response
object also contains `title` and `description` for that feature. If the data is absent from
the YAML (e.g., `description:` is missing entirely), the server substitutes an empty string.

This makes compliance checkable: a grep for `featureId` in `types.ts` without an adjacent
`title` field is a type-level violation of this ADR.

---

## Consequences

### Positive
- Components always have something human-readable to render — no silent empty states
- UX Principle 2 becomes mechanically enforced by the type system, not just by convention
- New page authors cannot accidentally create identifier-only views because the view model
  does not permit it

### Negative
- View model objects are larger (carry more fields)
- Server readers must join feature YAML data to every view model construction — more reads

### Migrations required

These view models currently violate Rule 1 and must be updated:

| View model | Missing fields | Fix |
|-----------|---------------|-----|
| `InProgressFeature` | `title`, `description` | Add to server response + type |
| `RecentActivity` | `title` | Add to server response + type |
| `GateItem` | `featureTitle` | Add to server response + type |
| `WorkspaceSummary` | project `description` | Add `projectDescription` or derive from `INTENT.md` |

---

## Alternatives Considered

### A — Lazy-load descriptions on hover
Rejected. Requires extra round-trips and means the primary list view is still identifier-only
until the user hovers. Violates "summary first" (UX Principle 4).

### B — Show descriptions only on detail pages
Rejected. This is the current broken state. The overview and supervision pages are glance
pages — they must be readable without drilling into each feature.

### C — Require feature authors to fill descriptions before workspace is shown
Rejected. The system must be useful even with sparse metadata. Rule 4 (fallback) is the
correct answer.

---

## Checklist (enforced at each page spec review)

- [ ] Every `featureId` in the view model has an adjacent `title` field
- [ ] Every `featureId` in the view model has an adjacent `description` field
- [ ] Edge names in tables are accompanied by the human label from EDGE_LABELS.md
- [ ] Event types in lists are accompanied by the human summary from Rule 3
- [ ] Empty `description` fields render the Rule 4 fallback, not blank space
- [ ] No component renders a technical identifier as its only visible text
