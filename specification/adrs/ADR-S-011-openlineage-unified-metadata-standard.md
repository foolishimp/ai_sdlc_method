# ADR-S-011: Unified OpenLineage Metadata Standard

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-03
**Revised**: 2026-03-14 (registers CONSENSUS and Named Composition event types — ADR-S-027 Resolution 1; adds registration protocol)
**Scope**: All events in `.ai-workspace/events/events.jsonl` — iterate events, homeostasis events, spec evolution events

---

## Context

The event log (`events.jsonl`) is the shared integration contract between the methodology engine, homeostasis pipeline, observability tools, and routing logic. As the methodology scales:

1. **Two schemas are emerging.** Iterate events (`edge_started`, `iteration_completed`, `edge_converged`) and homeostasis events (`intent_raised`, `feature_proposal`, `spec_modified`) have been defined in separate ADRs with incompatible field shapes. Any consumer must handle both schemas.

2. **Routing logic is deferred but depends on queryable metadata.** ADR-S-008 defines the homeostasis pipeline but defers the escalation/routing mechanism. To build routing independently of the engine, the metadata must be in a standard, queryable format now.

3. **Causal chains are implicit.** ADR-S-010 defines `trigger_event_id` as a causal link, but it is a bespoke field. There is no standard mechanism to traverse the full chain from signal → triage → intent → proposal → spec_modified using off-the-shelf tools.

4. **The dual-mode traverse architecture (ADR-021) produces events from two paths**: interactive sessions (Level 1 agent instruction) and the engine CLI (Level 4 deterministic code). Consumers must not care which path produced an event.

**The engineering choice:** Adopt a single, standardised schema for all events — one that supports causal chains, custom metadata, and standard tooling — and defer routing logic to independent consumers built on top of it. Observability first; homeostasis routing second.

---

## Decision

### OpenLineage RunEvent as the canonical event schema

All entries in `events.jsonl` MUST conform to the [OpenLineage RunEvent specification](https://openlineage.io/spec/1-0-5/OpenLineage.json). The file remains a local, append-only JSONL file. OpenLineage backend tooling (Marquez, OpenMetadata) is **optional** — the local file is the source of truth.

```json
{
  "eventType": "START | COMPLETE | FAIL | ABORT | OTHER",
  "eventTime": "{ISO 8601}",
  "run": {
    "runId": "{UUID v4}",
    "facets": {}
  },
  "job": {
    "namespace": "aisdlc://{project_name}",
    "name": "{job_name}",
    "facets": {}
  },
  "inputs": [
    {"namespace": "file://{project_root}", "name": "{relative_path}", "facets": {}}
  ],
  "outputs": [
    {"namespace": "file://{project_root}", "name": "{relative_path}", "facets": {}}
  ],
  "producer": "https://github.com/foolishimp/ai_sdlc_method",
  "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json"
}
```

### Namespace conventions

| Resource | Namespace | Example |
|----------|-----------|---------|
| Jobs | `aisdlc://{project_name}` | `aisdlc://my-service` |
| File datasets | `file://{project_root}` | `file:///home/user/my-service` |
| Spec assets | `aisdlc://spec` | `aisdlc://spec` (shared across projects) |

Using `aisdlc://` as the job namespace ensures that multiple projects ingested into a shared Marquez instance do not collide. `file://` for datasets ensures asset paths resolve on any machine without configuration.

### eventType mapping

| Our semantic event | OL eventType | Rationale |
|-------------------|-------------|-----------|
| `edge_started` | `START` | Edge traversal begins |
| `edge_converged` | `COMPLETE` | Edge traversal complete (delta=0) |
| `edge_blocked` / engine error | `FAIL` | Convergence failed or blocked |
| `iteration_abandoned` | `ABORT` | Session ended mid-traversal |
| `iteration_completed` (delta>0) | `OTHER` | Iteration step, not yet converged |
| `feature_proposal` | `OTHER` | Homeostasis pipeline output |
| `intent_raised` | `OTHER` | Consciousness loop observation |
| `spec_modified` | `OTHER` | Spec evolution event |
| `health_checked` | `OTHER` | Workspace health observation |
| `gaps_validated` | `OTHER` | Traceability layer check |
| `spawn_created` | `OTHER` | Feature vector inflate operation |
| `status_generated` | `OTHER` | Derived view regenerated |

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

**Named Composition / Intent Vector events (ADR-S-026)**:

| Semantic event | OL eventType | sdlc:event_type value |
|---------------|-------------|----------------------|
| `composition_dispatched` | OTHER | `composition_dispatched` |
| `intent_vector_converged` | COMPLETE | `intent_vector_converged` |
| `intent_vector_blocked` | FAIL | `intent_vector_blocked` |

All `OTHER` events carry an `sdlc:event_type` facet (see below) encoding the semantic type. This preserves full semantic fidelity while conforming to the OL schema.

**Registration protocol**: Any new semantic event type introduced in a future spec ADR MUST be registered in this ADR (by editing it in place) before the event type is used in code or tooling. The registration MUST precede or accompany the ADR that introduces the event.

### Custom facet library

All custom facets follow the OL facet contract: each must declare `_producer` (URI) and `_schemaURL` (URI pointing to the facet JSON Schema).

#### `sdlc:event_type`

Encodes the methodology-specific event type for `OTHER` events. Required on all `OTHER` events.

```json
"sdlc:event_type": {
  "_producer": "https://github.com/foolishimp/ai_sdlc_method",
  "_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/sdlc_event_type.json",
  "type": "intent_raised | feature_proposal | spec_modified | iteration_completed |
           health_checked | gaps_validated | spawn_created | status_generated |
           proposal_published | comment_received | vote_cast | asset_version_changed |
           consensus_reached | consensus_failed | recovery_path_selected |
           composition_dispatched | intent_vector_converged | intent_vector_blocked"
}
```

#### `sdlc:delta`

Convergence delta — the number of failing required checks at this iteration. Required on all iterate events.

```json
"sdlc:delta": {
  "_producer": "https://github.com/foolishimp/ai_sdlc_method",
  "_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/sdlc_delta.json",
  "delta": 3,
  "required_failing": 3,
  "optional_failing": 1,
  "total_checks": 12,
  "passed": 9
}
```

#### `sdlc:req_keys`

REQ keys this run implements or validates. Required on code and test edges.

```json
"sdlc:req_keys": {
  "_producer": "https://github.com/foolishimp/ai_sdlc_method",
  "_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/sdlc_req_keys.json",
  "implements": ["REQ-F-AUTH-001", "REQ-EVAL-002"],
  "validates": ["REQ-F-AUTH-001"],
  "telemetry": []
}
```

#### `sdlc:valence`

Affect triage result from the homeostasis pipeline (ADR-S-008). Required on all homeostasis events; optional on iterate events.

```json
"sdlc:valence": {
  "_producer": "https://github.com/foolishimp/ai_sdlc_method",
  "_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/sdlc_valence.json",
  "regime": "reflex | affect | conscious",
  "severity": 7,
  "urgency": 5
}
```

`severity` and `urgency` are integers 1–10. `regime` is the processing phase: reflex (autonomic, no judgment), affect (valence-weighted, may escalate), conscious (deliberative, human gate required).

#### `sdlc:proposal`

Homeostasis proposal metadata. Required on `feature_proposal` events.

```json
"sdlc:proposal": {
  "_producer": "https://github.com/foolishimp/ai_sdlc_method",
  "_schemaURL": "https://github.com/foolishimp/ai_sdlc_method/spec/facets/sdlc_proposal.json",
  "proposal_id": "PROP-007",
  "proposed_feature_id": "REQ-F-AUTO-001",
  "status": "draft | promoted | rejected"
}
```

### Causal chaining via ParentRunFacet

OL's standard `ParentRunFacet` links a child run to its parent. The full homeostasis causal chain is expressed as:

```
interoceptive_signal run (SENSORY_PROBE job, OTHER)
  └─ triage run (TRIAGE job, OTHER, parent=signal_run)
      └─ intent run (INTENT_ENGINE job, OTHER, parent=triage_run)
          └─ proposal run (FEATURE_PROPOSAL job, OTHER, parent=intent_run)
              └─ spec_modified run (SPEC_EVOLUTION job, OTHER, parent=proposal_run)
                  └─ spawn run (SPAWN job, OTHER, parent=spec_modified_run)
```

Each run carries `ParentRunFacet` pointing to its immediate parent:

```json
"run": {
  "runId": "uuid-of-this-run",
  "facets": {
    "parent": {
      "_producer": "https://github.com/foolishimp/ai_sdlc_method",
      "_schemaURL": "https://openlineage.io/spec/facets/ParentRunFacet.json",
      "run": {"runId": "uuid-of-parent-run"},
      "job": {"namespace": "aisdlc://my-project", "name": "TRIAGE"}
    }
  }
}
```

This makes the full causal chain queryable: "show me the lineage of PROP-007" traces back through intent → triage → signal using standard OL tooling.

Iterate events also chain:

```
edge_started run (START)
  └─ iteration_1 run (OTHER, parent=edge_started_run)
  └─ iteration_2 run (OTHER, parent=edge_started_run)
  └─ edge_converged run (COMPLETE, parent=edge_started_run)
```

### Job name conventions

| Event category | Job name | Example |
|---------------|----------|---------|
| Edge traversal | `{edge}` | `design→code` |
| Sensing | `SENSORY_PROBE:{sensor_type}` | `SENSORY_PROBE:interoceptive` |
| Triage | `TRIAGE` | |
| Intent generation | `INTENT_ENGINE` | |
| Feature proposal | `FEATURE_PROPOSAL` | |
| Spec evolution | `SPEC_EVOLUTION:{file}` | `SPEC_EVOLUTION:FEATURE_VECTORS.md` |
| Spawn/inflate | `SPAWN:{feature_id}` | `SPAWN:REQ-F-AUTH-001` |
| Health check | `HEALTH_CHECK` | |
| Gap validation | `GAP_VALIDATION:{layer}` | `GAP_VALIDATION:layer_2` |

### Local-first invariant

**`events.jsonl` is the source of truth.** OL backend tooling is optional.

1. All methodology tools MUST operate directly on the local JSONL file without requiring a running OL backend.
2. The schema MUST be parseable by any JSON parser — no OL SDK required for consumption.
3. Marquez / OpenMetadata transport is an optional layer. Implementations MAY push events to a backend; they MUST NOT require one.
4. The `producer` and `schemaURL` fields are informational. Tools that validate against the schema SHOULD do so; tools that don't still receive valid JSON.

This preserves the "laptop-runnable" property across all profiles (full, poc, spike, minimal) and all implementations (imp_claude, imp_gemini, imp_codex, imp_bedrock).

### v1 → v2 migration

Events written before this ADR use the v1 schema (bespoke `event_type` field, no OL structure). These are **valid historical records and MUST NOT be modified** (event log is append-only). Consumers MUST handle both schemas:

- v1 events: have `event_type` at root, no `run.runId`, no `job` object
- v2 events: have `eventType` at root, `run.runId` UUID, `job.namespace`, facets

Detection heuristic: if `eventType` is present → v2; if `event_type` is present → v1.

---

## Consequences

**Positive:**
- **Single schema.** All consumers — engine, gen-status, homeostasis router, monitoring dashboards — parse one format.
- **Standard tooling.** Marquez, OpenMetadata, and any OL-compatible tool can ingest the event log without transformation.
- **Causal traversal.** `ParentRunFacet` gives free "show lineage of X" queries. The homeostasis loop is now a queryable linked list of decisions.
- **Routing independence.** Routing logic consumes the event log as a standard data source — it can be implemented, iterated, and replaced without touching the engine.
- **Multi-project isolation.** `aisdlc://{project_name}` namespacing prevents collision in shared backends.
- **Laptop-runnable.** Local-first invariant preserves portability. No infrastructure required.

**Negative / Trade-offs:**
- **v1/v2 dual-schema period.** Consumers must handle both until all implementations migrate.
- **UUID generation.** `run.runId` must be a UUID v4. Implementations need a UUID generator at event emission time (trivial in Python/JS; may require a dependency in minimal environments).
- **`OTHER` is semantically lossy.** Routing consumers must read `sdlc:event_type` facet to get semantic type. Top-level `eventType` alone is insufficient for homeostasis events.
- **Facet schema URIs are aspirational.** The JSON Schema files at `_schemaURL` do not exist yet. They must be created before strict OL validation is enabled. Until then, facets are informally validated.

---

## Alternatives Considered

**Keep bespoke schema**: Simpler short-term, but two schemas (iterate + homeostasis) were already diverging. Rejected — the divergence compounds with each new event type.

**OL for iterate events only; bespoke for homeostasis**: Split reduces OL schema pressure but doesn't give a unified consumer surface. Homeostasis events remain opaque to standard tooling. Rejected — "uniformity of metadata is the highest-leverage move for an evolving system."

**Require Marquez backend**: Full OL backend gives richer queries but breaks laptop-runnable invariant and adds infrastructure dependency before the methodology is stable. Rejected — local-first is non-negotiable at this stage.

---

## References

- [ADR-S-008](ADR-S-008-sensory-triage-intent-pipeline.md) — homeostasis pipeline; this ADR defines the OL encoding for pipeline events
- [ADR-S-010](ADR-S-010-event-sourced-spec-evolution.md) — `feature_proposal` and `spec_modified` events; this ADR defines their OL encoding
- [OpenLineage specification](https://openlineage.io/spec/1-0-5/OpenLineage.json)
- [OpenLineage ParentRunFacet](https://openlineage.io/spec/facets/ParentRunFacet.json)
- imp_claude ADR-021 — dual-mode traverse; defines which mode emits which event schema
- [requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — REQ-EVOL-003/004 (event types that this ADR now encodes in OL format)
