# ADR-AB-008: Local-Cloud Hybrid Workspace Model

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-TOOL-002, REQ-CTX-001

---

## Context

The AI SDLC Asset Graph Model uses `.ai-workspace/` as the local file-system workspace for events, feature vectors, agent state, and configuration. The Claude and Gemini implementations operate entirely within this local workspace, which works well for single-developer, single-machine usage.

The Bedrock Genesis implementation introduces a tension: cloud services (Step Functions, Lambda, DynamoDB, S3) are the execution substrate, but developers still need a local workspace for authoring configurations, reviewing state, and working offline. Two distinct usage patterns must be supported:

1. **Developer workflow**: A developer authors `graph_topology.yml`, edge parameters, and project constraints locally. They iterate on configurations, run local validation, and push finalized configs to the cloud for execution.
2. **Cloud execution workflow**: Step Functions and Lambda execute iterate operations, writing events to DynamoDB and artifacts to S3. The developer needs to pull these results locally for review, debugging, and further iteration.

Additionally, team collaboration requires shared state. Multiple developers working on the same project need a consistent view of events, feature vectors, and convergence status. Local-only workspaces cannot provide this. CI/CD pipelines also need access to methodology state without requiring a local workspace at all.

The workspace model must also support offline development. A developer on a plane should be able to review current state, author new configurations, and even run iterate operations against Bedrock APIs (which only require internet access, not cloud state infrastructure).

---

## Options Considered

### Option 1: Cloud-Only Workspace

All state lives in S3 and DynamoDB. No local `.ai-workspace/` directory.

- **Pros**: Single source of truth; no sync needed; team collaboration is inherent.
- **Cons**: Poor developer experience (every state query requires AWS API calls); no offline capability; latency on every file read; breaks compatibility with the methodology's local workspace contract; developers cannot use standard file tools (grep, editors) to inspect state.

### Option 2: Local-Only Workspace

All state lives in `.ai-workspace/`. Cloud services read from and write to the local filesystem (e.g., via mounted EFS).

- **Pros**: Familiar developer experience; full offline capability; compatible with Claude/Gemini workspace model.
- **Cons**: No team collaboration; CI/CD pipelines cannot access state; EFS mounting is fragile and region-bound; does not leverage cloud-native state management (DynamoDB consistency, S3 durability).

### Option 3: Hybrid Workspace -- CHOSEN

Local `.ai-workspace/` for developer experience, S3/DynamoDB for cloud services. Bi-directional sync with clear ownership rules per resource type.

- **Pros**: Best of both worlds; works offline; team collaboration via cloud; CI/CD integration; familiar local workspace.
- **Cons**: Sync conflicts are possible; eventual consistency between local and cloud; additional tooling for sync management.

---

## Decision

**We adopt a hybrid workspace model (Option 3): local `.ai-workspace/` for developer-facing state and S3/DynamoDB for cloud-facing state, with defined sync directions per resource type.**

### Sync Direction Rules

Each resource type has a designated source of truth and sync direction:

| Resource | Source of Truth | Sync Direction | Mechanism |
|----------|----------------|----------------|-----------|
| Graph topology, edge params, profiles | Local filesystem | Local -> Cloud | `aws s3 sync` to config bucket |
| Project constraints | Local filesystem | Local -> Cloud | `aws s3 sync` to config bucket |
| Events (`events.jsonl`) | DynamoDB | Cloud -> Local | DynamoDB export to local JSONL |
| Feature vectors | DynamoDB | Cloud -> Local | DynamoDB query to local YAML |
| Iterate artifacts (generated code, designs) | S3 | Cloud -> Local | `aws s3 sync` from artifacts bucket |
| Agent working state | Per-agent (local or cloud) | No sync | Agent-scoped, ephemeral |

### Local-First Principle

The developer always has a working local workspace. Cloud sync is additive -- it enhances the experience but is never required for basic functionality:

- **Without cloud sync**: Developer can author configs, run local validation, and call Bedrock APIs directly for iterate operations. Events are written to local `events.jsonl`. This is functionally equivalent to the Claude implementation's workflow.
- **With cloud sync**: Configs are pushed to S3 for Step Functions consumption. Events from cloud executions appear in local workspace. Team members see shared state.

### Sync Configuration

Sync metadata is tracked in `.ai-workspace/bedrock/sync_config.yml`:

```yaml
sync:
  s3_config_bucket: "aisdlc-project-foo-config"
  s3_artifacts_bucket: "aisdlc-project-foo-artifacts"
  dynamodb_events_table: "aisdlc-events"
  dynamodb_features_table: "aisdlc-features"
  project_id: "project-foo"
  last_sync:
    configs_pushed: "2026-02-23T10:30:00Z"
    events_pulled: "2026-02-23T10:28:00Z"
    artifacts_pulled: "2026-02-23T10:29:00Z"
  direction:
    configs: "local_to_cloud"
    events: "cloud_to_local"
    artifacts: "cloud_to_local"
```

### Offline Mode

When operating offline (no AWS connectivity beyond Bedrock API):

1. Local configs are used directly -- no S3 fetch needed.
2. Events are written to local `events.jsonl` as in the Claude implementation.
3. On reconnection, local events can be pushed to DynamoDB via a reconciliation script that detects and merges based on event timestamps and idempotency keys.

### Team Mode

For team collaboration:

1. Cloud state (DynamoDB events, S3 artifacts) is the shared view.
2. Each developer's local workspace is a personal projection of the shared state.
3. Config changes follow a git-like flow: author locally, push to cloud, team members pull updated configs.
4. Event conflicts are avoided by design -- events are append-only and carry unique IDs. Two developers producing events concurrently simply produce interleaved entries ordered by timestamp.

---

## Rationale

1. **Developer experience preservation**: The local `.ai-workspace/` directory maintains compatibility with the methodology's workspace contract and allows developers to use familiar tools (editors, grep, file watchers) for state inspection.
2. **Clear ownership eliminates conflicts**: By designating a single source of truth per resource type and enforcing uni-directional sync, the model avoids the complexity of bidirectional sync and merge conflicts.
3. **Offline resilience**: Developers are not blocked by cloud infrastructure outages or network unavailability. The local workspace is always functional for authoring and Bedrock API-based iteration.
4. **Team scalability**: Cloud state provides the shared coordination layer that local-only workspaces cannot. CI/CD pipelines interact exclusively with cloud state, requiring no local workspace setup.
5. **Incremental adoption**: A developer can start with a purely local workflow (identical to Claude implementation) and enable cloud sync when ready, without restructuring their workspace.

---

## Consequences

### Positive

- Developers retain a familiar, file-system-based workspace that works with standard development tools.
- Offline development is fully supported -- configs are local, iterate calls only need Bedrock API access.
- Team collaboration is enabled through shared cloud state without requiring file-system sharing (NFS, EFS).
- CI/CD pipelines integrate via cloud state (S3/DynamoDB) without needing local workspace setup.
- Incremental adoption path: start local, add cloud sync when needed.

### Negative

- Eventual consistency: a developer's local workspace may lag behind cloud state until the next sync. Mitigated by timestamp tracking in `sync_config.yml` and explicit sync commands.
- Sync conflicts in offline-to-online reconciliation: if the same project runs iterate operations both locally (offline) and in the cloud (by another team member), event streams must be merged. Mitigated by append-only event design with unique IDs and timestamp ordering.
- Additional tooling: sync scripts and the `sync_config.yml` schema add implementation surface. Mitigated by keeping sync operations simple (`aws s3 sync`, DynamoDB queries) and providing a single CLI command (`gen-sync`) to orchestrate them.

### Mitigation

- Provide `gen-sync push` and `gen-sync pull` commands that handle the sync operations with clear feedback on what changed.
- Include staleness warnings in `gen-status` output when local state is older than a configurable threshold (default: 1 hour).
- Document the sync model in the Bedrock Genesis getting-started guide so developers understand ownership rules from the outset.

---

## References

- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) -- Bedrock Runtime as Target Platform
- [ADR-AB-005](ADR-AB-005-dynamodb-event-sourcing.md) -- DynamoDB Event Sourcing
- [ADR-AB-007](ADR-AB-007-infrastructure-as-code-cdk.md) -- Infrastructure as Code via AWS CDK (S3 assets, config deployment)
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) -- REQ-TOOL-002, REQ-CTX-001
