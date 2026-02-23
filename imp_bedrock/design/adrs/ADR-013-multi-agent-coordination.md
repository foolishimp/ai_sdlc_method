# ADR-013: Multi-Agent Coordination — DynamoDB Conditional Writes

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-COORD-001 (Agent Identity), REQ-COORD-002 (Feature Assignment via Events), REQ-COORD-003 (Work Isolation), REQ-COORD-004 (Markov-Aligned Parallelism), REQ-COORD-005 (Role-Based Evaluator Authority)
**Supersedes**: None (new capability)

---

## Context

As the AI SDLC transitions from a single-agent "pilot" to a multi-agent "fleet," concurrent agents must not corrupt project state or perform redundant work. The Claude reference implementation (ADR-013) solves this with immutable event-sourced claims, inbox staging, and a single-writer filesystem serialiser. This works well for single-machine CLI workflows where all agents share a local filesystem.

Bedrock Genesis operates in a cloud-native environment where coordination participants are distributed:

- **Step Functions workflows** — multiple iterate executions running concurrently for different features or edges.
- **Lambda functions** — stateless evaluators and routing functions executing in parallel.
- **CI/CD pipelines** — external systems triggering iterations via API Gateway.
- **Developer CLI tools** — local developers invoking commands against the same project state.

There is no shared filesystem. There is no single persistent process to act as serialiser. The inbox/serialiser pattern from the CLI design does not translate to serverless architecture. However, the cloud environment provides a stronger primitive: **DynamoDB conditional writes** deliver exactly-once claim semantics at the database level, eliminating the need for application-level serialisation entirely.

### Options Considered

1. **SQS-based claim queue** — Agents submit claims to an SQS FIFO queue. A single consumer Lambda processes claims in order, writing grants/rejections to DynamoDB. Replicates the serialiser pattern in the cloud.
2. **DynamoDB conditional writes** — Each claim attempt is a `PutItem` with `attribute_not_exists` condition expression. DynamoDB atomically grants or rejects. No queue, no consumer, no serialiser.
3. **Redis/ElastiCache distributed lock** — Agents acquire distributed locks via Redis SETNX. Classic approach but introduces a stateful dependency (Redis cluster) into a serverless architecture.
4. **Step Functions semaphore pattern** — Use Step Functions Map state with concurrency limits. Works for intra-workflow coordination but not across independent workflows.

---

## Decision

**We adopt DynamoDB conditional writes (Option 2) for multi-agent coordination. Claim acquisition is a single atomic `PutItem` with `attribute_not_exists` condition. No serialiser process, no queue, no distributed lock. All coordination state is stored in DynamoDB and derivable from the events table.**

### Claim Protocol

```
Agent A (Step Functions execution)         Agent B (CI/CD trigger)
   │                                           │
   ▼                                           ▼
┌──────────────────────────────────┐    ┌──────────────────────────────────┐
│ DynamoDB PutItem                 │    │ DynamoDB PutItem                 │
│   PK: project_id                │    │   PK: project_id                │
│   SK: CLAIM#feature#edge        │    │   SK: CLAIM#feature#edge        │
│   agent_id: "sf-exec-abc123"    │    │   agent_id: "cicd-pipeline-42"  │
│   Condition: attribute_not_exists│    │   Condition: attribute_not_exists│
└──────────┬───────────────────────┘    └──────────┬───────────────────────┘
           │                                       │
           ▼                                       ▼
    PutItem succeeds                        ConditionalCheckFailedException
    (claim granted)                         (claim rejected — A holds it)
           │                                       │
           ▼                                       ▼
    Emit edge_started event                 Emit claim_rejected event
    to DynamoDB events table                to DynamoDB events table
           │                                       │
           ▼                                       ▼
    Begin iteration                         Re-route to different
    (Step Functions)                         feature or edge
```

### Claim Lifecycle

1. **Acquire**: `PutItem` with `attribute_not_exists(SK)` condition. If condition succeeds, the agent holds the claim. If condition fails (`ConditionalCheckFailedException`), the claim is rejected.

2. **Heartbeat**: The agent updates a `last_active` attribute on the claim record periodically (every N iterations). This is a simple `UpdateItem`, not conditional — only the holder updates.

3. **Release on convergence**: On `edge_converged`, the agent deletes the claim record and emits an `edge_converged` event. The claim is freed atomically.

4. **Release on abandonment**: If the agent abandons work (error, timeout, manual cancel), it deletes the claim record and emits an `edge_released` event.

5. **Expiry**: DynamoDB TTL on claim records provides automatic expiry. If an agent crashes without releasing, the claim record expires after `claim_ttl_seconds` (configurable, default: 3600). An EventBridge Scheduler rule runs a Lambda that detects expired claims and emits `claim_expired` events.

```
DynamoDB Claims Record:

PK:          project_id                    (String)
SK:          CLAIM#feature_id#edge         (String)
agent_id:    "sf-exec-abc123"              (String)
agent_role:  "tdd_engineer"                (String)
claimed_at:  "2026-02-23T10:30:00Z"        (String, ISO-8601)
last_active: "2026-02-23T10:35:00Z"        (String, ISO-8601)
ttl:         1708689600                    (Number, epoch seconds)
```

### DynamoDB Conditional Write Semantics

The conditional write provides **exactly-once claim semantics** without any application-level coordination:

```python
# Claim acquisition (Lambda or Step Functions state)
try:
    table.put_item(
        Item={'PK': project_id, 'SK': f'CLAIM#{feature_id}#{edge}',
              'agent_id': agent_id, 'agent_role': agent_role,
              'claimed_at': datetime.utcnow().isoformat(),
              'ttl': int(time.time()) + claim_ttl_seconds},
        ConditionExpression='attribute_not_exists(SK)')
    # Claim granted — emit edge_started event
except ClientError as e:
    if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
        # Claim rejected — emit claim_rejected event with holding agent info
        pass
```

This replaces the entire inbox/serialiser mechanism from ADR-013 (Claude) with a single DynamoDB API call.

### Work Isolation

Agents iterate in isolated S3 prefixes:

```
s3://project-bucket/agents/<agent_id>/drafts/
s3://project-bucket/agents/<agent_id>/scratch/
```

Promotion to shared state (`s3://project-bucket/assets/`) requires:
- All evaluators for the edge pass (Step Functions workflow completes successfully)
- Human review for edges with `human_required: true` (ADR-AB-004 callback)
- DynamoDB Streams Lambda updates the features table on `edge_converged`

Agent state in S3 is ephemeral. On crash, only emitted DynamoDB events persist. Drafts and scratch are disposable — the iterate engine reconstructs from the last converged asset.

### Stale Claim Detection

An EventBridge Scheduler rule invokes a Lambda every 15 minutes that:

1. Scans claims table for records where `last_active` exceeds `stale_threshold_seconds` (configurable, default: 1800).
2. For each stale claim, emits a `claim_expired` event to the DynamoDB events table.
3. Stale claims are **not auto-released** — human decides. The `claim_expired` event surfaces in `/api/status` health checks and can trigger SNS notifications.

DynamoDB TTL provides a hard backstop: even if the stale detection Lambda fails, claim records expire after `claim_ttl_seconds`.

### Role-Based Evaluator Authority

`agent_roles.yml` is stored in S3 alongside edge configs. The routing Lambda reads it to enforce role-based authority:

```yaml
roles:
  architect:
    converge_edges: [intent_requirements, requirements_design, design_code]
  tdd_engineer:
    converge_edges: [code_unit_tests, design_test_cases]
  cicd_agent:
    converge_edges: [uat_tests, cicd]
  full_stack:
    converge_edges: [all]  # single-agent backward compat
```

When an agent attempts to converge an edge outside its role authority, the `ConvergenceCheck` state in the Step Functions workflow emits a `convergence_escalated` event and routes to the human review path (ADR-AB-004) instead of promoting.

### Single-Agent Mode (Backward Compatible)

In single-agent mode:
- `agent_id` defaults to `"primary"`, `agent_role` defaults to `"full_stack"`.
- No claim records are written — `edge_started` is emitted directly to the events table.
- The Step Functions workflow skips the claim acquisition state.
- All coordination machinery (claims table, stale detection, role checking) is dormant — zero cost when unused.

### Markov-Aligned Parallelism

The routing Lambda in `POST /api/start` uses the inner product check (spec section 6.7) to route concurrent agents:

- **Zero inner product** (no shared modules between features): freely assign to parallel Step Functions executions. No coordination overhead.
- **Non-zero inner product** (shared modules): warn in the routing response, suggest sequential ordering. If the caller proceeds anyway, the claim protocol prevents conflicting concurrent edits.
- Feature priority tiers (closest-to-complete first) apply per-agent, skipping already-claimed features.

The inner product is computed by the routing Lambda from DynamoDB feature records and the shared module dependency graph stored in the features table.

---

## Rationale

### Why DynamoDB Conditional Writes (vs SQS Queue)

1. **No consumer process** — The SQS approach replicates the serialiser pattern: a single consumer Lambda must poll the queue, resolve conflicts, and write results. This is a stateful dependency in a stateless architecture. DynamoDB conditional writes are atomic at the database layer — no consumer needed.

2. **Lower latency** — A `PutItem` with condition expression is a single API call (~5ms typical). The SQS approach involves: produce message (~10ms), consumer polls (~100ms interval), consumer processes (~5ms), consumer writes result (~5ms). Total: ~120ms minimum.

3. **Simpler failure model** — If a DynamoDB `PutItem` fails (throttling, transient error), the caller retries directly. If an SQS consumer fails mid-processing, the message returns to the queue after visibility timeout, creating duplicate processing risk.

4. **Native TTL** — DynamoDB TTL handles claim expiry without application code. SQS message retention is unrelated to claim lifecycle.

### Why DynamoDB Conditional Writes (vs Redis)

1. **Serverless alignment** — Redis (ElastiCache) requires a persistent cluster with provisioned capacity, running 24/7 regardless of project activity. DynamoDB on-demand costs nothing when idle.
2. **Durability** — Redis is in-memory. Cluster failures can lose claim state. DynamoDB is durable with cross-AZ replication.
3. **No operational overhead** — DynamoDB is fully managed. Redis requires cluster sizing, patching, and failover configuration.

### Advantage Over Filesystem Serialiser

| Concern | Filesystem Serialiser | DynamoDB Conditional Write |
|:---|:---|:---|
| Atomicity | Single-writer process (software guarantee) | Database-level (hardware guarantee) |
| Failure mode | Ghost inboxes if process crashes | Automatic TTL expiry |
| Scalability | Single machine | Global table, multi-region |
| Observability | Parse events.jsonl | DynamoDB Streams + CloudWatch |
| Recovery | Replay events.jsonl | DynamoDB point-in-time recovery |
| Latency | Depends on serialiser poll interval | Single API call (~5ms) |

DynamoDB conditional writes provide **stronger guarantees with less code**. The database replaces the serialiser.

---

## Consequences

### Positive

- **Zero deadlocks** — No locks means no deadlocks. Conditional writes are non-blocking: they succeed or fail immediately.
- **Exactly-once claims** — DynamoDB's conditional write is atomic at the database layer. There is no window where two agents can both believe they hold the same claim.
- **No serialiser process** — Eliminates the single-writer process that the filesystem design requires. One fewer component to deploy, monitor, and recover.
- **Automatic expiry** — DynamoDB TTL handles crashed-agent cleanup without application code. No stale lock files, no manual intervention for common failure cases.
- **High concurrency** — Orthogonal features (zero inner product) run with zero coordination overhead. Claims on different feature+edge combinations never contend.
- **Backward compatible** — Single-agent mode works with `agent_id="primary"` and no claim records. The event schema is identical.
- **Cost-efficient** — On-demand DynamoDB pricing means coordination costs scale linearly with agent count. Zero cost when no agents are coordinating.

### Negative

- **Hot partition risk** — If many agents contend for the same feature+edge, the partition becomes a hot key. Mitigated: Markov-aligned routing avoids this by design — agents are routed to orthogonal features.
- **TTL granularity** — DynamoDB TTL is approximate (items may persist up to 48 hours beyond TTL). The stale detection Lambda provides timely detection; TTL is the hard backstop.
- **No claim ordering** — Unlike the serialiser (deterministic lexicographic order), DynamoDB conditional writes are first-writer-wins. Acceptable for methodology purposes — any valid agent can hold any edge within its role authority.
- **Vendor lock** — DynamoDB conditional writes are AWS-specific. Mitigated: the protocol is documented as compare-and-swap semantics, portable to Cosmos DB or Cloud Spanner.

---

## Coordination Event Types

This ADR preserves the 5 coordination event types from the Claude reference design, adapted for DynamoDB storage:

| Event Type | Where Written | Purpose |
|:---|:---|:---|
| `edge_claim` | DynamoDB claims record (not events table) | Agent proposes to work on feature+edge |
| `claim_rejected` | DynamoDB events table | Conflict: feature+edge already claimed |
| `edge_released` | DynamoDB events table | Agent voluntarily abandons claim |
| `claim_expired` | DynamoDB events table | Stale claim detected by scheduled Lambda |
| `convergence_escalated` | DynamoDB events table | Agent converged outside role authority |

Note: `edge_claim` is realised as a DynamoDB claims record, not an event. It never appears in the events table. The `PutItem` with condition transforms it into either `edge_started` (success, written to events table) or `claim_rejected` (conflict, written to events table). This parallels the Claude design where `edge_claim` is inbox-local and the serialiser transforms it into resolved facts.

---

## References

- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) — Platform binding (DynamoDB conditional writes for coordination)
- [ADR-AB-005](ADR-AB-005-event-sourcing-dynamodb.md) — Event sourcing (DynamoDB events table schema, coordination records)
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding (role-based evaluator authority maps to ambiguity classification; `claim_rejected` and `convergence_escalated` are affect-phase signals)
- [ADR-013 (Claude)](../../imp_claude/design/adrs/ADR-013-multi-agent-coordination.md) — Reference design (inbox/serialiser pattern, Markov alignment, role-based authority)
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) — Bedrock implementation design
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) — Canonical model, section 6.7 (Basis Projections), section 7.5 (Event Sourcing), section 7.7.6 (Markov Boundaries)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — Requirements baseline, section 12 (Multi-Agent Coordination)
