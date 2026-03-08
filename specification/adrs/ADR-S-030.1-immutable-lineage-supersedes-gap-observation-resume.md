# ADR-S-030.1: Immutable Lineage — Gap Work Spawns Child Vectors

**Series**: S
**Parent**: ADR-S-030 (Immutable Lineage Rule — Gap-Driven Vector Typing)
**Status**: Accepted
**Date**: 2026-03-09
**Supersedes**: ADR-S-026.2 — routing rule that gap work on existing REQ-F-* resumes the parent vector
**Withdrawal Rationale**: ADR-S-026.2 defined `source_kind: gap_observation` on `feature_vector` as a signal to transition `status` back to `iterating` on the existing vector. This creates a state machine violation: the event log is append-only, so a `status: converged` event followed by `status: iterating` for the same vector ID is contradictory. It also prevents CONSENSUS composability — a ratified asset cannot be modified without a new CONSENSUS round. ADR-S-030.1 resolves this by adopting immutable lineage universally.
**Prior reference**: git tag `adr-deleted/ADR-S-026.2`

---

## What changes from ADR-S-026.2

### The routing rule is replaced

ADR-S-026.2 routing rule (superseded):
> When `source_kind: gap_observation` on a `feature_vector`, the vector MUST reference an existing spec-defined `REQ-F-*` key. The existing feature vector's `status` transitions to `iterating`.

**New rule**: converged trajectories are immutable. Once a feature vector reaches `status: converged`, its trajectory MUST NOT be modified or reverted. Any gap discovered against a converged vector MUST spawn a new child intent vector.

### Child vector schema

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

### Subtype table — gap_observation on child vectors only

`gap_observation` as a `source_kind` is retained. Its meaning changes:

```
Before (ADR-S-026.2): gap_observation on feature_vector → resume parent
After  (ADR-S-030.1): gap_observation on child vector   → spawned from parent gap
```

The full updated subtype table:

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

Note: `gap_observation` is no longer valid as `source_kind` on a top-level `feature_vector`. All `gap_observation` vectors are either child vectors (with `parent_vector_id`) or `discovery_vector` / `hotfix_vector` / `spike_vector` subtypes.

### Feature complete definition

```
feature_complete(F) ⟺ F.status = converged
                     ∧ ∀ child ∈ children(F) where child.blocking = true:
                           child.status = converged
```

Non-blocking children (advisory improvements, telemetry enhancements) do not gate feature completion. Blocking children (missing tests on REQ key, correctness bugs) do.

### Routing table

| Situation | Action |
|-----------|--------|
| Gap against converged REQ-F-* | Spawn child vector with `source_kind: gap_observation`, `parent_vector_id: REQ-F-*`, `blocking: true\|false` |
| Gap requiring new REQ-F-* | `feature_proposal → spec_modified → new feature_vector` with `source_kind: abiogenesis` |
| Gap against in-progress (not yet converged) vector | No spawn — gap is feedback to the active iterate() loop on that vector |

The third row is unchanged from prior ADRs: a vector that has not yet converged is already in an iterate() loop. Gap findings against it are evaluator outputs that drive that loop — not triggers for child spawning.

---

## What does not change

- Four primitives, one operation
- Five-level stack (ADR-S-026 §1)
- Intent vector tuple fields (ADR-S-026 §4.1)
- Named compositions (PLAN, POC, SCHEMA_DISCOVERY, DATA_DISCOVERY)
- `source_kind` values for non-gap vectors: `abiogenesis`, `parent_spawn`
- `discovery_vector`, `spike_vector`, `hotfix_vector` subtype definitions
- CONSENSUS composability semantics (ADR-S-025) — unchanged and now strengthened

---

## Rationale

Four properties make immutable lineage the correct model:

1. **Event sourcing integrity**: the event log is append-only. State reversion (`converged → iterating`) on the same vector ID is not representable without corrupting the log's causal order. Child vectors are new identities — no reversion occurs.

2. **CONSENSUS composability**: if CONSENSUS ratified an asset, a mutable resume would modify a ratified artifact without a new CONSENSUS round. With immutable lineage, the ratified asset is untouched; repair work goes through its own evaluation cycle with its own evaluators.

3. **Parallel repair**: multiple agents can work different child vectors simultaneously without coordination overhead. Mutable resume requires serialised ownership of the parent.

4. **Causal audit**: `parent_vector_id` + `trigger_event` gives a complete chain from original intent to every subsequent repair. No state archaeology required.

The cost — child vector accumulation — is managed by the `blocking` flag and the `feature_complete` definition. genesis_monitor displays child vectors grouped under their parent.

---

## References

- ADR-S-030 (parent) — Immutable Lineage Rule
- ADR-S-026.2 (superseded) — git tag `adr-deleted/ADR-S-026.2`
- ADR-S-026 — Named Compositions and Intent Vectors (five-level stack, vector subtypes)
- ADR-S-025 — CONSENSUS functor (ratification composability)
- ADR-S-009.1 — Intent vector schema extension (source_kind field)
- Proposal `20260309T120000`: Decision 1 — immutable lineage rationale
