# STRATEGY: The Intent→Requirements boundary is the universal epistemically hard edge

**Author**: claude
**Date**: 2026-03-13T14:00:00+11:00
**Addresses**: universal invariant of the Genesis formal system — one irreducible F_H stage per domain graph, all downstream edges deterministic against it
**For**: all

## Proposition

Every well-formed Genesis graph package has exactly one epistemically hard edge: the boundary where intent is translated into a formal specification surface. Everything downstream of that boundary is deterministically evaluable against it.

This is not a property of any specific domain. It is a structural invariant of the formal system.

## The Invariant

For any domain graph `G`:

```
∃ exactly one edge E in G such that:
  - E cannot be evaluated deterministically against a prior asset
  - E is the only edge where the evaluation surface itself is uncertain
  - All edges downstream of E evaluate deterministically against E's output
  - Gap analysis at E admits no convergence guarantee
  - Gap analysis at all edges downstream of E is computable
```

This edge is always the `intent → specification` boundary — the point where human meaning (vague, incomplete, emergent) is translated into a formal artifact that downstream work can evaluate against.

## Instances

| Domain | Hard Edge | Downstream Surface |
|--------|-----------|-------------------|
| AI SDLC | `intent → requirements` | requirements spec |
| `genesis_obligations` | `source → interpretation_case` | normalized obligations |
| Medical device | `clinical intent → functional requirements` | device specification |
| Financial system | `business intent → product requirements` | product spec |
| Any governed system | `human meaning → formal artifact` | that artifact |

The surface changes. The structure does not.

## Why downstream is deterministic

Once the specification surface is attested, all subsequent edges evaluate against it — not against intent. This makes them computable:

- Does the design satisfy the specification? Computable.
- Does the code implement the design? Computable.
- Do tests cover the specified behaviour? Computable.
- Does the system behave as specified under real conditions? Largely computable — and where it fails, the failure is evidence of a gap at the hard edge, not a failure of the downstream edge.

UAT failures are not convergence failures in the test edge. They are signals that the intent→requirements edge did not fully converge. They feed back.

## Implications for F_H gate design

The hard edge is the correct and only necessary location for maximum F_H investment:

- deepest deliberation floor
- highest evidence requirements before F_H is presented
- mandatory ambiguity documentation
- quorum where precedent is being set
- explicit risk appetite attestation

Downstream F_H gates exist for governance and accountability, not epistemic necessity. They are checkpoints, not the irreducible judgment event.

## Implications for gap analysis

Gap analysis at the hard edge cannot converge to 100%. It converges to **"F_H attested under these conditions with this risk appetite"** — which is the correct terminal state. The conditions and the appetite are in the record.

Gap analysis at all downstream edges can in principle converge to 100% against the attested specification surface. That is the standard to hold them to.

## Implications for profile design

The profile configuration for any Genesis domain package follows directly:

1. Front-load F_H rigor at the hard edge
2. Maximise F_D automation at all downstream edges
3. Use F_P to raise confidence before F_H is presented at the hard edge
4. Treat downstream F_H gates as governance checkpoints with lighter evidence requirements

This is not a per-domain design decision. It is a consequence of the invariant.

## The universal claim

`genesis_obligations` illustrates this with `source → interpretation_case` as its hard edge. But the principle is not about regulatory interpretation. It is about the structure of any governed asset system:

**There is always exactly one place where human meaning enters the formal system. That is the hard edge. Make it visible, make it attested, make it traceable. Everything else follows.**

All software is provisional on user acceptance. All legal interpretations are provisional on governance attestation. All medical devices are provisional on clinical validation. The provisionally is not a defect — it is the correct terminal condition at the hard edge. Genesis does not eliminate it. Genesis makes it explicit, recorded, and auditable.

*Reference: conversation 2026-03-13, genesis_obligations strategy review*
*Relates to: ADR-S-008 (Sensory-Triage-Intent), ADR-S-025 (CONSENSUS), ADR-S-036 (Invariants as Termination Conditions)*
