# ADR-008: Universal Iterate Agent — Bedrock Genesis Adaptation

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-ITER-001, REQ-ITER-002, REQ-GRAPH-002
**Adapts**: Claude ADR-008 (Universal Iterate Agent) for AWS Bedrock

---

## Context

The Asset Graph Model defines one universal operation: `iterate(Asset<Tn>, Context[], Evaluators(edge_type)) -> Asset<Tn.k+1>`. The Claude reference implementation (ADR-008) binds this to a single markdown prompt file (`gen-iterate.md`) that is fully parameterised by edge configuration YAML. The key invariant: one operation, parameterised per edge, no hard-coded stages.

Bedrock Genesis must preserve this invariant while operating in a fundamentally different execution model. There is no persistent conversation session and no markdown agent file. Instead:

- **Step Functions** provides the orchestration substrate (ADR-AB-002).
- **Bedrock Converse API** provides model-agnostic LLM construction.
- **Lambda functions** provide deterministic evaluator execution.
- **S3 and local `.ai-workspace/`** provide configuration storage.

The question is whether the "single iterate agent" concept translates cleanly to a serverless, stateless environment where the "agent" is a state machine rather than a prompt file.

### The Structural Mapping

In Claude Code, the iterate agent is a single markdown file that reads edge config at invocation time and adapts its behaviour accordingly. In Bedrock Genesis, the equivalent is a single Step Functions state machine definition that reads edge config from S3 and adapts its state transitions accordingly. The structural isomorphism is:

| Claude Concept | Bedrock Equivalent |
|:---|:---|
| `gen-iterate.md` (prompt file) | Step Functions state machine definition (ASL) |
| Edge config YAML (local files) | Edge config YAML (S3 objects or local `.ai-workspace/`) |
| Evaluator checklist in prompt | Evaluator chain in state machine (Lambda + Bedrock + API Gateway) |
| Convergence check by agent reasoning | Convergence check by Choice state with data conditions |
| Context[] loaded from workspace | Context[] loaded from Knowledge Base (RAG) + direct S3 reads |

### Options Considered

1. **One state machine per edge type** — each graph edge gets a dedicated Step Functions definition with hard-coded evaluator chain. Edge-specific logic is embedded in the ASL.
2. **Single parameterised state machine** — one state machine definition, parameterised by edge config loaded at runtime. The same definition handles all edges.
3. **Meta-generator** — a CDK construct generates edge-specific state machines from YAML config at deployment time. Each deployed state machine is edge-specific, but the generation logic is universal.

---

## Decision

**We use a single parameterised Step Functions state machine (Option 2) as the universal iterate engine. Edge behaviour is determined entirely by configuration loaded at runtime from S3, not by the state machine definition.**

The iterate state machine follows the canonical structure defined in ADR-AB-002:

```
LoadConfig → LoadContext → ConstructCandidate → EvaluatorChain → ConvergenceCheck → (Loop | Promote | Escalate)
```

This structure is invariant across all edges. What varies per edge is:

- **LoadConfig**: which `edge_params/{edge_type}.yml` file is loaded from S3
- **LoadContext**: which context documents are retrieved (Knowledge Base query or direct S3 read)
- **ConstructCandidate**: which foundation model is used, which system prompt guidance applies
- **EvaluatorChain**: which evaluators execute (deterministic, probabilistic, human), in what order, with what thresholds
- **ConvergenceCheck**: what `max_iterations`, `stuck_threshold`, and `human_required` values apply

The state machine receives the edge type as input and dispatches to the appropriate configuration. No ASL changes are needed to add a new edge type — only a new YAML config file in S3.

### Edge Config Loading

The `LoadConfig` Lambda reads edge parameters from S3:

```
s3://project-bucket/config/edge_params/{edge_type}.yml
```

Or from local workspace in hybrid mode:

```
.ai-workspace/config/edge_params/{edge_type}.yml
```

The config is merged with `evaluator_defaults.yml` and any active profile overrides (full, standard, poc, spike, hotfix, minimal). The merged config is passed as state to all subsequent steps.

### Evaluator Dispatch

The `EvaluatorChain` state uses a Map state or sequential states to execute evaluators specified in the edge config. Each evaluator type dispatches differently:

| Evaluator Type | Dispatch Mechanism |
|:---|:---|
| `deterministic` | Lambda container image (pytest, lint, schema validation) |
| `agent` (probabilistic) | Bedrock Converse API call with checklist items as structured prompt |
| `human` | Step Functions `waitForTaskToken` + SNS notification + API Gateway callback (ADR-AB-004) |

The evaluator list is data-driven — the state machine reads the evaluator array from the loaded edge config and iterates through it. Adding an evaluator to an edge requires only a YAML config change.

### Convergence Logic

The `ConvergenceCheck` Choice state evaluates three conditions from the edge config:

1. All evaluators passed (stable)
2. `max_iterations` reached (timeout escalation)
3. `stuck_threshold` breached (same failures repeating — stuck escalation)

These thresholds are not hard-coded in the state machine. They are read from the edge config at `LoadConfig` time and evaluated as data conditions in the Choice state.

---

## Rationale

### Why Single Parameterised Machine (vs One Per Edge)

**1. The model says one operation** — The Asset Graph Model defines `iterate()` as a single function parameterised by edge type. Having separate state machines per edge re-introduces the hard-coded stage pattern that v2.1 eliminated. One state machine, one operation.

**2. Extensibility** — Adding a new edge type (e.g., `api_spec -> code`) requires only a new YAML file in `s3://project-bucket/config/edge_params/`. No CDK redeployment, no ASL changes, no new state machine creation.

**3. Consistency** — All edges traverse the same state machine with the same error handling, retry policies, and execution history format. With per-edge machines, each would need independent maintenance of these operational concerns.

**4. Cost** — Step Functions charges per state machine execution. One machine handling all edges is operationally simpler than managing N machines (one per edge type). Monitoring, alarming, and cost allocation are centralised.

### Why Not Meta-Generator (vs Dynamic Parameterisation)

The meta-generator approach (Option 3) generates edge-specific state machines from YAML at CDK deploy time. This has the theoretical benefit of compile-time validation but the practical cost of requiring a CDK redeployment for every edge config change. Dynamic parameterisation reads config at runtime, allowing config changes to take effect immediately via S3 upload.

For methodology evolution (adding evaluators, adjusting thresholds, tuning convergence criteria), immediate feedback from config changes is more valuable than deployment-time validation. Validation is handled by the `LoadConfig` Lambda, which checks config schema before proceeding.

### Alignment with Claude ADR-008

The invariant from Claude ADR-008 is preserved exactly:

> "The agent has no hard-coded knowledge of 'stages'. It reads: the edge type, the evaluator configuration, the context, the asset type schema."

In Bedrock Genesis, this becomes:

> "The state machine has no hard-coded knowledge of edges. It reads: the edge type from its input, the evaluator configuration from S3, the context from Knowledge Base/S3, the asset type schema from the graph topology config."

The mechanism differs (state machine vs prompt file), but the architectural commitment is identical: one operation, data-driven behaviour, zero-code extensibility.

---

## Consequences

### Positive

- **One state machine to maintain** — all iterate behaviour in one ASL definition, parameterised by edge config
- **Edge configs are data** — YAML files in S3 that can be versioned, diffed, composed, and updated without deployment
- **New edges are zero-deployment** — upload a YAML config to S3, the next iterate invocation picks it up
- **Theory-implementation alignment** — the code reflects the model: one operation, parameterised per edge
- **Visual debugging applies universally** — Step Functions console shows the same state machine structure for every edge, making cross-edge comparison straightforward
- **Execution history is uniform** — all edges produce comparable execution traces, enabling cross-edge performance analysis

### Negative

- **Runtime config validation** — invalid edge config YAML is detected at iterate time, not at deployment time. A malformed config causes a runtime failure on the `LoadConfig` step.
- **Complex Choice state** — the `ConvergenceCheck` Choice state must evaluate data-driven conditions loaded from config, which is more complex than hard-coded threshold comparisons.
- **S3 read latency** — every iterate invocation reads config from S3 (typically 5-15ms). For rapid iteration cycles, this adds cumulative overhead. Mitigated by Lambda function caching of recently-read configs.
- **Single point of failure** — one state machine handles all edges. A bug in the state machine definition affects all edges. Mitigated by the state machine being simple and stable (the complexity is in the configs, not the machine).

### Mitigation

- `LoadConfig` Lambda validates edge config against a JSON schema before proceeding. Invalid configs fail fast with a clear error message in the Step Functions execution history.
- Edge configs are deployed as CDK S3 assets with content-addressable naming, ensuring Lambda cache invalidation on config changes.
- The state machine definition is covered by unit tests in the CDK construct library (ADR-AB-007). Config changes do not require state machine changes.
- `/gen-status --health` reports config loading success/failure rates across recent executions.

---

## Relation to Superseded ADRs

| Superseded ADR | What It Specified | Where It Goes in Bedrock Genesis |
|:---|:---|:---|
| ADR-003 (Stage Personas) | 7 agent markdown files with per-stage personas | 1 state machine, personas encoded in edge configs |
| ADR-004 (Reusable Skills) | 11 skills (extraction, merging, etc.) | Evaluator/constructor logic in edge parameterisations |
| ADR-005 (Feedback Loops) | Per-stage iteration patterns | Inherent in iterate() — the state machine IS the iteration loop |

---

## References

- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) — Bedrock Runtime as Target Platform (establishes Step Functions + Bedrock Converse)
- [ADR-AB-002](ADR-AB-002-iterate-engine-step-functions.md) — Iterate Engine via Step Functions (detailed state machine design)
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) — Bedrock implementation design
- [ADR-008: Universal Iterate Agent (Claude)](../../imp_claude/design/adrs/ADR-008-universal-iterate-agent.md) — reference implementation (single agent, edge-parameterised)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §3 (The Iteration Function), §4.6 (IntentEngine)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-ITER-001, REQ-ITER-002, REQ-GRAPH-002
