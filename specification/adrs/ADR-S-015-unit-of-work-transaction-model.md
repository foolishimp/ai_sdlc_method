# ADR-S-015: Unit of Work as Transaction

**Series**: S (specification-level — applies to all implementations)
**Status**: Accepted
**Date**: 2026-03-05
**Scope**: All implementations — event log schema, edge traversal lifecycle, recovery semantics
**Extends**: ADR-S-011 (OpenLineage event schema), ADR-S-012 (event stream as formal model)

---

## Context

The spec defines `iterate(Asset, Context[], Evaluators) → Asset'` as the single operation. Each invocation of this operation produces two side effects: a modified artifact and an event record. These side effects have been treated independently — the engine writes the artifact, then emits an event. No formal relationship between the two has been specified.

In practice this causes two classes of failure:

1. **Uncommitted writes**: The agent writes an artifact but the session crashes before emitting the event. The artifact exists on disk but the event log has no record of it. The system cannot distinguish this from deliberate uncommitted work.

2. **Phantom events**: A bug or retry emits a COMPLETE event for work that was only partially done. The event log records a delta=0 convergence that never happened.

Neither failure is detectable under the current model. The event log is a passive telemetry stream with no commit semantics.

---

## Decision

### The edge traversal is a transaction

Each invocation of `iterate()` for a single edge is a **transaction** with explicit boundaries:

| Phase | Event | Meaning |
|---|---|---|
| Open | `START` (OL eventType) | Transaction begun; input state recorded |
| Execute | *(no event)* | Functor runs; side effects accumulate |
| Commit | `COMPLETE` (OL eventType) | All outputs written and hashed; transaction committed |
| Rollback | `FAIL` or `ABORT` | Execution failed; prior state is authoritative |

> **Saga scope note**: At saga scope, the term "rollback" is not used. Recovery before an irreversibility boundary is **re-anchoring** to the last accountability boundary. Recovery after an external commitment is **compensation**. Saga terminal failures (such as `consensus_failed`) are typed terminal failure resolutions, not rollbacks. Abandoned speculative branches are retained in immutable lineage — the event log is never rewritten. See ADR-S-031 §Delegated Authority, Accountability Boundaries, and Speculative Branching.

The **COMPLETE event is the commit point**. Writing it atomically to `events.jsonl` is the commit. Everything before the COMPLETE is uncommitted. An artifact written to disk without a corresponding COMPLETE is an uncommitted side effect.

### Custom facet schema requirements (errata applied 2026-03-06)

Per ADR-S-011 §custom facets, all `sdlc:*` facets MUST include `_producer` and `_schemaURL` fields. Implementations that omit these fields produce invalid facets that break observability consumers.

**Normative rule:** Every `sdlc:*` facet emitted by any implementation MUST include:
```json
"_producer": { "name": "<engine-name>", "version": "<version>" },
"_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/<facet-name>.json"
```

### Content hashes on all outputs

Every COMPLETE event MUST include `sdlc:contentHash` facets on all `outputs[]`:

```json
{
  "eventType": "COMPLETE",
  "run": {
    "runId": "uuid",
    "facets": {
      "sdlc:delta": {
        "_producer": { "name": "genesis-engine", "version": "1.0" },
        "_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/delta.json",
        "delta": 0.0, "checks_passed": 12, "checks_total": 12
      }
    }
  },
  "inputs": [
    {
      "namespace": "file:///project",
      "name": "imp_claude/design/adrs/ADR-020.md",
      "facets": {
        "sdlc:contentHash": {
          "_producer": { "name": "genesis-engine", "version": "1.0" },
          "_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/contentHash.json",
          "algorithm": "sha256", "hash": "abc..."
        }
      }
    }
  ],
  "outputs": [
    {
      "namespace": "file:///project",
      "name": "src/converter.py",
      "facets": {
        "sdlc:contentHash": {
          "_producer": { "name": "genesis-engine", "version": "1.0" },
          "_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/contentHash.json",
          "algorithm": "sha256", "hash": "def..."
        },
        "sdlc:previousHash": {
          "_producer": { "name": "genesis-engine", "version": "1.0" },
          "_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/previousHash.json",
          "hash": "xyz..."
        }
      }
    }
  ]
}
```

`sdlc:previousHash` records the hash of the input artifact before modification. This makes the transition auditable: given any COMPLETE event, you can verify the artifact at any point in its history.

### START events record input manifest (errata applied 2026-03-06)

Every START event MUST record the content hashes of **all** input artifacts, not just the primary one. A single `sdlc:inputHash` is insufficient for edges that modify multiple files (e.g., `code↔unit_tests` touches both `src/` and `tests/`).

```json
{
  "eventType": "START",
  "run": {
    "runId": "uuid",
    "facets": {
      "sdlc:inputManifest": {
        "_producer": { "name": "genesis-engine", "version": "1.0" },
        "_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/inputManifest.json",
        "artifacts": [
          { "path": "src/engine.py",       "hash": "abc..." },
          { "path": "tests/test_engine.py", "hash": "def..." }
        ]
      },
      "sdlc:edge": {
        "_producer": { "name": "genesis-engine", "version": "1.0" },
        "_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/edge.json",
        "edge": "code↔unit_tests", "feature": "REQ-F-ENGINE-001"
      }
    }
  }
}
```

This enables recovery: if a session crashes after START but before COMPLETE, the engine compares current filesystem hashes against the **full manifest**, not just the primary artifact. Any hash mismatch indicates an uncommitted write.

### Causal chain for spawns

When a step spawns a child unit of work, the child's START and COMPLETE events MUST include a `parent` facet referencing the parent `runId`:

```json
{
  "run": {
    "runId": "uuid-child",
    "facets": {
      "parent": {
        "_producer": { "name": "genesis-engine", "version": "1.0" },
        "_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/parent.json",
        "run": { "runId": "uuid-parent" }
      }
    }
  }
}
```

This encodes the spawn tree in the event log. The full recursion depth is recoverable by following `parent.run.runId` links.

### Startup recovery scan

On startup, every implementation MUST scan the event log and flag open transactions:

```
For each START event:
  If no corresponding COMPLETE/FAIL/ABORT with same runId exists:
    → Open transaction detected (crash during execution)
    → Load sdlc:inputManifest from START event
    → For each artifact in manifest:
        Compute current filesystem hash
        If current hash ≠ manifest hash: artifact was modified but not committed
    → If any hash differs: emit gap_detected (uncommitted write)
    → If all hashes equal: execution had not started → safe to retry
```

The `gap_detected` event is emitted to `events.jsonl` and surfaces in `/gen-status`. It does not block execution — it is an advisory signal for human or homeostasis review.

---

## Consequences

**Positive:**
- Uncommitted writes are detectable and distinguishable from committed work.
- The event log is formally the source of truth for asset state — not the filesystem.
- Replay of the event log produces a verified history of every state transition.
- Cross-implementation consistency: any implementation that follows this model produces compatible event logs.
- Fractal recursion (spawn) is structurally encoded in the event log via `parent` facets.

**Negative / Trade-offs:**
- Content hashing every output adds overhead to each COMPLETE event. For large files this is non-trivial. Implementations may hash lazily (on COMPLETE emission) rather than eagerly.
- START events must be emitted before functor execution begins — this requires the engine to know the runId before calling the functor. This is a constraint on functor dispatch order.
- Recovery scan on startup adds latency proportional to event log size. Implementations should cache the last scan result and only re-scan events since the last known-good checkpoint.

---

## Implementation notes

The `sdlc:contentHash` and `sdlc:previousHash` facets are additions to the OL schema defined in ADR-S-011. They do not break existing events — they are additive facets on the `outputs[]` dataset entries.

Implementations that have already emitted COMPLETE events without content hashes are not retroactively non-compliant. Content hashes are required for all new events from the date of this ADR.

The startup recovery scan is implemented in:
- `imp_gemini`: `IterateEngine.detect_integrity_gaps()` (2026-03-05)
- `imp_claude`: `workspace_state.py` gap detection (partial — does not yet use event log hashes)

---

## References

- [ADR-S-011](ADR-S-011-openlineage-unified-metadata-standard.md) — OL event schema; `inputs[]` and `outputs[]` with dataset facets
- [ADR-S-012](ADR-S-012-event-stream-as-formal-model-medium.md) — event stream as the formal model medium
- [ADR-S-016](ADR-S-016-invocation-contract.md) — the typed interface that produces `StepResult` with `VersionedArtifact`
- [ADR-010](../../imp_claude/design/adrs/ADR-010-spec-reproducibility.md) — content-addressable hashing for spec/context manifests; same principle extended to runtime artifacts
