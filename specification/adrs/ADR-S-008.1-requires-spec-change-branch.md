# ADR-S-008.1: Stage 3 — requires_spec_change Branch

**Series**: S
**Parent**: ADR-S-008 (Sensory-Triage-Intent Pipeline)
**Status**: Accepted
**Date**: 2026-03-09
**Authority**: ADR-S-027 Resolution 2

---

## What changes

ADR-S-008 Stage 3 (Intent Generation) terminates at `intent_raised`. This amendment adds a mandatory branch at that point based on whether the detected delta requires a spec change.

### Amendment to Stage 3

Every `intent_raised` event MUST carry a `requires_spec_change: true | false` field.

**Branch semantics**:

```
intent_raised
  │
  ├── requires_spec_change: false ──→ DISPATCHABLE
  │                                   composition_dispatched event emitted
  │                                   no feature_proposal required
  │                                   no human gate required
  │                                   (implementation resolves macro from registry)
  │
  └── requires_spec_change: true  ──→ PROMOTION REQUIRED
                                      feature_proposal event emitted (ADR-S-010)
                                      enters Draft Features Queue
                                      F_H gate required before any work begins
```

**Classification rule** (how to determine which branch):

| Delta type | requires_spec_change |
|-----------|---------------------|
| Gap in existing spec coverage (code, tests, telemetry missing for a defined REQ key) | false |
| New capability not represented in spec (new REQ key, new feature, new requirement) | true |
| Ecosystem change requiring spec response (new CVE, breaking API change) | true if spec must change; false if implementation can adapt within existing spec |

### Invariant (new)

> An `intent_raised` event with `requires_spec_change: true` MUST NOT result in `composition_dispatched` without an intervening `spec_modified` event that references its `feature_proposal`.

---

## What does not change

All other Stage 1, Stage 2, and Stage 3 semantics in ADR-S-008 are unchanged.

---

## References

- ADR-S-008 (parent)
- ADR-S-010.1 — companion amendment adding the same invariant on the feature_proposal side
- ADR-S-026.1 — adds `requires_spec_change` to composition expression schema
- ADR-S-027 Resolution 2 — authority for this amendment
