# ADR-014: IntentEngine Binding — Bedrock Genesis Implementation

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-SUPV-001
**Extends**: ADR-008 (Universal Iterate Agent), ADR-011 (Consciousness Loop)

---

## Context

The specification (section 4.6) introduces the **IntentEngine** as a composition law over the four primitives: `IntentEngine(intent + affect) = observer -> evaluator -> typed_output(reflex.log | specEventLog | escalate)`. This is not a fifth primitive but the universal processing unit that operates on every edge, at every scale, chaining fractally.

The Claude reference implementation (ADR-014) binds IntentEngine to the iterate agent and edge configuration system — a configuration-only approach where the iterate agent already implements the observer-evaluator-output pattern and edge configs parameterise ambiguity thresholds. No new executable code is required.

Bedrock Genesis uses **Step Functions workflows** as the iterate engine (ADR-AB-002). The state machine structure — LoadConfig, LoadContext, ConstructCandidate, EvaluatorChain, ConvergenceCheck — already implements the observer-evaluator-output pattern at the infrastructure level. The IntentEngine formalisation maps naturally to the Step Functions state machine without requiring additional states or Lambda functions.

The key architectural questions for Bedrock binding are:

1. How do the three output types (`reflex.log`, `specEventLog`, `escalate`) map to AWS service actions?
2. How is ambiguity classification (zero / bounded / persistent) bound to Lambda vs Bedrock vs API Gateway?
3. How does affect propagation work across DynamoDB-backed state?
4. Where do consciousness levels map in a distributed, stateless architecture?

### Options Considered

1. **New IntentEngine Lambda** — Build a dedicated Lambda that wraps the iterate Step Functions workflow, adding IntentEngine semantics (affect tracking, output classification, consciousness routing) as a pre/post processing layer.
2. **Step Functions state additions** — Add IntentEngine-specific states to the iterate state machine (AffectLoad, OutputClassify, ConsciousnessRoute) that run between existing states.
3. **Configuration-only** — Express IntentEngine semantics through existing Step Functions states and edge configuration. The state machine already implements observer-evaluator-output; edge configs parameterise ambiguity thresholds and affect weights. No new states, no new Lambdas.

---

## Decision

**The IntentEngine is realised through the existing Step Functions iterate workflow (ADR-AB-002) and S3-hosted edge configuration. No new Lambda functions or state machine states are required. The Step Functions state machine already implements observer->evaluator->typed_output; edge configs stored in S3 parameterise ambiguity thresholds and affect weights. The three output types map to existing Step Functions control flow and DynamoDB events.**

### Output Type Mapping

| Spec Output Type | Bedrock Realisation | Event (DynamoDB) | AWS Control Flow |
|:---|:---|:---|:---|
| `reflex.log` | DynamoDB event + Step Functions continue/promote | `iteration_completed`, `edge_converged`, `interoceptive_signal` | ConvergenceCheck -> Loop (continue) or Promote (converge) |
| `specEventLog` | Deferred intent in DynamoDB features table | `iteration_completed` (non-zero delta), `affect_triage` (deferred) | ConvergenceCheck -> Loop with incremented iteration count |
| `escalate` | API Gateway callback + SNS notification | `intent_raised`, `convergence_escalated`, `spawn_created` | ConvergenceCheck -> Escalate state -> waitForTaskToken (ADR-AB-004) |

### Ambiguity Classification Binding

The three ambiguity regimes map to AWS service boundaries:

| Ambiguity Regime | Evaluator Type | AWS Binding | Latency Profile |
|:---|:---|:---|:---|
| **Zero** (reflex) | Deterministic Tests (F_D) | Lambda container image — pytest, linters, schema validators. Pass/fail, no LLM involved. | 100ms-5s (Lambda cold start + execution) |
| **Bounded nonzero** (probabilistic) | Agent(intent, context) (F_P) | Bedrock Converse API — gap analysis, coherence check, candidate assessment. Model selected per edge config. | 2-30s (model inference) |
| **Persistent** (escalate) | Human (F_H) | API Gateway callback + SNS notification + Step Functions `waitForTaskToken`. Asynchronous approval flow (ADR-AB-004). | Minutes to days (human response time) |

The service boundary between Lambda (deterministic) and Bedrock (probabilistic) is the **ambiguity classification boundary**. Edge configs determine which evaluators fall into which category. The Step Functions state machine routes to the appropriate service based on evaluator type.

### Ambiguity Threshold Configuration

Thresholds are configured per edge in S3-hosted YAML files (same format as Claude reference):

```yaml
# s3://project-bucket/config/edge_params/code_unit_tests.yml
edge:
  type: code_unit_tests
  evaluators:
    deterministic:
      - pytest_pass          # ambiguity = 0: Lambda container, pass/fail
      - coverage_threshold   # ambiguity = 0: Lambda, above/below 80%
    agent:
      - code_coherence       # ambiguity bounded: Bedrock Converse, design alignment
      - req_tag_coverage     # ambiguity bounded: Bedrock Converse, REQ key presence
    human:
      - design_approval      # ambiguity persistent: API Gateway callback
  convergence:
    max_iterations: 5        # escalate to human after 5 non-converging iterations
    stuck_threshold: 3       # emit intent_raised after 3 iterations with same delta
  affect:
    base_urgency: normal     # profile can override (hotfix -> critical)
    escalation_weight: 1.0   # multiplier for iteration-derived urgency increase
```

The `max_iterations` and `stuck_threshold` parameters are the **escalation boundaries** — they determine when bounded ambiguity (Bedrock Converse loops) is reclassified as persistent (API Gateway callback to human). The ConvergenceCheck state in the Step Functions workflow implements this classification:

```
ConvergenceCheck (Choice state):
  if all_evaluators_passed:
    -> Promote (emit edge_converged)
  elif iteration_count >= max_iterations:
    -> Escalate (emit convergence_escalated, waitForTaskToken)
  elif stuck_count >= stuck_threshold:
    -> Escalate (emit intent_raised, notify via SNS)
  else:
    -> Loop (back to ConstructCandidate, iteration_count++)
```

### Affect Propagation

Affect (urgency, valence) is stored in the DynamoDB features table and read by the routing Lambda and Step Functions states:

```
DynamoDB Features Table — Affect Fields:

PK:               project_id                (String)
SK:               FEATURE#feature_id        (String)
affect_urgency:   "normal"                  (String: low | normal | high | critical)
affect_source:    "profile"                 (String: profile | signal | iteration | human)
escalation_count: 0                         (Number)
```

Affect propagation mechanisms:

- **Profile-derived urgency**: The routing Lambda reads the project profile (hotfix, spike, standard, etc.) from S3 and sets base urgency on all features. Hotfix profile sets `critical`; spike sets `low`.
- **Signal-derived urgency**: Sensory signals from EventBridge (ADR-AB-006) carry severity. The affect triage Lambda maps signal severity to urgency updates on the features table.
- **Iteration-derived urgency**: The ConvergenceCheck state increments a stuck counter. When `stuck_count` crosses thresholds, a Lambda updates the feature's `affect_urgency` in DynamoDB (normal -> high at `stuck_threshold/2`, high -> critical at `stuck_threshold`).
- **Propagation to children**: When `POST /api/spawn` creates a child vector, the Lambda copies the parent's `affect_urgency` to the child record. Spawns inherit urgency.

The routing Lambda in `POST /api/start` reads `affect_urgency` from the features table to influence routing priority. Critical-urgency features are routed before normal-urgency features, regardless of graph position.

### Consciousness-as-Relative in Bedrock Genesis

Level N's `escalate` becomes Level N+1's reflex. Each level maps to a specific AWS service boundary:

| Level | AWS Mechanism | N's Escalate Becomes N+1's... |
|:---|:---|:---|
| Single iteration | Step Functions state transition (ConstructCandidate -> EvaluatorChain -> ConvergenceCheck) | Input to next iteration loop (specEventLog) or Escalate state (escalate) |
| Edge convergence | Step Functions execution completion | DynamoDB Stream event triggers routing Lambda -> next edge execution (reflex at feature level) |
| Feature traversal | DynamoDB features table state change | `GET /api/status` health check detects trajectory change (reflex at project level) |
| Sensory monitor | EventBridge rule -> Lambda signal handler (ADR-AB-006) | Affect triage Lambda classifies signal -> DynamoDB update (reflex at triage level) |
| Spec review | `POST /api/review` decision callback (ADR-AB-004) | New intent via `POST /api/start` -> new feature in DynamoDB (reflex at project level) |

The consciousness hierarchy is distributed across AWS services rather than contained in a single agent session. This is a structural consequence of the serverless architecture: each level operates independently, connected by events (DynamoDB Streams) and state (DynamoDB tables) rather than in-memory context.

### Per-Edge Ambiguity Thresholds

Each edge's YAML config in S3 defines its own ambiguity boundaries. The CDK deployment reads these configs and parameterises the Step Functions state machine accordingly:

| Edge | Zero (Lambda) | Bounded (Bedrock) | Persistent (API Gateway) | Max Iterations |
|:---|:---|:---|:---|:---|
| intent_requirements | schema check | completeness check | stakeholder approval | 3 |
| requirements_design | ADR schema | coherence, gap detection | architect approval | 5 |
| design_code | lint, type check | design alignment | code review | 5 |
| code_unit_tests | pytest pass, coverage | code coherence | — | 8 |
| design_test_cases | test schema | coverage analysis | QA approval | 4 |
| uat_tests | test execution | scenario coverage | product owner | 3 |

Edges with no human evaluator (e.g., `code_unit_tests` in standard profile) use Express Workflows for lower cost and latency. Edges with human gates use Standard Workflows with `waitForTaskToken`.

---

## Rationale

### Why Configuration-Only (vs New IntentEngine Lambda)

1. **The Step Functions state machine already IS the IntentEngine** — it observes (LoadContext, ConstructCandidate), evaluates (EvaluatorChain), and produces typed output (ConvergenceCheck branching to Loop, Promote, or Escalate). Adding a wrapper Lambda would create indirection without capability.

2. **Edge configs already parameterise ambiguity** — `max_iterations`, evaluator composition, and convergence thresholds in S3-hosted YAML control the boundary between deterministic (Lambda), probabilistic (Bedrock), and escalation (API Gateway). The IntentEngine formalisation explains WHY these parameters exist; it does not require new runtime machinery.

3. **No additional state machine states** — The ConvergenceCheck Choice state already implements the three-way branch (continue/promote/escalate) that maps to IntentEngine's three output types. Adding explicit IntentEngine states would duplicate existing control flow.

### Why DynamoDB for Affect State (vs Step Functions Payload)

1. **Cross-execution persistence** — Affect must persist across iterate executions. A feature's urgency set by a sensory signal at 2am must be readable by a developer invoking `gen-start` at 9am. Step Functions execution payloads are ephemeral — they exist only during execution.

2. **Observable** — Affect stored in DynamoDB is queryable via `GET /api/status`. The health check can report "3 features at critical urgency" without inspecting running Step Functions executions.

3. **Stream-driven** — DynamoDB Streams on the features table enable automated reactions to affect changes (e.g., SNS alert when a feature reaches critical urgency).

### Why Service Boundaries as Ambiguity Classification

The mapping of ambiguity regimes to AWS services (Lambda / Bedrock / API Gateway) is not arbitrary — it reflects the cost and latency characteristics of each regime:

- **Zero ambiguity** uses Lambda because deterministic evaluators are fast, cheap, and produce binary results. There is no reason to invoke an LLM for a pytest pass/fail check.
- **Bounded ambiguity** uses Bedrock because probabilistic assessment requires model inference. The Converse API's model-agnostic interface allows tuning the model per edge (cheaper model for simple coherence checks, larger model for complex gap analysis).
- **Persistent ambiguity** uses API Gateway because human review is inherently asynchronous and requires secure callback mechanisms. The `waitForTaskToken` pattern (ADR-AB-004) is designed exactly for this use case.

---

## Consequences

### Positive

- **Zero new code** — IntentEngine binding is purely configurational, extending existing edge YAML schemas with `affect` and `convergence` sections. The Step Functions state machine implements the pattern without modification.
- **Explicit ambiguity thresholds** — `max_iterations`, `stuck_threshold`, and evaluator type composition are understood as ambiguity classification boundaries. This gives operational teams a principled framework for tuning convergence behavior.
- **Affect is observable** — Urgency stored in DynamoDB is visible in `GET /api/status` health checks, queryable via GSI, and streamable via DynamoDB Streams. Methodology self-observation (ADR-011) is a database query, not log parsing.
- **Consciousness-as-relative is automatic** — The existing level hierarchy (state transition -> execution -> feature -> sensory -> spec review) is distributed across AWS services, each operating independently and connected by events.
- **Model-agnostic bounded ambiguity** — Bedrock Converse API allows different foundation models for different edges. A cheap, fast model for simple coherence checks; a capable model for complex gap analysis. The ambiguity classification boundary is independent of model selection.

### Negative

- **Distributed consciousness overhead** — The consciousness hierarchy spans Step Functions, DynamoDB, EventBridge, and API Gateway. Tracing an escalation from Level 1 (iteration) to Level 5 (spec review) requires correlating events across multiple AWS services. Mitigated: DynamoDB events table provides a single audit trail; X-Ray traces link service invocations.
- **Affect staleness** — DynamoDB Streams processing is eventually consistent. A feature's urgency may be stale by milliseconds when the routing Lambda reads it. Mitigated: urgency is a coarse-grained signal (4 levels), not a precise measure. Sub-second staleness does not affect routing decisions.
- **Conceptual overhead** — Developers must understand the IntentEngine model to tune thresholds effectively. Mitigated by sensible defaults in edge YAML configs and profile-level overrides (hotfix profile sets aggressive thresholds without per-edge tuning).
- **Affect schema addition** — DynamoDB features table gains affect-related attributes. Mitigated by optional defaults (urgency: normal if omitted, escalation_count: 0).

---

## References

- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) — Platform binding (Bedrock, Step Functions, DynamoDB)
- [ADR-AB-002](ADR-AB-002-iterate-engine-step-functions.md) — Iterate engine (Step Functions state machine structure)
- [ADR-AB-004](ADR-AB-004-human-review-api-gateway-callbacks.md) — Human review callbacks (escalation path for persistent ambiguity)
- [ADR-AB-005](ADR-AB-005-event-sourcing-dynamodb.md) — Event sourcing (DynamoDB events table, features table)
- [ADR-008](../../imp_claude/design/adrs/ADR-008-universal-iterate-agent.md) — Universal Iterate Agent (the iterate engine IS the IntentEngine)
- [ADR-011](../../imp_claude/design/adrs/ADR-011-consciousness-loop-at-every-observer.md) — Consciousness Loop (signal sources are affect-phase observers)
- [ADR-015](../../imp_claude/design/adrs/ADR-015-sensory-service-technology-binding.md) — Sensory Service Technology Binding (continuous signal source feeding IntentEngine)
- [ADR-016](../../imp_claude/design/adrs/ADR-016-design-tolerances-as-optimization-triggers.md) — Design Tolerances (tolerance breaches generate optimization intents via the IntentEngine pipeline)
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) — Bedrock implementation design
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) — Canonical model, section 4.6 (IntentEngine)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — Requirements baseline, REQ-SUPV-001 (IntentEngine interface)

---

## Requirements Addressed

- **REQ-SUPV-001**: IntentEngine interface — observer -> evaluator -> typed_output, parameterised by intent + affect. Realised through Step Functions state machine (observer = LoadContext + ConstructCandidate, evaluator = EvaluatorChain, typed_output = ConvergenceCheck branching).
