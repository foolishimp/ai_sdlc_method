# ADR-AB-001: AWS Bedrock Runtime as Target Platform

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-TOOL-001, REQ-TOOL-002, REQ-TOOL-003
**Supersedes**: ADR-001 (Claude Code as MVP Platform) — for Bedrock Genesis implementation

---

## Context

The AI SDLC Asset Graph Model is platform-agnostic but requires a concrete runtime binding. Claude Code is the reference implementation (CLI-first, single-developer, interactive session). Gemini and Codex provide sibling bindings, also CLI-first. We need a fourth binding that preserves methodology semantics while targeting a fundamentally different execution model: **cloud-native, API-driven, serverless**.

AWS Bedrock runtime primitives differ structurally from the three existing implementations:

- **No interactive session**: Stateless API calls replace conversational agent loops. There is no persistent chat session holding methodology state in memory.
- **Model-agnostic LLM access**: The Bedrock Converse API abstracts over multiple foundation models (Claude, Llama, Mistral, Titan). The iterate engine is not coupled to a single model provider.
- **Managed orchestration**: AWS Step Functions provides visual, debuggable, retry-aware state machines — a first-class orchestration primitive that the CLI implementations must simulate.
- **Team-native from day one**: Cloud deployment means multiple developers and CI/CD pipelines access the same iterate engine simultaneously. This is not a bolted-on multi-user extension; it is the primary operating mode.
- **Pay-per-invocation**: No idle compute. Every iterate call, every evaluator execution, every context retrieval is a metered API call.

This is the first implementation where the runtime is not a developer-local tool. The binding must bridge local developer experience (`.ai-workspace/`, git-based artifacts) with cloud-backed state and execution.

### Options Considered

1. **Direct SDK integration**: Thin Python wrapper calling Bedrock Runtime SDK directly. Orchestration logic lives in the wrapper (Lambda functions calling Lambda functions, or a monolithic orchestrator).
2. **Full serverless**: Every methodology concept maps to a separate AWS service. Maximum decomposition: one Lambda per evaluator, one DynamoDB table per concern, EventBridge for all routing.
3. **Hybrid cloud/local**: Step Functions for orchestration, Bedrock Runtime for LLM, Lambda for deterministic evaluators. Local `.ai-workspace/` for developer experience, DynamoDB/S3 for cloud state. CLI tool wraps API Gateway for developer ergonomics.

---

## Decision

**We adopt the Hybrid cloud/local binding (Option 3): Step Functions orchestration, Bedrock Runtime for LLM construction, Lambda for deterministic evaluators, with a local/cloud workspace bridge.**

Key mappings from methodology concepts to AWS services:

| Methodology Concept | AWS Binding | Rationale |
|:---|:---|:---|
| Iterate engine | Step Functions Standard Workflow (per edge type) | Visual debugging, native retry/timeout, execution history; maps 1:1 to graph edges |
| Candidate construction | Bedrock Runtime Converse API | Model-agnostic; supports Claude, Llama, Mistral, Titan without code changes |
| Deterministic evaluators (F_D) | Lambda container images | Isolated pytest/lint/schema execution; containerised for language-specific toolchains |
| Probabilistic evaluators (F_P) | Bedrock Runtime Converse API | Same model-agnostic interface used for construction; different prompt template |
| Human evaluators (F_H) | API Gateway + SNS + Step Functions `waitForTaskToken` | Asynchronous approval flow; human receives notification, responds via callback URL |
| Event store | DynamoDB (cloud canonical) / `events.jsonl` (local hybrid) | DynamoDB for team/CI access; local file for single-developer ergonomics |
| Feature vector state | DynamoDB `features` table | Atomic updates, query by REQ key, stream processing for projections |
| Context (large) | Bedrock Knowledge Bases (RAG) | Automatic chunking + vector retrieval for spec/ADR context |
| Context (config) | S3 objects / local `.ai-workspace/` | Edge configs, profiles, constraints — small files read directly |
| Multi-agent coordination | DynamoDB conditional writes | `PutItem` with `attribute_not_exists` provides atomic claim acquisition |
| Infrastructure deployment | CDK (TypeScript) | Infrastructure-as-code; reproducible, versionable, reviewable stacks |
| Developer entry point | CLI tool wrapping API Gateway | Local developer experience preserved; same `/gen-*` command vocabulary |
| CI/CD entry point | API Gateway RESTful endpoints | Webhook-triggered iteration; programmatic status queries |

---

## Rationale

### Why Hybrid Cloud/Local (vs Direct SDK)

**1. Separation of orchestration from execution** — Direct SDK integration conflates iterate logic with AWS API calls. The orchestrator becomes a monolithic Lambda that must manage retries, timeouts, state persistence, and error handling manually. Step Functions provides these natively, keeping iterate logic declarative and the execution surface managed.

**2. Debuggability** — Step Functions provides a visual execution graph with per-state input/output inspection, automatic execution history, and native CloudWatch integration. A direct SDK approach produces opaque Lambda logs that require manual correlation.

**3. The model says orchestration is graph traversal** — The Asset Graph Model defines iteration as graph edge traversal. Step Functions state machines are, literally, graph traversal engines. The structural alignment is not cosmetic; it means graph topology changes map directly to state machine definition changes.

### Why Hybrid Cloud/Local (vs Full Serverless)

**1. Operational complexity ceiling** — Full decomposition (one Lambda per evaluator type per edge, separate DynamoDB tables per concern, EventBridge rules for all routing) creates a combinatorial explosion of resources. For a 10-edge graph with 3 evaluator types, that is 30+ Lambda functions, 10+ DynamoDB tables, and dozens of EventBridge rules — before adding monitoring, permissions, and deployment automation.

**2. Developer experience** — Full serverless eliminates local development entirely. Developers cannot iterate on edge configs or test evaluators without deploying to AWS. The hybrid approach preserves `.ai-workspace/` as a local sandbox that syncs to cloud state when ready.

**3. Cost proportionality** — Full decomposition means even a simple status query fans out across multiple DynamoDB reads, Lambda invocations, and EventBridge events. The hybrid approach uses DynamoDB for state that needs cloud access and local files for developer-only workflows.

### Why Not CLI-First (Like Claude/Gemini/Codex)

**1. The gap this fills** — Three CLI-first implementations already exist. A fourth would add marginal value. The Bedrock binding addresses the team/CI/CD use case that CLI tools serve poorly: shared state, concurrent access, programmatic triggering, and cloud-native observability.

**2. Model agnosticism** — CLI implementations are bound to their host model (Claude Code uses Claude, Gemini CLI uses Gemini). Bedrock's Converse API decouples the iterate engine from the foundation model. Teams can choose the best model per edge type, or switch models without changing the implementation.

**3. First-class CI/CD integration** — API Gateway endpoints and EventBridge rules make CI/CD integration a configuration concern, not a scripting exercise. A CodePipeline stage can trigger `/gen-iterate` directly.

### Feature Vector Alignment

| Feature Vector | Bedrock Binding | Coverage |
|:---|:---|:---|
| REQ-F-ENGINE-001 | Step Functions + Bedrock Converse | Full |
| REQ-F-EVAL-001 | Lambda (F_D) + Bedrock (F_P) + API Gateway (F_H) | Full |
| REQ-F-CTX-001 | Knowledge Bases + S3 + context_manifest.yml | Full |
| REQ-F-TRACE-001 | DynamoDB features table + REQ-key tags | Full |
| REQ-F-EDGE-001 | Shared YAML edge params in S3 | Full |
| REQ-F-TOOL-001 | 13 commands via API Gateway + CLI wrapper | Full |
| REQ-F-LIFE-001 | EventBridge + CloudWatch + CodePipeline triggers | Full |
| REQ-F-SENSE-001 | EventBridge Scheduler + Lambda monitors | Full |
| REQ-F-UX-001 | CLI wrapper + API Gateway + progressive disclosure | Full |
| REQ-F-SUPV-001 | DynamoDB escalation queue + SNS alerts | Full |
| REQ-F-COORD-001 | DynamoDB conditional writes + S3 work isolation | Full |

**11/11 feature vectors aligned with Claude reference implementation.**

---

## Consequences

### Positive

- **Model-agnostic**: Teams choose foundation models per edge or per project — Claude for design, Llama for code generation, Mistral for rapid prototyping — without changing the iterate engine.
- **Team and CI/CD ready from day one**: Cloud deployment means shared state, concurrent access, and programmatic triggering are the default operating mode, not an afterthought.
- **Pay-per-use economics**: No idle compute. Iterate calls, evaluator executions, and context retrievals are metered. Quiet projects cost nearly nothing.
- **Visual debugging**: Step Functions execution history provides per-state inspection that no CLI implementation can match.
- **Infrastructure-as-code**: CDK stacks make the entire methodology infrastructure reproducible, versionable, and reviewable in pull requests.
- **Native observability**: X-Ray traces, CloudWatch metrics, and CloudTrail audit logs are available without additional tooling.

### Negative

- **Cold start latency**: Lambda cold starts (100ms-2s depending on runtime and container size) add latency to evaluator execution. Step Functions state transitions add ~50ms each. An iterate cycle with 6 states and 3 evaluators may see 500ms-3s of orchestration overhead beyond LLM inference time.
- **AWS vendor lock at design level**: While the Asset Graph Model is platform-agnostic and the specification is shared, this implementation binds deeply to AWS service APIs (Step Functions ASL, DynamoDB expressions, Bedrock Converse API, EventBridge rule syntax). Porting to GCP or Azure would require reimplementing the entire engine layer.
- **Operational complexity**: Even the hybrid approach requires managing IAM roles, DynamoDB capacity, S3 lifecycle policies, Lambda memory configuration, Step Functions definitions, API Gateway routes, SNS topics, and CDK deployment pipelines. The operational surface is significantly larger than any CLI implementation.
- **256KB state payload limit**: Step Functions Standard Workflows limit state transition payloads to 256KB. Large artifacts (generated code files, comprehensive test suites) must be passed by reference (S3 URI) rather than by value.
- **Local/cloud sync discipline**: The hybrid workspace requires developers to maintain consistency between local `.ai-workspace/` and cloud state. Stale local caches or missed syncs can cause subtle state divergence.

### Mitigation

- **Cold starts**: Use provisioned concurrency for frequently-invoked evaluator Lambdas. Use Express Workflows for deterministic-only edges (< 5 min, lower latency).
- **Vendor lock**: Keep methodology semantics in shared YAML configs and specification documents. AWS-specific bindings are isolated in `imp_bedrock/` — the methodology survives platform migration by writing a new `imp_<platform>/` binding.
- **Operational complexity**: CDK stacks encapsulate infrastructure complexity. `gen-init` bootstraps the full stack from a single command. CloudFormation drift detection catches manual changes.
- **Payload limits**: Store artifacts in S3 with versioned URIs. Step Functions states pass URIs, not content. Lambda evaluators fetch artifacts directly from S3.
- **Sync discipline**: DynamoDB streams trigger local cache invalidation via CLI tool polling. `gen-status --health` reports sync freshness.

---

## References

- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) — Bedrock implementation design
- [AISDLC_V2_DESIGN.md](../../imp_claude/design/AISDLC_V2_DESIGN.md) — reference implementation
- [CODEX_GENESIS_DESIGN.md](../../imp_codex/design/CODEX_GENESIS_DESIGN.md) — sibling design (CLI-first)
- [GEMINI_GENESIS_DESIGN.md](../../imp_gemini/design/GEMINI_GENESIS_DESIGN.md) — sibling design (CLI-first)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) — canonical model
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — requirements baseline (REQ-TOOL-001, REQ-TOOL-002, REQ-TOOL-003)
- [ADR-AB-002](ADR-AB-002-iterate-engine-step-functions.md) — Step Functions as iterate engine (detailed state machine design)
