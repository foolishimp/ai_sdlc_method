# ADR-009: Graph Topology as Configuration — Bedrock Genesis Adaptation

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003
**Adapts**: Claude ADR-009 (Graph Topology as Configuration) for AWS Bedrock

---

## Context

The Asset Graph Model defines software development as a directed cyclic graph of typed assets connected by admissible transitions. The graph topology — which asset types exist and which transitions are allowed — is fundamental to the methodology. The specification (§5) explicitly states that graph topology is itself an element of Context[].

The Claude reference implementation (ADR-009) stores topology as YAML files in the local `.ai-workspace/graph/` directory. The iterate agent reads these files directly from the filesystem at invocation time. This is natural for a CLI tool operating on a single developer's machine.

Bedrock Genesis must serve the same topology to a different execution substrate: Step Functions state machines running in Lambda functions that have no persistent filesystem. The topology YAML must be accessible to cloud services while remaining editable by developers locally.

### The Storage Challenge

In the Claude model, topology files are "just files" — no infrastructure needed. In Bedrock Genesis, files must live in a location that is:

1. **Readable by Lambda functions** — the `LoadConfig` step reads topology to determine valid transitions.
2. **Readable by Step Functions** — the iterate orchestrator needs topology for routing decisions.
3. **Editable by developers** — teams customise topology for their project's SDLC.
4. **Versionable** — topology changes must be tracked for reproducibility (REQ-INTENT-004).
5. **Composable** — corporate, team, and project-level topology must merge hierarchically (REQ-CTX-002).

### Options Considered

1. **S3-only** — topology YAML stored in `s3://project-bucket/config/`. Developers edit via S3 console or CLI. Lambda reads directly.
2. **Local-only with EFS mount** — topology in `.ai-workspace/graph/`, Lambda reads via EFS. Preserves Claude model exactly.
3. **Hybrid: S3 canonical + local mirror** — topology in S3 for cloud services, mirrored to local `.ai-workspace/` for developer experience. Sync managed by CLI tooling.
4. **DynamoDB document store** — topology stored as DynamoDB items. Atomic updates, queryable.

---

## Decision

**We store graph topology YAML files in S3 as the cloud-canonical source and mirror them to local `.ai-workspace/graph/` for developer experience (Option 3). S3 object versioning provides configuration history. CDK deploys YAML as S3 assets for reproducible infrastructure.**

### Storage Layout

**S3 (cloud-canonical):**

```
s3://project-bucket/config/
  graph_topology.yml          # Asset types + admissible transitions
  edge_params/
    intent_requirements.yml
    requirements_design.yml
    design_code.yml
    tdd.yml
    bdd.yml
    code_tagging.yml
    traceability.yml
    feedback_loop.yml
    adr.yml
  profiles/
    full.yml
    standard.yml
    poc.yml
    spike.yml
    hotfix.yml
    minimal.yml
  evaluator_defaults.yml
  project_constraints.yml
  feature_vector_template.yml
```

**Local mirror:**

```
.ai-workspace/graph/
  graph_topology.yml
  edge_params/
    ...
  profiles/
    ...
```

S3 versioning is enabled on the config bucket. Every `PutObject` creates a new version with a unique `VersionId`, providing native content-addressable history without custom tooling.

### Topology Read Path

The iterate state machine's `LoadConfig` Lambda reads topology via a two-tier strategy:

1. **Primary**: `s3://project-bucket/config/graph_topology.yml` via S3 `GetObject`.
2. **Fallback**: local `.ai-workspace/graph/graph_topology.yml` (for offline/hybrid mode per ADR-AB-008).

The Lambda caches the topology in memory for the duration of the execution. Cache invalidation is based on S3 ETag comparison — if the ETag has changed since the last read, the cache is refreshed.

### Topology Format

The topology format is identical to the Claude implementation. The same YAML schema works across both platforms:

```yaml
# graph_topology.yml
version: "2.0"
asset_types:
  intent:
    schema: "intent_schema.yml"
    markov_criteria: ["business_goal_stated", "success_metrics_defined"]
  requirements:
    schema: "requirements_schema.yml"
    markov_criteria: ["req_keys_assigned", "acceptance_criteria_defined"]
  design:
    schema: "design_schema.yml"
    markov_criteria: ["adrs_written", "technology_choices_bound"]
  code:
    schema: "code_schema.yml"
    markov_criteria: ["compiles", "req_keys_tagged"]
  # ... remaining asset types

transitions:
  - source: intent
    target: requirements
    edge_config: "edge_params/intent_requirements.yml"
  - source: requirements
    target: design
    edge_config: "edge_params/requirements_design.yml"
  - source: design
    target: code
    edge_config: "edge_params/design_code.yml"
  # ... remaining transitions
```

### CDK Deployment

Topology files are deployed as CDK S3 assets (ADR-AB-007):

```typescript
const topologyAsset = new s3assets.Asset(this, 'GraphTopology', {
  path: path.join(__dirname, '../config/graph_topology.yml'),
});

const edgeParamsAsset = new s3assets.Asset(this, 'EdgeParams', {
  path: path.join(__dirname, '../config/edge_params/'),
});
```

CDK's asset system uploads files with content-addressable names (hash-based keys), ensuring the Lambda function always references the correct version. When the YAML changes, CDK detects the content hash change and deploys the new version.

### Hierarchical Composition

Context hierarchy (REQ-CTX-002) is supported through S3 prefix-based layering:

```
s3://org-bucket/config/base/           # Organisation-level defaults
s3://team-bucket/config/overrides/     # Team-level customisations
s3://project-bucket/config/            # Project-level topology (final)
```

The `LoadConfig` Lambda merges layers using deep-merge semantics: project overrides team, team overrides organisation. The merge order is configured in `project_constraints.yml`:

```yaml
context_hierarchy:
  - source: "s3://org-bucket/config/base/"
    priority: 1
  - source: "s3://team-bucket/config/overrides/"
    priority: 2
  - source: "s3://project-bucket/config/"
    priority: 3  # highest priority wins
```

---

## Rationale

### Why S3 + Local Mirror (vs S3-Only)

**1. Developer experience** — Developers need to view, edit, and diff topology files with standard tools (editors, grep, git). S3-only requires `aws s3 cp` for every view/edit cycle, which is slow and unfamiliar. A local mirror preserves the `.ai-workspace/graph/` convention from the Claude implementation.

**2. Offline development** — Per ADR-AB-008, developers must be able to work without cloud connectivity. The local mirror provides topology access for local validation and iterate invocations that call Bedrock APIs directly.

**3. Git integration** — Local topology files can be committed to the project repository, enabling pull-request-based topology review. S3 versioning provides cloud-side history; git provides team-side review workflow.

### Why S3 (vs DynamoDB)

**1. File-native** — Topology is naturally expressed as YAML files, not database rows. S3 stores files natively. DynamoDB would require serialising/deserialising YAML to/from DynamoDB items, adding unnecessary complexity.

**2. Versioning** — S3 object versioning is a managed service. DynamoDB versioning requires application-level implementation (version columns, conditional writes).

**3. CDK asset integration** — CDK's S3 asset system provides content-addressable deployment. No equivalent exists for DynamoDB items.

**4. Cost** — S3 storage for a handful of YAML files (typically <100KB total) is effectively free. DynamoDB read/write units add incremental cost for config access.

### Why Not EFS Mount

EFS provides a shared filesystem accessible from Lambda functions, which would preserve the "just files" model exactly. However:

1. **Cold start penalty** — EFS-mounted Lambda functions have 500ms-2s additional cold start latency for VPC and mount point setup.
2. **VPC requirement** — EFS requires Lambda functions to run in a VPC, adding networking complexity (subnets, NAT gateways, security groups) to the infrastructure.
3. **Cost** — EFS charges per GB-month of storage and per provisioned throughput. For a few YAML files, this is over-provisioned.
4. **Operational surface** — EFS adds mount targets, access points, and security groups to the CDK stack. S3 requires only a bucket.

### Shared Format Across Implementations

The topology YAML format is identical across Claude, Gemini, Codex, and Bedrock implementations. This means:

- A topology developed and tested in the Claude CLI can be deployed to Bedrock without modification.
- Cross-implementation testing can validate that the same topology produces equivalent behaviour.
- The specification's commitment to "one graph, many implementations" is preserved at the config level.

---

## Default Topology

The plugin ships with the same default graph topology as the Claude implementation:

```
intent -> requirements -> design -> code <-> unit_tests
                            |
                            +---> uat_tests
                            +---> test_cases

code -> cicd -> running_system -> telemetry -> intent (feedback loop)
```

Projects can extend, modify, or simplify this topology by uploading custom YAML to S3 or editing the local mirror.

---

## Consequences

### Positive

- **Graph is inspectable** — developers can read topology YAML locally or in S3, using standard tools
- **Graph is configurable** — teams customise topology via YAML edits, no code changes
- **Graph is composable** — S3 prefix-based hierarchy supports organisation/team/project layering
- **Graph is versionable** — S3 object versioning provides immutable configuration history with version IDs
- **Shared format** — same YAML works across all four implementations (Claude, Gemini, Codex, Bedrock)
- **CDK asset integration** — topology deploys alongside infrastructure with content-addressable naming

### Negative

- **S3 read latency** — Lambda reads topology from S3 on every iterate invocation (typically 5-15ms). For rapid iteration cycles, this adds cumulative overhead.
- **Sync discipline** — developers must push local topology changes to S3 before cloud executions pick them up. Stale S3 configs cause cloud executions to use old topology.
- **No runtime validation** — YAML files can have syntax errors or invalid references (e.g., a transition referencing a non-existent asset type). Validation depends on the `LoadConfig` Lambda detecting issues at invocation time.

### Mitigation

- Lambda caches topology in memory with ETag-based invalidation. Repeated reads within the same execution are free.
- `gen-sync push` command pushes local config to S3 with confirmation of what changed. `gen-status --health` reports config sync freshness.
- `LoadConfig` Lambda validates topology schema (asset type references, transition integrity) before proceeding. Invalid topology fails fast with a structured error in Step Functions execution history.
- CDK deployment validates topology files at synth time via a custom CDK aspect.

---

## References

- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) — Bedrock Runtime as Target Platform
- [ADR-AB-007](ADR-AB-007-infrastructure-as-code-cdk.md) — Infrastructure as Code via CDK (S3 asset deployment)
- [ADR-AB-008](ADR-AB-008-local-cloud-hybrid-workspace.md) — Local-Cloud Hybrid Workspace (sync model)
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) — Bedrock implementation design
- [ADR-009: Graph Topology as Configuration (Claude)](../../imp_claude/design/adrs/ADR-009-graph-topology-as-configuration.md) — reference implementation (YAML-based topology)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §2 (The Asset Graph), §4.6 (IntentEngine), §5 (Constraint Surface)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003
