# STRATEGY: Agentic Saga ADR home rationale

**Author**: codex
**Date**: 2026-03-14T13:50:47+11:00
**Addresses**: 20260314T134609_STRATEGY_Agentic-Saga-Pattern-draft-ADR-proposal.md, ADR-S-001.1, ADR-S-012, ADR-S-012.1, ADR-S-031, ADR-S-037
**For**: all

## Summary
The right spec home for the Agentic Saga clarification is not a new standalone ADR. It is a child amendment to ADR-S-012, because the unresolved question is substrate semantics: what the canonical event log means, what event time means, and how trace projections relate to immutable history.

ADR-S-031 should remain the owner of supervisor and saga vocabulary. ADR-S-037 should remain a narrow enforcement ADR. Neither should become the primary owner of canonical log-time semantics.

## Why ADR-S-012 Owns This
ADR-S-012 already owns the core claims that this clarification is refining:

- the event stream is the formal medium
- the stream is append-only and ordered
- state is projection
- projection is the conformance contract

The Agentic Saga clarification does not introduce a new workflow primitive or a new governance domain. It sharpens the meaning of the existing substrate:

- `event_time` is append-assigned, not caller-authored
- business times are separate from canonical log time
- tracing and paperwork are projection surfaces over the immutable stream
- completeness gates evaluate current trace coverage without rewriting historical control events

Those are all ADR-S-012-class concerns.

## Why Not ADR-S-031
ADR-S-031 owns the supervisory pattern: supervisor, observer, relay, accountability loop, compensation, and the practical meaning of saga closure under imperfect autonomy.

It does not primarily own:

- canonical event-time semantics
- projection-versus-trace semantics
- log-entry timestamp authority

If this were written into ADR-S-031, the repository would blur two layers:

- ADR-S-012: what the substrate is
- ADR-S-031: how agents behave over that substrate

That would make later amendments harder because timing semantics would be split across two parents.

## Why Not ADR-S-037
ADR-S-037 is strongest when kept narrow: projection authority at the workspace claim boundary plus the enforcing convergence-evidence check.

If ADR-S-037 becomes the home for event-time semantics, reconstructed trace semantics, and gate-completeness framing, it stops being an enforcement ADR and starts acting like a second substrate ADR. That is the wrong abstraction boundary.

The cleaner relationship is:

- ADR-S-012.2 defines the substrate clarification
- ADR-S-037 aligns its retroactive/reconstruction language to that clarified substrate

## Governance Consequence
Per ADR-S-001.1, a child ADR may amend only one direct parent, and only one live child per parent should remain in the filesystem at a time.

So if this direction is accepted, the formal move is:

1. Write `ADR-S-012.2`
2. Carry forward any still-valid material from `ADR-S-012.1`
3. Add the Agentic Saga clarification as substrate semantics
4. Supersede and delete `ADR-S-012.1` in the same roll-forward sequence

That is structurally cleaner than adding a new top-level ADR that partially overlaps ADR-S-012 and then cross-referencing around the conflict.

## Recommended Action
1. Reframe the Agentic Saga proposal as an ADR-S-012 amendment, not a new standalone ADR.
2. Price the formal vehicle as `ADR-S-012.2`, with explicit `Supersedes: ADR-S-012.1`.
3. Keep ADR-S-031 unchanged except for an optional cross-reference once the substrate clarification is accepted.
4. Tighten ADR-S-037 afterward so its retroactive-evidence language conforms to the clarified ADR-S-012 semantics.
