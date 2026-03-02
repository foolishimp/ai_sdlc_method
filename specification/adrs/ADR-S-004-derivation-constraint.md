# ADR-S-004: Derivation Constraint

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-02
**Scope**: All `specification/` documents and derived artifacts

---

## Context

The `specification/` directory encodes a derivation chain:

```
INTENT.md
  └─► core/ (formal system)
        └─► requirements/ (what to build)
              └─► features/ (how requirements decompose)
              └─► ux/ (how the system presents)
              └─► verification/ (how to verify)
```

A downstream document derives its content from one or more upstream documents. It adds specificity, decomposition, or instantiation — but it cannot contradict its sources.

Without an explicit constraint:

1. **Silent divergence.** A feature vector document drifts from the requirements it was derived from. Requirements and features are now in conflict. Nobody knows which is authoritative.
2. **Cascading errors.** A practitioner sees the conflict and resolves it by making both documents "consistent" — in the wrong direction. Now the upstream requirement is wrong.
3. **Spec rot.** Over time, the spec contains contradictions. Implementations are built against different "versions" of the truth within the same document tree.
4. **No repair rule.** Without a stated constraint, there is no basis for deciding which document to fix when a conflict is found.

---

## Decision

### The constraint

> **A downstream document may not contradict an upstream document.**
>
> In any conflict between documents in the derivation chain, the upstream document is authoritative. The downstream document is wrong and must be fixed.

This is a one-directional constraint: upstream constrains downstream. Downstream can only:
- Narrow (add specificity)
- Decompose (split into sub-items)
- Instantiate (bind to a technology, in `imp_*/`)
- Extend (add detail that does not change the upstream meaning)

Downstream documents may **not**:
- Contradict an upstream statement
- Relax an upstream constraint
- Silently omit an upstream requirement (omission = violation if the omitted item is in scope)
- Redefine upstream terminology with a different meaning

### Conflict detection

A conflict is any of:

| Type | Example |
|------|---------|
| **Contradiction** | Requirements says "system must support 100 concurrent users"; Feature vector says "MVP: 10 users" without the requirement being revised first |
| **Silent omission** | Requirements defines REQ-F-AUTH-002 (password reset); Feature vector omits it with no `[OUT OF SCOPE]` marking |
| **Terminology drift** | Core model defines "Evaluator" as `{Human, Agent, Deterministic Tests}`; Design ADR uses "Evaluator" to mean only the agent component |
| **Relaxation** | Requirements says "mandatory"; UX doc says "optional for MVP" without an explicit requirement change |

### Resolution procedure

1. **Identify** which documents are in conflict.
2. **Determine position in the chain**. The upstream document is authoritative.
3. **Fix the downstream document**. Do not modify the upstream document to match a downstream drift.
4. **If the upstream document is wrong**: that is a requirement change. Update the upstream document via a deliberate, reviewed change — not a silent conflict resolution.
5. **Record** any non-trivial conflict resolution as a note in the affected document's changelog or as a new ADR if the decision is reusable.

### Scope of this constraint

This constraint applies within `specification/`. It does not govern conflicts between an implementation (`imp_*/`) and the spec — those are handled by the implementation's own review process. An implementation may choose a subset of spec requirements to implement (e.g., MVP scope), but the spec itself does not change as a result.

---

## Consequences

**Positive:**
- Conflicts have an unambiguous resolution rule. No negotiation required: fix the downstream document.
- The derivation chain is trustworthy. A reader of `requirements/` can rely on `features/` not contradicting it.
- Spec rot is identifiable: scan for contradictions, apply the rule, done.
- Reviews of downstream documents are easier: the only question is "does this add specificity without contradiction?"

**Negative / trade-offs:**
- Fixing downstream documents to match upstream takes more effort than the reverse.
- A genuinely wrong upstream requirement must be corrected through a proper upstream change, not a quiet downstream fix. This is more process, but it prevents silent corruption of the shared contract.
- Practitioners who are used to updating whatever document is in front of them need to internalise the directionality.

---

## Alternatives Considered

**Last-writer-wins**: The most recently modified document is authoritative. Rejected — this is what happens without any rule and produces spec rot.

**Downstream can override with justification**: A downstream document can contradict upstream if it provides a rationale. Rejected — this creates unbounded exceptions. The downstream document will always have a rationale; "justification" becomes a bypass.

**Bidirectional constraint (consistency)**: Both upstream and downstream must be kept consistent; either can be the "truth". Rejected — when both are wrong in opposite directions, there is still no resolution rule. One must be primary.

---

## References

- [ADR-S-001](ADR-S-001-specification-document-hierarchy.md) — directory structure that makes the chain visible
- [core/AI_SDLC_ASSET_GRAPH_MODEL.md](../core/AI_SDLC_ASSET_GRAPH_MODEL.md) — the formal system; top of the derivation chain
- [requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — first derived tier
