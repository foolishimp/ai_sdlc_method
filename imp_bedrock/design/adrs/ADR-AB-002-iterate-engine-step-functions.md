# ADR-AB-002: Iterate Engine via Step Functions

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-ITER-001, REQ-ITER-002, REQ-GRAPH-002

---

## Context

The Asset Graph Model defines one universal operation: `iterate(Asset<Tn>, Context[], Evaluators(edge_type)) -> Asset<Tn.k+1>`. ADR-AB-001 establishes the hybrid cloud/local platform binding. This ADR decides how to implement the iterate engine itself — the core loop that loads configuration, constructs candidates, runs evaluators, checks convergence, and either loops or promotes.

In CLI implementations (Claude, Gemini, Codex), the iterate engine is an in-session agent or orchestrator that holds state in the conversation context and drives tool calls sequentially. This works for single-developer interactive sessions but has structural limitations:

- **No execution history**: When the session ends, the iterate trace is lost (unless manually logged to events).
- **No native retry/timeout**: The agent must implement retry logic in prompting or scripting. Timeout enforcement is approximate.
- **No visual debugging**: Iterate failures require reading event logs and agent output. There is no graphical view of which state the iteration reached before failing.
- **No concurrent execution**: Two developers cannot iterate the same graph simultaneously without explicit coordination (ADR-013).

AWS Step Functions addresses all four limitations natively. The question is whether the structural mapping is clean enough to justify the operational overhead.

### Options Considered

1. **Lambda orchestrator loop**: A single Lambda function implements the iterate loop. It calls Bedrock Converse for construction, invokes evaluator Lambdas, checks convergence, and either recurses (via self-invocation) or returns. State is passed in the invocation payload.

2. **ECS long-running task**: An ECS Fargate task runs a Python process implementing the iterate loop. The process has full access to the AWS SDK and maintains in-memory state across iteration cycles. Similar to the CLI model but running in the cloud.

3. **Step Functions Standard Workflow**: Each edge type gets a Step Functions state machine definition derived from edge config YAML. The state machine structure maps directly to the iterate operation: load config, load context, construct candidate, evaluate, check convergence, loop or promote.

---

## Decision

**We will use Step Functions Standard Workflows as the iterate engine (Option 3). Each edge type in the graph topology maps to a Step Functions state machine definition. The state machine structure mirrors the iterate operation directly.**

### State Machine Structure

Every iterate state machine follows this canonical structure, parameterised by edge configuration:

```
┌───────────────────────────────────────────────────────────────────────┐
│                   ITERATE STATE MACHINE (edge: {edge_type})           │
│                                                                       │
│  ┌──────────────┐                                                     │
│  │  LoadConfig   │  Read edge_params/{edge_type}.yml from S3          │
│  │  (Lambda)     │  Read evaluator_defaults.yml                       │
│  │               │  Merge profile overrides                           │
│  └──────┬───────┘                                                     │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────┐                                                     │
│  │  LoadContext  │  Retrieve context via Knowledge Base (RAG)         │
│  │  (Lambda)     │  or direct S3 read for small configs               │
│  │               │  Assemble Context[] per edge requirements          │
│  └──────┬───────┘                                                     │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────────────┐                                             │
│  │  ConstructCandidate   │  Bedrock Converse API call                 │
│  │  (Lambda + Bedrock)   │  Model selected per edge config            │
│  │                       │  System prompt from edge guidance field    │
│  │                       │  Input: current asset + Context[]          │
│  │                       │  Output: candidate Asset<Tn.k+1>          │
│  └──────────┬───────────┘                                             │
│             │                                                         │
│             ▼                                                         │
│  ┌──────────────────────┐                                             │
│  │  EvaluatorChain       │  Ordered execution of evaluators           │
│  │                       │                                            │
│  │  ┌─── F_D ─────────┐ │  Deterministic: Lambda container           │
│  │  │ pytest/lint/     │ │  (pytest, linters, schema validators)     │
│  │  │ schema check     │ │  Pass/fail + structured report            │
│  │  └────────┬─────────┘ │                                            │
│  │           │            │                                            │
│  │  ┌─── F_P ─────────┐ │  Probabilistic: Bedrock Converse           │
│  │  │ coherence check  │ │  (gap detection, consistency review)      │
│  │  │ gap detection    │ │  Score + issue list                       │
│  │  └────────┬─────────┘ │                                            │
│  │           │            │                                            │
│  │  ┌─── F_H ─────────┐ │  Human: waitForTaskToken + SNS + API Gw   │
│  │  │ approval gate    │ │  (only when human_required = true)        │
│  │  │ (conditional)    │ │  Approve / reject / request-changes       │
│  │  └────────┬─────────┘ │                                            │
│  └───────────┴───────────┘                                            │
│             │                                                         │
│             ▼                                                         │
│  ┌──────────────────────┐                                             │
│  │  ConvergenceCheck     │  All evaluators passed?                    │
│  │  (Choice state)       │  max_iterations reached?                   │
│  │                       │  stuck_threshold breached?                 │
│  └──────┬───────┬───────┘                                             │
│    Yes  │       │ No                                                  │
│         │       │                                                     │
│         ▼       ▼                                                     │
│  ┌──────────┐  ┌──────────────┐                                       │
│  │ Promote  │  │ Loop         │──▶ Back to ConstructCandidate         │
│  │ + Emit   │  │ (iteration+1)│   OR                                  │
│  │ Events   │  └──────────────┘   ┌──────────────┐                    │
│  └──────────┘                     │ Escalate     │  (stuck/timeout)   │
│                                   │ + Emit Events│                    │
│                                   └──────────────┘                    │
└───────────────────────────────────────────────────────────────────────┘
```

### Workflow Type Selection

| Edge Characteristic | Workflow Type | Rationale |
|:---|:---|:---|
| Deterministic-only evaluators, no human gate | Express Workflow | < 5 min execution, lower cost ($0.000001/state transition), synchronous response |
| Any human evaluator gate | Standard Workflow | Supports `waitForTaskToken` (up to 1 year wait), execution history retained |
| Mixed evaluators, long-running | Standard Workflow | Timeout flexibility, visual debugging, audit trail |

Default: Standard Workflow for all edges. Express Workflow is an optimisation applied to edges where the edge config specifies `human_required: false` and `max_iterations` is low (typically lint/schema validation edges).

### Edge Config to State Machine Mapping

The CDK deployment reads edge configuration YAML and generates Step Functions ASL (Amazon States Language) definitions:

```yaml
# edge_params/requirements_design.yml (methodology config)
edge_type: requirements_design
source: requirements
target: design
evaluators:
  - type: deterministic
    command: "pytest tests/design/ -v"
  - type: agent
    checklist:
      - "ADRs reference implementation requirements"
      - "Design does not introduce spec-level concerns"
  - type: human
    gate: approve_before_promote
convergence:
  max_iterations: 5
  stuck_threshold: 3
  human_required: true
```

This generates a Standard Workflow with:
- `LoadConfig` state reading this YAML from S3
- `LoadContext` state retrieving spec + requirements assets
- `ConstructCandidate` state invoking Bedrock Converse with edge-specific guidance
- `EvaluatorChain` with three states: Lambda (pytest), Bedrock (checklist), API Gateway (human gate)
- `ConvergenceCheck` choice state with loop-back, promote, and escalate branches

---

## Rationale

### Why Step Functions (vs Lambda Orchestrator Loop)

**1. Graph-to-workflow structural isomorphism** — The Asset Graph Model defines iterate as a traversal of states: load, construct, evaluate, converge-or-loop. Step Functions state machines are literally state traversal engines. The structural mapping is 1:1. A Lambda orchestrator loop hides this structure inside procedural code, making the graph topology invisible at the execution layer.

**2. Native retry and timeout** — Step Functions provides per-state `Retry` and `Catch` configurations with exponential backoff, maximum attempts, and interval control. A Lambda orchestrator must implement retry logic manually, and Lambda itself has a hard 15-minute timeout that constrains iteration cycles. Step Functions Standard Workflows can run for up to one year.

**3. Execution history as iterate audit trail** — Every Step Functions execution retains a detailed history of state transitions, inputs, outputs, and timestamps. This is, effectively, a built-in iterate trace that supplements the DynamoDB event store. A Lambda orchestrator produces CloudWatch logs that must be manually correlated.

**4. Visual debugging** — The Step Functions console renders the state machine as a graph and highlights the current/failed state in active executions. When an iterate cycle fails at the evaluator stage, the developer can see exactly which evaluator failed, with its input and output, without grep-ing logs.

**5. Concurrent execution safety** — Step Functions manages execution state internally. Multiple iterate executions (different edges, different features) run as independent executions with no shared in-memory state. A Lambda orchestrator loop sharing DynamoDB state requires explicit locking and conflict resolution.

### Why Not ECS Long-Running Task

**1. Over-provisioned for iterate** — An iterate cycle is bursty: it loads config (fast), calls Bedrock (slow, waiting for LLM), runs evaluators (fast for deterministic, slow for human), and checks convergence (fast). An ECS task provisions compute for the entire duration, paying for idle time during the Bedrock call and the human review wait. Step Functions pauses between states at zero compute cost.

**2. No native state inspection** — ECS tasks are black boxes from the orchestration perspective. The only visibility is stdout/stderr and custom CloudWatch metrics. Step Functions provides per-state visibility out of the box.

**3. Session-affinity anti-pattern** — An ECS task holding iterate state in memory recreates the CLI session model in the cloud. This is precisely the pattern Bedrock Genesis is designed to avoid. The iterate engine should be stateless between steps, with state persisted in DynamoDB/S3.

### Why Standard Workflows as Default

Standard Workflows cost more per state transition ($0.025 per 1,000 transitions vs $0.000001 for Express) but provide:
- Execution history retained for 90 days (Express: none)
- `waitForTaskToken` for human evaluator gates (Express: not supported)
- Maximum duration of 1 year (Express: 5 minutes)
- Exactly-once execution semantics (Express: at-least-once)

Since most methodology edges include human review gates or multi-iteration cycles that may exceed 5 minutes, Standard is the safe default. Express is an explicit optimisation for known-fast, deterministic-only edges.

---

## Consequences

### Positive

- **Graph-to-workflow 1:1 mapping**: Each graph edge has a corresponding state machine. The methodology topology is visible in the AWS console. Adding a new edge means deploying a new state machine from config — no code changes to the engine.
- **Native retry and timeout**: Bedrock Converse API transient failures (throttling, model overload) are handled by Step Functions `Retry` policies. Lambda evaluator failures get automatic backoff. No retry logic in application code.
- **Execution history as audit trail**: Every iterate cycle is an execution with full state-by-state history. Combined with DynamoDB event sourcing, this provides two complementary audit layers: methodology events (semantic) and execution traces (operational).
- **Visual debugging**: The Step Functions console shows exactly where an iterate cycle is, which state it reached, and what each state's input/output was. This is significantly more accessible than parsing CloudWatch logs.
- **Parallel state support**: Step Functions `Parallel` states enable concurrent evaluator execution where evaluators are independent (e.g., running lint and unit tests simultaneously). The methodology spec does not require sequential evaluator execution when evaluators are independent.
- **Human gate as first-class state**: The `waitForTaskToken` pattern makes human review a proper state in the workflow rather than an external polling mechanism. The workflow pauses, the human is notified, and the workflow resumes when the human responds. No polling, no timeouts on the human side (up to 1 year).

### Negative

- **State transition costs**: At $0.025 per 1,000 state transitions (Standard), an iterate cycle with 6 states and 3 iteration loops costs ~$0.00045 in Step Functions charges alone. For a project with 10 edges and 50 iterations each, that is ~$0.225. Negligible per project, but non-zero — and adds to Bedrock token costs, Lambda invocation costs, and DynamoDB read/write costs.
- **256KB payload limit per state**: Step Functions Standard Workflows limit each state's input/output to 256KB. A generated code file, comprehensive test suite output, or large specification context can exceed this. All large data must be passed by S3 URI reference, not by value. This adds a "materialise to S3, pass URI" pattern to every state that handles artifacts.
- **Eventual consistency**: Step Functions execution history is eventually consistent. A `DescribeExecution` call immediately after completion may not reflect the final state. Status queries (`/gen-status`) must tolerate brief delays between execution completion and history availability.
- **ASL complexity**: Amazon States Language (JSON-based state machine definitions) is verbose and non-trivial to generate correctly from YAML edge configs. The CDK deployment code that transforms edge YAML to ASL definitions is itself a significant piece of implementation logic.
- **Cold start cascade**: An iterate cycle starting from a cold state may trigger cold starts on the LoadConfig Lambda, the ConstructCandidate Lambda, and each evaluator Lambda sequentially. Worst case: 4-6 cold starts in series, adding 2-8 seconds to the first iteration cycle.

### Mitigation

- **Payload limits**: Adopt the "S3 reference" pattern universally. Every state that produces or consumes artifacts uses `{bucket, key, version}` tuples instead of inline content. The `ConstructCandidate` state writes the candidate to S3 and passes the reference; evaluator states fetch from S3 directly.
- **Cold starts**: Use Lambda provisioned concurrency for the `ConstructCandidate` Lambda (most frequently invoked, most latency-sensitive). Use Lambda SnapStart (Java) or container reuse (Python) for evaluator Lambdas. Express Workflows for fast edges avoid the Standard Workflow overhead.
- **ASL generation**: Build a tested CDK construct (`IterateStateMachine`) that takes edge config YAML as input and produces validated ASL. Unit test the construct against known edge configurations. The construct is the only place ASL is generated; all other code works with edge config YAML.
- **Eventual consistency**: `/gen-status` reads from DynamoDB event store (strongly consistent reads available) rather than Step Functions execution history. Execution history is a supplementary debugging tool, not the primary state source.
- **Cost monitoring**: CloudWatch cost allocation tags per project and per edge type. `gen-status --health` includes iteration cost summary. Budget alarms on per-project Step Functions spend.

---

## References

- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) — platform binding decision (establishes Step Functions as orchestration primitive)
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) §1.3 (Universal Iterate Orchestration), §2.1 (Asset Graph Engine)
- [ADR-008: Universal Iterate Agent](../../imp_claude/design/adrs/ADR-008-universal-iterate-agent.md) — reference implementation (single agent, edge-parameterised)
- [ADR-009: Graph Topology as Configuration](../../imp_claude/design/adrs/ADR-009-graph-topology-as-configuration.md) — YAML-based topology (shared config format)
- [ADR-CG-002: Universal Iterate Orchestrator](../../imp_codex/design/adrs/ADR-CG-002-universal-iterate-orchestrator.md) — Codex sibling (tool-calling iterate)
- [ADR-GG-002: Universal Iterate Sub-Agent](../../imp_gemini/design/adrs/ADR-GG-002-universal-iterate-sub-agent.md) — Gemini sibling (template agent iterate)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §3 (The Iteration Function), §4.6 (IntentEngine)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-ITER-001, REQ-ITER-002, REQ-GRAPH-002
