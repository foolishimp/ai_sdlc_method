# ADR-S-024.1: Rename — "Consensus Decision Gate" → "Design Signal Gate"

**Series**: S
**Parent**: ADR-S-024 (Consensus Decision Gate)
**Status**: Accepted
**Date**: 2026-03-09
**Authority**: ADR-S-027 Resolution 4

---

## What changes

ADR-S-024's mechanism is renamed from **"Consensus Decision Gate"** to **"Design Signal Gate"**.

### Reason

ADR-S-025 defines CONSENSUS as a higher-order multi-stakeholder evaluator functor with quorum voting, participation floors, and typed failure outcomes. ADR-S-024's mechanism — marketplace signal triage at session boundaries using the ambiguity routing table — is a different construct that does not involve voting.

Sharing the word "consensus" creates a false equivalence between:
- ADR-S-024: exteroceptive sensory evaluation of design signals (reflex/affect/escalate routing)
- ADR-S-025: multi-stakeholder quorum evaluation of a proposed asset (vote/quorum/ratify)

### Canonical terminology after this amendment

| Term | Meaning | Owner |
|------|---------|-------|
| **Design Signal Gate** | Session-boundary evaluation of marketplace artifacts; routes by ambiguity level | ADR-S-024 (as amended) |
| **CONSENSUS** | Multi-stakeholder F_H evaluator functor; quorum voting on a proposed asset | ADR-S-025 |

### Substitution

All occurrences of "Consensus Decision Gate" in ADR-S-024 are replaced by "Design Signal Gate". No other changes. The substance, evaluation protocol, trigger conditions, and three-outcome routing table are all unchanged.

The ADR-S-024 title and filename are grandfathered (per ADR-S-001.1 parent immutability rule). The canonical name going forward is "Design Signal Gate". References to ADR-S-024 should use "Design Signal Gate (ADR-S-024)".

---

## What does not change

- Trigger conditions (session start, mid-session, convergence boundary)
- Three-outcome routing table (zero/bounded/persistent → reflex/affect/escalate)
- Evaluation protocol (read → classify → respond → route)
- Ratification event semantics
- Relationship to the IntentEngine composition law

---

## References

- ADR-S-024 (parent)
- ADR-S-025 — CONSENSUS functor (distinct construct)
- ADR-S-027 Resolution 4
