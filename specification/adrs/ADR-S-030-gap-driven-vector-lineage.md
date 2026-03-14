# ADR-S-030: Immutable Lineage Rule — Gap-Driven Vector Typing

**Series**: S
**Status**: Accepted
**Date**: 2026-03-09
**Revised**: 2026-03-14 (adds child vector spawning detail — supersedes ADR-S-026.2 resume rule)
**Scope**: Vector model refinement — typing and lineage for repair work

--- 

## Context

ADR-S-026 unified vectors into `intent_vector`. However, the typing rule for work discovered against an already-converged feature remained ambiguous (Codex residual finding #2). If a gap (e.g., `missing_telemetry`) is found on `REQ-F-123`, do we re-open the original vector or spawn a new one?

## Decision

### The Immutable Lineage Rule

Converged trajectories are **Immutable**. Once a feature vector reaches `status: converged`, its historical trajectory MUST NOT be modified or reverted.

### Repair Work as Child Intent Vectors

Any work discovered by a gap evaluator against an existing requirement MUST spawn a **NEW** intent vector with the following typing rules:

1.  **source**: `gap`
2.  **parent_vector_id**: The ID of the converged parent feature (e.g., `REQ-F-123`).
3.  **subtype**: `repair_vector` (or `telemetry_vector`, `test_vector` based on gap type).
4.  **resolution_level**: The level where the gap was observed (e.g., `telemetry`, `code`).

### Causal Mapping

The project graph MUST project these as child branches. The repair vector carries its own trajectory and converges independently. The parent feature's lineage facet will eventually include the child's convergence as a "Stability Anchor."

## Child Vector Schema

Gap-driven child vectors carry:

```yaml
id: REQ-F-{DOMAIN}-{SEQ}-repair-{N}   # or telemetry-{N}, test-{N} by gap type
source_kind: gap_observation
parent_vector_id: REQ-F-{DOMAIN}-{SEQ}  # the converged parent
trigger_event: {event_id}               # gaps_validated, telemetry_breach, etc.
blocking: true | false                  # does this gate parent feature_complete?
resolution_level: code | tests | telemetry | design  # where gap was observed
vector_type: feature | hotfix           # per gap severity
```

### Updated Subtype Table

`gap_observation` as a `source_kind` is retained. Its meaning: applies to child vectors only, not top-level feature vectors.

```
feature_vector   = intent_vector where vector_type = feature,
                                       source_kind ∈ {abiogenesis, parent_spawn},
                                       profile ∈ {full, standard, hotfix, minimal}

child_vector     = intent_vector where vector_type ∈ {feature, hotfix},
                                       source_kind = gap_observation,
                                       parent_vector_id = existing converged REQ-F-*

discovery_vector = intent_vector where vector_type = discovery,
                                       source_kind = gap_observation

spike_vector     = intent_vector where vector_type = spike,
                                       source_kind ∈ {abiogenesis, gap_observation}

poc_vector       = intent_vector where vector_type = poc,
                                       source_kind ∈ {abiogenesis, parent_spawn}

hotfix_vector    = intent_vector where vector_type = hotfix,
                                       source_kind = gap_observation
```

Note: `gap_observation` is NOT valid as `source_kind` on a top-level `feature_vector`. All `gap_observation` vectors are either child vectors (with `parent_vector_id`) or `discovery_vector` / `hotfix_vector` / `spike_vector` subtypes.

### Feature Complete Definition

```
feature_complete(F) ⟺ F.status = converged
                     ∧ ∀ child ∈ children(F) where child.blocking = true:
                           child.status = converged
```

Non-blocking children (advisory improvements, telemetry enhancements) do not gate feature completion. Blocking children (missing tests on REQ key, correctness bugs) do.

### Routing Table

| Situation | Action |
|-----------|--------|
| Gap against converged REQ-F-* | Spawn child vector with `source_kind: gap_observation`, `parent_vector_id: REQ-F-*`, `blocking: true\|false` |
| Gap requiring new REQ-F-* | `feature_proposal → spec_modified → new feature_vector` with `source_kind: abiogenesis` |
| Gap against in-progress (not yet converged) vector | No spawn — gap is feedback to the active iterate() loop on that vector |

**Prior rule superseded**: ADR-S-026.2 defined `source_kind: gap_observation` on `feature_vector` as a signal to transition `status` back to `iterating` on the existing vector. This created a state machine violation: the event log is append-only, so a `status: converged` event followed by `status: iterating` for the same vector ID is contradictory. It also prevented CONSENSUS composability — a ratified asset cannot be modified without a new CONSENSUS round. The child vector rule above resolves this.

## Consequences

- **Positive**: Preserves event-sourced history. No "state-reversion" side effects. Clear causal audit trail from initial creation to every subsequent repair. Parallel repair: multiple agents can work different child vectors simultaneously. CONSENSUS composability: ratified assets are untouched; repair work goes through its own evaluation cycle.
- **Negative**: Increases the number of active intent vectors in large projects. The `blocking` flag and `feature_complete` definition manage this — genesis_monitor displays child vectors grouped under their parent.
