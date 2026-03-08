# ADR-S-011.1: Event Type Registrations — CONSENSUS and Named Composition Events

**Series**: S
**Parent**: ADR-S-011 (Unified OpenLineage Metadata Standard)
**Status**: Accepted
**Date**: 2026-03-09
**Authority**: ADR-S-027 Resolution 1

---

## What changes

ADR-S-025 and ADR-S-026 introduced new event types without registering them in ADR-S-011's eventType mapping table. This amendment registers them.

### Amendment to §eventType mapping

Add the following rows to the eventType mapping table. All map to `eventType: OTHER` with `sdlc:event_type` facet.

**CONSENSUS functor events (ADR-S-025)**:

| Semantic event | OL eventType | sdlc:event_type value |
|---------------|-------------|----------------------|
| `proposal_published` | OTHER | `proposal_published` |
| `comment_received` | OTHER | `comment_received` |
| `vote_cast` | OTHER | `vote_cast` |
| `asset_version_changed` | OTHER | `asset_version_changed` |
| `consensus_reached` | OTHER | `consensus_reached` |
| `consensus_failed` | OTHER | `consensus_failed` |
| `recovery_path_selected` | OTHER | `recovery_path_selected` |

**Named Composition / Intent Vector events (ADR-S-026 + ADR-S-027)**:

| Semantic event | OL eventType | sdlc:event_type value |
|---------------|-------------|----------------------|
| `composition_dispatched` | OTHER | `composition_dispatched` |
| `intent_vector_converged` | COMPLETE | `intent_vector_converged` |
| `intent_vector_blocked` | FAIL | `intent_vector_blocked` |

### Amendment to §sdlc:event_type facet

Add the new event type values to the `type` enum in the `sdlc:event_type` facet definition:

```json
"sdlc:event_type": {
  "type": "intent_raised | feature_proposal | spec_modified | iteration_completed |
           health_checked | gaps_validated | spawn_created | status_generated |
           proposal_published | comment_received | vote_cast | asset_version_changed |
           consensus_reached | consensus_failed | recovery_path_selected |
           composition_dispatched | intent_vector_converged | intent_vector_blocked"
}
```

### Registration protocol (enforced from this amendment forward)

Any new semantic event type introduced in a future spec ADR MUST include a companion registration in ADR-S-011 (via a child amendment ADR-S-011.Y) before the event type is used in code or tooling. The registration MUST precede or accompany the ADR that introduces the event.

---

## What does not change

- OL RunEvent schema
- Namespace conventions
- Local-first invariant
- v1/v2 migration handling
- All existing event type mappings
- Custom facet library (new `type` values added to existing facet; no new facets)

---

## References

- ADR-S-011 (parent)
- ADR-S-012.1 — companion: adds same event types to the semantic taxonomy
- ADR-S-025 — CONSENSUS functor events (source)
- ADR-S-026 — Named composition events (source)
- ADR-S-027 Resolution 1
