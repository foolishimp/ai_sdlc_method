# ADR-AB-005: Event Sourcing via DynamoDB

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-LIFE-005 (Event Sourcing), REQ-COORD-002 (Feature Assignment via Events)

---

## Context

The AI SDLC Asset Graph Model treats the event log as the canonical source of truth for all project state. Feature vectors, status views, and coordination state are derived projections — they are regenerated from events, never edited directly.

The Claude reference implementation uses a local append-only file (`events.jsonl`) with a single-writer serialiser for multi-agent coordination (ADR-013). This works well for single-machine CLI workflows but does not extend to cloud-native, multi-service, multi-region scenarios where Bedrock Genesis operates.

Bedrock Genesis needs an event store that provides:

1. **Atomic writes** — multiple concurrent Lambda functions and Step Functions workflows emit events simultaneously.
2. **Queryable history** — status, feature trajectory, and trace projections require filtering by feature, edge, time range, and agent.
3. **Stream processing** — derived projections (feature vector updates, STATUS regeneration) must react to new events in near-real-time.
4. **Coordination primitives** — multi-agent claim/release must be atomic and conflict-free.
5. **Hybrid local support** — developers working locally need access to events without requiring constant cloud connectivity.

### Options Considered

1. **S3 append-only log** — Append JSON lines to an S3 object. Simple, cheap storage. However: S3 does not support atomic appends (each write replaces the object), has no native stream processing, and queries require full object scans. Coordination would require separate locking mechanisms.

2. **DynamoDB events table** — Each event is a separate item with composite key. Supports conditional writes for coordination, DynamoDB Streams for projections, and flexible queries via GSIs. Native TTL for transient records. Pay-per-request pricing aligns with serverless model.

3. **EventBridge event bus only** — Events published to EventBridge for routing. However: EventBridge is a routing layer, not a persistence layer. No native replay capability. Event archive has limited query support and 24-hour replay latency. Not suitable as a source of truth.

---

## Decision

**DynamoDB is the canonical event store for Bedrock Genesis, with local `events.jsonl` maintained as a hybrid cache for developer experience.**

### Events Table Schema

```
Table: {project_prefix}-events

Primary Key:
  PK (Partition Key): project_id          (String)
  SK (Sort Key):      timestamp#event_id  (String, ISO-8601#UUID-v7)

Attributes:
  event_type    (String)   — one of the canonical event types
  payload       (Map)      — event-specific data (feature, edge, agent_id, etc.)
  agent_id      (String)   — emitting agent ("primary" for single-agent mode)
  feature_id    (String)   — affected feature vector key (nullable)
  edge          (String)   — affected edge (nullable)
  ttl           (Number)   — epoch seconds; set ONLY on claim records, NULL for events

GSI-1 (feature-time):
  PK: feature_id
  SK: timestamp#event_id
  — enables: feature trajectory queries, /gen-trace --req

GSI-2 (event-type-time):
  PK: event_type
  SK: timestamp#event_id
  — enables: type-filtered queries (all edge_started, all reviews)

GSI-3 (agent-time):
  PK: agent_id
  SK: timestamp#event_id
  — enables: agent activity view, stale claim detection
```

### Canonical Event Types

The 10 methodology event types are preserved without modification:

| Event Type | Origin | Purpose |
|:---|:---|:---|
| `project_initialized` | `/gen-init` | Workspace scaffolded |
| `iteration_completed` | iterate engine | Asset iteration finished |
| `edge_started` | iterate engine | Edge work begun |
| `edge_converged` | iterate engine | Edge evaluators satisfied |
| `spawn_created` | `/gen-spawn` | New feature/discovery/spike/hotfix vector |
| `spawn_folded_back` | iterate engine | Spawn results merged to parent |
| `checkpoint_created` | `/gen-checkpoint` | Immutable snapshot taken |
| `review_completed` | `/gen-review` | Human evaluator decision recorded |
| `gaps_validated` | `/gen-gaps` | Coverage analysis completed |
| `release_created` | `/gen-release` | Release manifest generated |

### Coordination Event Types

Five additional event types support multi-agent coordination (aligned with ADR-013):

| Event Type | Purpose | TTL |
|:---|:---|:---|
| `edge_claim` | Agent proposes to work on feature+edge | Yes (claim TTL) |
| `claim_rejected` | Conflict: feature+edge already claimed | No (permanent) |
| `edge_released` | Agent voluntarily abandons claim | No (permanent) |
| `claim_expired` | Stale claim detected by monitor | No (permanent) |
| `convergence_escalated` | Agent converged outside role authority | No (permanent) |

Claim records (`edge_claim`) use DynamoDB TTL for automatic expiration. All other events are permanent — no TTL.

### Coordination via Conditional Writes

Multi-agent coordination uses DynamoDB conditional expressions instead of inbox staging:

```
PutItem(
  PK = project_id,
  SK = "CLAIM#feature_id#edge",
  agent_id = requesting_agent,
  ttl = now + claim_duration
)
ConditionExpression: attribute_not_exists(SK)
```

- If the condition succeeds: claim granted, `edge_started` event emitted.
- If the condition fails (ConditionalCheckFailedException): claim rejected, `claim_rejected` event emitted with the holding agent's ID read from the existing item.

This replaces the file-based inbox/serialiser pattern from ADR-013 with DynamoDB's native atomic conditional writes — achieving the same "exactly one winner" semantics without a single-writer process.

### DynamoDB Streams for Derived Projections

A DynamoDB Stream on the events table triggers a Lambda function that maintains derived views:

1. **Feature vector state** — updated in the `features` DynamoDB table on `edge_converged`, `spawn_created`, `spawn_folded_back` events.
2. **Status projection** — regenerated on any methodology event. Cached in S3 or DynamoDB for fast `/gen-status` queries.
3. **Trace index** — REQ-key to event mapping updated on `iteration_completed` and `edge_converged`.

Stream processing is eventually consistent (typically sub-second latency). Projections are always regenerable from a full event table scan.

### Local Hybrid Cache

For local developer experience, `events.jsonl` is maintained as a synchronized cache:

- **Cloud-to-local sync**: Lambda function triggered by DynamoDB Stream exports new events to an S3 object (`events-export/events.jsonl`). Developer pulls via `aws s3 sync` or CLI wrapper command.
- **Local-to-cloud sync**: CLI tool reads local `events.jsonl` additions and writes them to DynamoDB via `BatchWriteItem`. Idempotent — `event_id` (UUID-v7) prevents duplicates.
- **Offline mode**: Developer works locally with `events.jsonl` as sole store. On reconnect, sync pushes local events to DynamoDB. Conflict resolution: DynamoDB conditional writes reject duplicate `event_id` values.

The local file is a **cache**, not the source of truth. DynamoDB is authoritative. If `events.jsonl` is deleted, it can be fully reconstructed from DynamoDB.

### Single-Agent Backward Compatibility

In single-agent mode:

- `agent_id` defaults to `"primary"` on all events.
- No claim records are written — `edge_started` is emitted directly.
- DynamoDB Streams and projections work identically.
- Local-only mode (no cloud) degrades to `events.jsonl`-only, matching Claude reference behavior.

---

## Rationale

### Why DynamoDB (vs S3 or EventBridge)

1. **Atomic conditional writes**: DynamoDB's `ConditionExpression` provides the exact primitive needed for multi-agent coordination — compare-and-swap without external locking. S3 has no equivalent; EventBridge is fire-and-forget.

2. **Native stream processing**: DynamoDB Streams deliver ordered, exactly-once event notifications to Lambda. S3 event notifications are eventually consistent and can miss events under high write rates.

3. **Flexible querying**: GSIs enable queries by feature, event type, agent, and time range — all required by `/gen-status`, `/gen-trace`, and `/gen-zoom`. S3 requires full object scans; EventBridge archive has limited query support.

4. **Pay-per-request pricing**: On-demand capacity mode charges per read/write unit. For typical SDLC projects (hundreds to thousands of events), costs are negligible. No provisioned capacity to manage.

5. **TTL for claims**: DynamoDB TTL automatically removes expired claim records without application logic. This replaces the serialiser's stale-claim-detection timer from ADR-013.

6. **Hybrid compatibility**: The event schema is identical whether stored in DynamoDB items or JSONL lines. The `event_id` (UUID-v7) provides monotonic ordering and deduplication across both stores.

---

## Consequences

### Positive

- **Atomic coordination**: Conditional writes eliminate the need for a single-writer serialiser process. Multiple Step Functions workflows and Lambda functions can emit events concurrently without corruption.
- **Stream-driven projections**: Feature vector state, status views, and trace indices are updated automatically and consistently via DynamoDB Streams.
- **Query flexibility**: Any event dimension (feature, edge, agent, time, type) is queryable via table scan or GSI. Supports the full set of `/gen-status`, `/gen-trace`, and `/gen-zoom` queries.
- **Conditional writes for coordination**: The claim protocol maps directly to DynamoDB's native `attribute_not_exists` condition — no application-level locking.
- **Cost-efficient**: On-demand pricing means zero cost when idle. Event storage costs scale linearly with project activity.

### Negative

- **DynamoDB cost for hot tables**: Projects with high iteration rates (many concurrent agents, rapid convergence loops) will incur proportional read/write costs. Mitigated: on-demand pricing auto-scales; reserved capacity available for predictable workloads.
- **Eventual consistency for streams**: DynamoDB Streams deliver events with sub-second latency, but projections are not immediately consistent after a write. Mitigated: projections include a `last_updated` timestamp; consumers can perform a direct table read for strong consistency when needed.
- **Local sync complexity**: Maintaining bidirectional sync between DynamoDB and `events.jsonl` requires careful conflict handling. Mitigated: UUID-v7 event IDs provide natural deduplication; DynamoDB is always authoritative; local file is a disposable cache.
- **Vendor lock-in**: DynamoDB is AWS-specific. Mitigated: the event schema is platform-agnostic JSON; only the storage and query layer is DynamoDB-specific. Migration to another store requires changing the persistence adapter, not the event format.

---

## References

- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) §1.1, §4.4 (DynamoDB as event store and coordination)
- [ADR-AB-001-bedrock-runtime-as-platform.md](ADR-AB-001-bedrock-runtime-as-platform.md) — platform binding decision
- [ADR-013-multi-agent-coordination.md](../../../imp_claude/design/adrs/ADR-013-multi-agent-coordination.md) — immutable event-sourced claims (reference design, inbox/serialiser pattern)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §7.5 (Event Sourcing)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) §9 (Lifecycle), §12 (Multi-Agent Coordination)
