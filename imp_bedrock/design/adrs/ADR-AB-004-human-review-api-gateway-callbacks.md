# ADR-AB-004: Human Review via API Gateway Callbacks

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-EVAL-003, REQ-UX-006

---

## Context

The Asset Graph Model specifies three evaluator types: deterministic (F_D), probabilistic (F_P), and human (F_H). The human evaluator is the accountability boundary — AI evaluators assist, but humans decide (REQ-EVAL-003). Additionally, REQ-UX-006 requires that events needing human approval reach the human through configurable notification channels, and escalations must never be silently deferred or lost.

In CLI-based implementations (Claude, Gemini, Codex), human review is synchronous: the iterate agent pauses, presents the artifact diff, and the developer approves or rejects inline. This works because the developer is present in the same terminal session.

Bedrock Genesis operates as a **stateless, serverless** system. Step Functions workflows execute asynchronously. The human reviewer may not be online when an iteration reaches a human-required evaluator gate. The system needs an **asynchronous review mechanism** that:

1. Pauses the iterate workflow at the human gate without consuming compute resources.
2. Notifies the reviewer through their preferred channel (email, Slack, web console, CLI).
3. Accepts the review decision via a secure callback.
4. Resumes the iterate workflow with the decision.
5. Maintains a complete audit trail of who decided what and when.

### Options Considered

1. **Polling-based review** — The iterate workflow writes a review request to DynamoDB. A separate CLI tool or web console polls for pending reviews. The reviewer makes a decision, which the workflow detects on next poll cycle.
2. **WebSocket-based review** — API Gateway WebSocket endpoint maintains a persistent connection to the reviewer. Review requests are pushed in real-time; decisions flow back on the same connection.
3. **Callback pattern** — Step Functions emits a task token at the human gate. A Lambda sends a notification (SNS) with a callback URL (API Gateway). The reviewer clicks approve/reject. The callback Lambda validates the token and resumes Step Functions.

---

## Decision

**We adopt the callback pattern (Option 3): Step Functions `waitForTaskToken` + API Gateway REST callback + SNS multi-channel notification.**

### Review Flow

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        ITERATE STATE MACHINE                           │
│                                                                        │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────────────┐  │
│  │ F_D Evaluate │───▶│ F_P Evaluate │───▶│ Human Required?           │  │
│  │ (Lambda)     │    │ (Bedrock)    │    │ (check edge config)       │  │
│  └──────────────┘    └──────────────┘    └─────────┬─────────────────┘  │
│                                              Yes   │   No              │
│                                                    ▼    ▼              │
│                                          ┌─────────────┐  Continue     │
│                                          │ Emit Task   │              │
│                                          │ Token        │              │
│                                          │ (waitFor     │              │
│                                          │  TaskToken)  │              │
│                                          └──────┬──────┘              │
│                                                 │                      │
│                        WORKFLOW PAUSED ──────────┘                      │
│                        (no compute cost)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      NOTIFICATION LAMBDA                               │
│                                                                        │
│  Receives: task_token, edge_context, artifact_diff, evaluator_results  │
│                                                                        │
│  1. Generate time-limited callback URLs:                               │
│     - POST /api/review/{review_id}/approve?token={signed_token}        │
│     - POST /api/review/{review_id}/reject?token={signed_token}         │
│                                                                        │
│  2. Store review request in DynamoDB reviews table:                    │
│     - review_id, task_token, callback_urls, ttl, status=pending        │
│     - artifact_diff, evaluator_results, edge_context, feature_state    │
│                                                                        │
│  3. Dispatch notifications via configured channels:                    │
│     - SNS → Email (direct)                                             │
│     - SNS → Lambda → Slack API (webhook)                               │
│     - SNS → Lambda → Custom webhook (configurable)                     │
│     - DynamoDB entry → Web console polls pending reviews               │
│     - DynamoDB entry → CLI tool queries pending reviews                │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      REVIEWER (Human)                                  │
│                                                                        │
│  Receives notification with:                                           │
│  - Summary of what changed (artifact diff)                             │
│  - Evaluator results so far (F_D pass/fail, F_P confidence scores)    │
│  - Edge context (which transition, which feature vector)               │
│  - Approve / Reject links (or CLI command)                             │
│                                                                        │
│  Decision paths:                                                       │
│  - Click "Approve" link → API Gateway callback                         │
│  - Click "Reject" link (with optional reason) → API Gateway callback   │
│  - CLI: gen-review --approve --review-id abc123                        │
│  - Web console: review dashboard with approve/reject buttons           │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  API GATEWAY CALLBACK LAMBDA                           │
│                                                                        │
│  POST /api/review/{review_id}/{decision}                               │
│                                                                        │
│  1. Validate signed token (HMAC-SHA256, check expiry)                  │
│  2. Load review record from DynamoDB                                   │
│  3. Verify status = pending (reject duplicate decisions)               │
│  4. Record decision:                                                   │
│     - Update DynamoDB: status=approved|rejected, decided_by, decided_at│
│     - Emit review_completed event to DynamoDB events table             │
│  5. Resume Step Functions:                                             │
│     - SendTaskSuccess (approve) with review metadata                   │
│     - SendTaskFailure (reject) with reason                             │
│                                                                        │
│  Step Functions resumes iterate workflow:                               │
│  - Approve → promote asset, emit edge_converged event                  │
│  - Reject → log rejection, re-iterate or escalate per policy           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Callback URL Structure

```
https://{api-id}.execute-api.{region}.amazonaws.com/prod/review/{review_id}/approve?token={signed_token}
https://{api-id}.execute-api.{region}.amazonaws.com/prod/review/{review_id}/reject?token={signed_token}&reason={optional}
```

- **`review_id`**: UUID identifying this specific review request.
- **`signed_token`**: HMAC-SHA256 signed payload containing `review_id`, `task_token_hash`, and `expiry_timestamp`. Prevents forgery and replay.
- **TTL**: Configurable in `project_constraints.yml` under `review.callback_ttl_days` (default: 7 days). After expiry, the callback URL returns 410 Gone and the Step Functions workflow times out to its configured escalation path.

### Review Payload

The notification sent to the reviewer includes a structured payload:

```yaml
review_id: "rev-2026-02-23-abc123"
project_id: "my-project"
feature: "REQ-F-AUTH-001"
edge: "requirements_design"
iteration: 3

artifact_diff:
  type: "unified_diff"
  summary: "Added OAuth2 flow to authentication design"
  lines_added: 47
  lines_removed: 12

evaluator_results:
  deterministic:
    - name: "schema_validation"
      result: "pass"
    - name: "req_key_coverage"
      result: "pass"
      details: "3/3 REQ keys traced"
  probabilistic:
    - name: "coherence_check"
      result: "pass"
      confidence: 0.92
    - name: "gap_detection"
      result: "warn"
      details: "Consider error handling for token refresh"

feature_vector_state:
  current_edge: "requirements_design"
  edges_completed: ["intent_requirements"]
  convergence_progress: "2/3 evaluators passed"

callback_urls:
  approve: "https://api.example.com/review/rev-abc123/approve?token=..."
  reject: "https://api.example.com/review/rev-abc123/reject?token=..."
  expires_at: "2026-03-02T10:30:00Z"
```

### Notification Channels

Channels are configured in `project_constraints.yml`:

```yaml
notification_channels:
  - type: email
    enabled: true
    sns_topic_arn: "arn:aws:sns:us-east-1:123456789:review-notifications"

  - type: slack
    enabled: true
    webhook_url: "https://hooks.slack.com/services/T.../B.../..."
    channel: "#dev-reviews"

  - type: webhook
    enabled: false
    url: "https://internal.example.com/webhooks/review"

  - type: review_queue
    enabled: true   # Always active as fallback (REQ-UX-006)
```

The `review_queue` channel is always active as a fallback, ensuring escalations are never silently lost (REQ-UX-006 mandate). Even if email and Slack delivery fail, the review request exists in DynamoDB and is visible via `gen-status` and `gen-review --list`.

---

## Rationale

### Why Callback Pattern (vs Polling)

1. **No wasted compute**: Step Functions `waitForTaskToken` consumes zero compute while waiting. Polling requires either a long-running process or periodic Lambda invocations checking DynamoDB — both wasteful.
2. **Instant resume**: When the reviewer clicks approve, the callback Lambda immediately resumes Step Functions. No polling interval delay (which could be minutes).
3. **Push notification**: The reviewer receives a notification when the review is ready, rather than having to remember to check a queue. This significantly reduces review latency in practice.
4. **Native Step Functions support**: `waitForTaskToken` is a first-class Step Functions integration pattern, designed exactly for human-in-the-loop workflows. Using it aligns with AWS best practices and gets reliability guarantees (automatic retries, state persistence) for free.

### Why Callback Pattern (vs WebSocket)

1. **Infrastructure simplicity**: WebSocket connections require persistent connection management, connection tracking (DynamoDB), heartbeat handling, and reconnection logic. The callback pattern is stateless — a single API Gateway endpoint handles all callbacks.
2. **Multi-channel support**: WebSocket only works for connected clients. The callback pattern works with any channel that can deliver a URL (email, Slack, SMS, webhook). The reviewer does not need to be online when the review is created.
3. **Cost**: WebSocket API Gateway charges per connection-minute. Reviews can take hours or days. A callback URL costs nothing until clicked.

### Why SNS for Notification Delivery

1. **Fan-out**: A single SNS publish fans out to multiple subscribers (email, Lambda for Slack, Lambda for webhook) simultaneously. Adding a new notification channel is adding a new SNS subscription, not modifying the notification Lambda.
2. **Delivery guarantees**: SNS provides at-least-once delivery with retry policies. Email delivery via SNS handles SMTP complexity.
3. **Audit**: SNS delivery status logging provides proof that the notification was sent, supporting the REQ-UX-006 requirement that escalations must never be silently lost.

---

## Consequences

### Positive

- **Asynchronous review**: The reviewer does not need to be online when the iteration reaches the human gate. They can review hours or days later via any configured channel.
- **Multi-channel delivery**: Email, Slack, web console, CLI, and custom webhooks are all supported. Teams choose their preferred workflow without code changes.
- **Audit trail**: Every review request, notification delivery, and decision is recorded in DynamoDB and Step Functions execution history. Full accountability chain from iteration to decision to resume.
- **Zero idle cost**: Step Functions `waitForTaskToken` consumes no compute while waiting for the human decision. The workflow can wait days without cost.
- **Native AWS integration**: Uses standard Step Functions callback pattern, API Gateway REST endpoints, and SNS notification — all managed services with built-in reliability.

### Negative

- **Callback URL management**: Signed callback URLs must be generated, validated, and expired. Key rotation for HMAC signing adds operational overhead.
- **Timeout handling**: If the reviewer does not respond within the TTL, the Step Functions workflow must handle the timeout gracefully. This requires a timeout path in the state machine (escalate to another reviewer, auto-reject, or extend TTL).
- **Stale reviews**: If the project state changes significantly while a review is pending (e.g., the feature vector is updated by a parallel iteration), the review payload may be stale. The reviewer could approve an artifact that no longer reflects current state.
- **SNS delivery failures**: Email can bounce, Slack webhooks can fail, and external webhooks can timeout. While the `review_queue` fallback ensures the request is not lost, the reviewer may not receive timely notification.

### Mitigation

- **Automatic key rotation**: HMAC signing keys stored in AWS Secrets Manager with automatic rotation schedule. Lambda retrieves current key at callback validation time.
- **Timeout escalation**: Step Functions state machine includes a `TimeoutSeconds` on the `waitForTaskToken` state. On timeout, a fallback path either re-notifies, escalates to a secondary reviewer, or creates an `escalation_timeout` event in the events table.
- **Staleness detection**: The callback Lambda checks the feature vector's `last_modified` timestamp against the review request's `created_at`. If the feature has been modified since the review was created, the callback returns a warning and the reviewer can re-fetch the current state before deciding.
- **Delivery monitoring**: CloudWatch alarms on SNS delivery failure metrics. If delivery failures exceed threshold, an `interoceptive_signal` event is emitted to the events table for the sensory service to surface.
- **Idempotent callbacks**: The callback Lambda checks `status = pending` before processing. Duplicate clicks on approve/reject URLs are rejected with 409 Conflict, preventing double-decision.

---

## References

- [ADR-AB-001-bedrock-runtime-as-platform.md](ADR-AB-001-bedrock-runtime-as-platform.md) — Platform binding (Bedrock as runtime)
- [ADR-AB-002-iterate-engine-step-functions.md](ADR-AB-002-iterate-engine-step-functions.md) — Iterate engine (Step Functions workflow contains the human gate)
- [ADR-AB-005-event-sourcing-dynamodb.md](ADR-AB-005-event-sourcing-dynamodb.md) — Event sourcing (review events stored in DynamoDB events table)
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) §2.2 (Evaluator Framework), §2.6 (Developer Tooling Surface)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.1 (Human Evaluator Type)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-EVAL-003 (Human Accountability), REQ-UX-006 (Human Gate Awareness)
