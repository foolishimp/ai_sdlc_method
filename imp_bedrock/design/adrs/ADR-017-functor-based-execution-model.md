# ADR-017: Functor-Based Execution Model — Deterministic / Probabilistic / Human Rendering

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-SUPV-001, REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003
**Extends**: ADR-008 (Universal Iterate Agent), ADR-014 (IntentEngine Binding)
**Resolves**: Actor Model Review (gates v3.0)

---

## Context

The active task gating v3.0 asks: **which IntentEngine flows become deterministic code-backed vs. agent-driven vs. human-driven?** (ACTIVE_TASKS.md, Key Questions 1-5).

ADR-014 established that the IntentEngine is realised through the iterate engine and edge configs — configuration-only, no new engine code. The spec (SS4.6.2) defines three ambiguity regimes (zero, bounded, persistent) mapping to three processing phases (reflex, affect, conscious) and three evaluator types (deterministic, agent, human). ADR-016 established that design tolerances generate intents through the same pipeline.

The unresolved question: is the boundary between deterministic and probabilistic a **static design decision** (hardcoded per flow) or a **runtime parameter**? And if runtime, what controls it?

### The Insight

The three processing phases are not three different subsystems. They are **three renderings of the same objects**. Each functional unit in the system — evaluate, construct, classify, route, propose, sense — can be rendered as deterministic code, as a probabilistic agent, or as a human interaction. The choice of rendering is not fixed at design time; it is parameterised by:

1. **The current ambiguity level** — does this invocation have zero, bounded, or persistent ambiguity?
2. **The execution mode** — is the system running headless (CI/CD), interactive (CLI), or autopilot (EventBridge-triggered)?
3. **The affect valence** — how aggressively should the system escalate between renderings?

This is a **functor** in the category-theoretic sense (ontology SSV): a structure-preserving map from one category to another. The same object (same input type, same output type, same boundary) maps to different implementations that preserve the compositional structure.

### AWS Service Rendering

Bedrock Genesis has a natural advantage: the three functor categories map cleanly to distinct AWS service boundaries:
- **F_D** = Lambda functions (deterministic, fast, cheap)
- **F_P** = Bedrock Runtime Converse API (probabilistic, model-agnostic, metered)
- **F_H** = API Gateway + SNS + Step Functions `waitForTaskToken` (human, asynchronous, unbounded)

The service boundary between categories is explicit and observable. Each category has its own cost model, latency profile, and scaling characteristics. The natural transformation between categories (escalation) maps to Step Functions Choice states and task token callbacks.

---

## Decision

**Each functional unit in the IntentEngine has three renderings — deterministic (F_D), probabilistic (F_P), and human (F_H). The execution model is a functor composition: each unit starts in one category and escalates to the next via a natural transformation when ambiguity exceeds the current category's capacity. The starting category and escalation valence are runtime parameters, not static design choices.**

### The Three Categories — AWS Binding

| Category | Symbol | AWS Service | Regime | Cost | Speed |
|:---------|:-------|:------------|:-------|:-----|:------|
| **Deterministic** | F_D | Lambda container images | Ambiguity = 0 | ~$0.0001/invocation | Milliseconds |
| **Probabilistic** | F_P | Bedrock Runtime Converse API | Ambiguity bounded | ~$0.001-0.05/call | Seconds |
| **Human** | F_H | API Gateway + SNS + waitForTaskToken | Ambiguity persistent | $0 compute (waiting) | Minutes to days |

### The Rendering Table

Each functional unit maps to all three categories. The mapping preserves input/output types — the boundary (Markov blanket) is invariant across renderings:

| Functional Unit | F_D (Lambda) | F_P (Bedrock Converse) | F_H (API Gateway + waitForTaskToken) |
|:---------------|:-------------|:----------------------|:------------------------------------|
| **Evaluate** | pytest, coverage, schema validator, lint (Lambda container) | LLM coherence/gap review, design alignment check (Converse API) | Human review via callback URL, approval gate |
| **Construct** | Template expansion, code generation from schema (Lambda) | LLM generates candidate from context + intent (Converse API) | Human writes artifact directly (local editor) |
| **Classify** | Rule-based severity thresholds, regex pattern match (Lambda) | LLM classifies ambiguous signal, context-sensitive triage (Converse API) | Human triages manually (sensory review boundary) |
| **Route** | Topological sort, priority queue, dependency resolution (Lambda) | LLM picks optimal next edge from heuristic context (Converse API) | Human chooses what to work on (CLI/console) |
| **Propose** | Template-driven proposal from structured input (Lambda) | LLM drafts intent, diff, or spec modification (Converse API) | Human writes proposal from scratch |
| **Sense** | CloudWatch Alarm, EventBridge cron, Lambda monitor (Lambda) | LLM interprets telemetry pattern, anomaly detection (Converse API) | Human notices something |
| **Emit** | DynamoDB write — **always deterministic** (Lambda) | -- | -- |
| **Decide** | -- | -- | API Gateway callback — **always human** |

**Category-fixed units**: Emit is always F_D (it is a pure side effect — append structured data to DynamoDB). Decide is always F_H (this is the review boundary invariant from ADR-015 / REQ-EVAL-003). All other units are **category-variable** — renderable in any category depending on ambiguity.

### Escalation as Natural Transformation

When a unit rendered in category C produces ambiguity that exceeds C's capacity, the **natural transformation eta** re-renders the same unit in the next category:

```
eta_D->P :  F_D(unit) produces ambiguity > 0        ->  re-render as F_P(unit)
eta_P->H :  F_P(unit) produces persistent ambiguity  ->  re-render as F_H(unit)
```

**AWS implementation of eta:**

- **eta_D->P**: Step Functions **Choice state** evaluates Lambda output. If the Lambda evaluator returns `{ "ambiguity": "bounded", ... }`, the Choice state routes to the Bedrock Converse task state instead of proceeding to convergence check. Same input payload, different service.

- **eta_P->H**: Step Functions **waitForTaskToken** state. When the Bedrock Converse evaluator returns `{ "ambiguity": "persistent", ... }`, the state machine emits a task token, sends an SNS notification with a callback URL, and pauses. The human responds via API Gateway callback. The state machine resumes with the human's decision.

The escalation preserves the unit's boundary — same input type, same output type. Only the implementation (and the AWS service invoked) changes:

```
F_D(Evaluate) fails     ->  eta_D->P  ->  F_P(Evaluate) tries    ->  eta_P->H  ->  F_H(Evaluate) decides
  Lambda pytest pass/fail       |          Bedrock says "gap found"       |          Human says "approved"
  but can't assess design       |          but can't resolve conflict      |
  coherence (ambiguity > 0)     |          (persistent ambiguity)          |
                                 |                                          |
                          Choice state                             waitForTaskToken
                          same I/O types                           same I/O types
```

### The Starting Functor Determines the Mode

The execution mode is **which category the system starts in**:

**Headless mode (start F_D -> escalate up):** Bottom-up. Lambda handles what it can, Bedrock handles the rest, human handles what is left. CI/CD mode — Step Functions workflows triggered by CodePipeline or EventBridge. Maximum automation; well-constrained edges may never reach F_P.

**Interactive mode (start F_H -> delegate down):** Top-down. Human directs via CLI, Bedrock constructs, Lambda validates. Developer-driven `gen-iterate`. Maximum control.

**Autopilot mode (start F_D -> valence-controlled escalation):** Hybrid. Start deterministic, but the **affect valence** controls how aggressively eta fires. EventBridge-triggered unattended iteration.

| Profile | Valence | Escalation Behaviour |
|:--------|:--------|:---------------------|
| **hotfix** | High (escalate aggressively) | F_D -> eta_D->P fires immediately on any nonzero -> eta_P->H fires quickly -> human decides fast. SNS notification with CRITICAL priority. |
| **standard** | Medium (normal thresholds) | F_D -> eta_D->P after deterministic tests fail -> F_P iterates up to `max_iterations` -> eta_P->H after `stuck_threshold`. Balanced automation and oversight. |
| **spike** | Low (suppress escalation) | F_D -> F_P -> iterate extensively before eta_P->H fires. Explore the space. Tolerate ambiguity. Escalate only when truly stuck. |
| **poc** | Low | Similar to spike — optimise for exploration over convergence. |

The affect field in the feature vector (ADR-014) is the **control signal for the natural transformation**:

```yaml
# In feature vector state (DynamoDB features table)
affect:
  urgency: normal          # Controls eta_P->H sensitivity
  source: profile          # What set the current valence
  escalation_count: 0      # Tracks how many times eta has fired
  valence: medium          # Controls eta_D->P sensitivity
```

The `valence` parameter is the threshold for the natural transformation. It determines how much ambiguity the current category tolerates before re-rendering in the next category.

### Configuration Binding

The functor composition is configured at three levels, matching the engine's three-layer architecture (SS2.7):

| Layer | What It Configures | Bedrock Binding |
|:------|:-------------------|:----------------|
| **Engine** (Layer 1) | The natural transformation mechanism — how eta fires | CDK stack: Lambda layers, Step Functions ASL definitions, Choice state conditions, waitForTaskToken timeout |
| **Graph Package** (Layer 2) | Default rendering per functional unit per edge | S3 config: `code_unit_tests.evaluate: start_F_D`, `intent_requirements.construct: start_F_P` |
| **Project Binding** (Layer 3) | Mode override, valence override, per-edge rendering override | Per-project CDK construct: `mode: headless`, `valence: high`, `design_code.evaluate: start_F_H` |

Edge configs (ADR-009) already encode this implicitly:

```yaml
# Existing edge config -- now understood as functor assignment
edge:
  type: code_unit_tests
  evaluators:
    deterministic:           # <- F_D rendering of Evaluate (Lambda container)
      - pytest_pass
      - coverage_threshold
    agent:                   # <- F_P rendering of Evaluate (Bedrock Converse API)
      - code_coherence
      - req_tag_coverage
    human:                   # <- F_H rendering of Evaluate (waitForTaskToken + API Gateway)
      - design_approval
  convergence:
    max_iterations: 5        # <- eta_P->H threshold
    stuck_threshold: 3       # <- urgency escalation trigger
```

The existing evaluator taxonomy in edge configs **already is** the functor rendering table. This ADR names the pattern and makes the execution mode (starting functor) and valence (escalation threshold) explicit configuration rather than implicit behaviour.

### Runtime Architecture

The functor model answers the active task's runtime architecture question (Key Question 4):

The runtime is Step Functions state machines (ADR-AB-002) with functor-parameterised service invocations. Lambda for F_D, Bedrock for F_P, waitForTaskToken for F_H. The Choice state between evaluator stages is the natural transformation eta. DynamoDB conditional writes (ADR-AB-005) manage coordination **between** agents orthogonally; the functor controls **within** a single iterate execution.

Starting functor: `config.mode` (headless | interactive | autopilot). Valence: `config.valence` (high | medium | low) or `affect.valence`.

---

## Rationale

### Why This Answers the v3.0 Gate Questions

**Q1: Which flows should be deterministic code?**
Not a static answer. Each functional unit *starts* deterministic (F_D) where possible. The rendering table enumerates the F_D implementation (Lambda container image) for each unit. If F_D can handle the invocation (ambiguity = 0), it does. No LLM involved. No Bedrock cost.

**Q2: Which flows remain probabilistic?**
Same answer, inverted. F_P handles what F_D cannot. The unit is the same; the rendering changes — Lambda to Bedrock Converse. The boundary is not "these flows are deterministic, those are probabilistic" — it is "this invocation's ambiguity determines which rendering fires."

**Q3: Where is the boundary?**
The natural transformation eta, implemented as a Step Functions Choice state. It fires when ambiguity exceeds the current category's capacity. The boundary moves per invocation, per edge, per profile. It is not a static line in the architecture.

**Q4: What is the runtime architecture?**
Step Functions state machines (ADR-AB-002) with functor-parameterised service invocations. No new orchestration layer. The state machine structure from ADR-AB-002 already separates deterministic, probabilistic, and human evaluator stages. The functor model names this pattern and makes mode and valence explicit.

**Q5: How do tolerances wire to monitors?**
Tolerances (ADR-016) are F_D(Sense) invocations — CloudWatch Alarms fire on metric thresholds. When an alarm fires, ambiguity > 0, and eta_D->P engages: the breach enters probabilistic triage (F_P(Classify) via Bedrock Converse). If triage resolves it (generates optimisation intent), done. If persistent, eta_P->H fires: human reviews the proposed technology rebinding via API Gateway callback.

### Why a Functor (Not Static Assignment)

1. **The same edge needs different renderings in different contexts.** A hotfix profile should escalate immediately; a spike profile should let Bedrock iterate extensively. The rendering must be parameterised by affect.
2. **The direction of traversal matters.** Headless starts F_D and escalates up. Interactive starts F_H and delegates down. Same functional units, different starting functor.
3. **The existing config already encodes it.** Edge YAML separates `deterministic`, `agent`, and `human` evaluators. The functor model names what is there and adds mode and valence.
4. **AWS services provide natural category boundaries.** Lambda, Bedrock, and API Gateway have distinct cost models, scaling, and observability — concrete category boundaries.

### Why Not New Engine Code (Yet)

This ADR extends ADR-014's "configuration-only" decision. The functor dispatch maps onto Step Functions state machines (ADR-AB-002). Making `mode` and `valence` explicit config changes how we compose edge configs without new state machine code. When the engine matures, the dispatch becomes a literal CDK construct: `render(unit, category) -> ASL_state_definition`.

### Ontology Grounding

The functor model instantiates the ontology's formal programme: F_D/F_P/F_H are three categories with structure-preserving maps between them (ontology #58-64). F_D = deterministic compute, F_P = probabilistic compute (#45), F_H = human compute. The natural transformation eta is the teleodynamic self-repair mechanism (#49) — when one rendering fails, the system adapts by re-rendering via Choice state or waitForTaskToken. Scale-dependent observation (#23) means the same unit at different scales starts in different categories: iteration-level Evaluate starts F_D (Lambda tests), feature-level starts F_P (Bedrock coherence), spec-level starts F_H (human judgment).

---

## Consequences

### Positive

- **Answers the v3.0 gate** — the boundary between deterministic and probabilistic is not a line to draw but a threshold to configure. The five key questions have principled answers.
- **No new infrastructure** — the functor model is a design interpretation of existing Step Functions state machine structure. Evaluator sections, Choice states, and waitForTaskToken already encode functor assignments.
- **Unified execution model** — headless (CI/CD-triggered), interactive (CLI-driven), and autopilot (EventBridge-triggered) are not three different architectures. They are three starting conditions for the same functor composition.
- **Observable per-category** — CloudWatch metrics, X-Ray traces, and cost allocation tags are naturally scoped to AWS service boundaries (Lambda, Bedrock, API Gateway). Each functor category has independent observability without custom instrumentation.
- **Cost-transparent** — F_D (Lambda) is cheap. F_P (Bedrock) is moderate. F_H (API Gateway + human wait) is free compute but expensive human time. The functor model makes the cost trade-off explicit and tunable via valence.
- **Composable** — valence can be tuned per edge, per profile, per project. A single project can have hotfix-valence edges (escalate fast) and spike-valence edges (explore broadly).
- **Future-proof** — when the CDK construct matures, the functor dispatch becomes a literal code path: `render(unit, category) -> ASL_state_definition`. The conceptual model maps directly to implementation.

### Negative

- **Conceptual density** — functor language adds abstraction overhead for developers unfamiliar with category theory. Mitigated: the rendering table is a concrete lookup; the category theory is explanatory, not operational. Developers interact with edge YAML, not functors.
- **Valence tuning** — initial valence values per profile will need calibration through use. Mitigated: sensible defaults (hotfix=high, standard=medium, spike=low) and the tolerance mechanism (ADR-016) auto-adjusts through feedback.
- **Testing escalation paths** — the natural transformations (eta_D->P via Choice state, eta_P->H via waitForTaskToken) need integration tests that verify re-rendering preserves boundaries. This adds test burden on the CDK construct that generates state machine definitions.
- **Step Functions ASL complexity** — encoding functor dispatch in ASL Choice states adds branching complexity to state machine definitions. Mitigated: the CDK `IterateStateMachine` construct (ADR-AB-002) generates ASL from edge YAML; developers do not write ASL directly.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) SS2.7 (Three Layers), SS4.1 (Evaluator Types), SS4.3 (Three Processing Phases), SS4.6 (IntentEngine), SS4.6.2 (Ambiguity Classification), SS4.6.6 (Consciousness as Relative), SS11.1 (Hilbert Space)
- [Constraint-Emergence Ontology](https://github.com/foolishimp/constraint_emergence_ontology) SSV (Category Theory / Functors), #45 (Two Compute Regimes), #49 (Teleodynamic Self-Maintenance)
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) SS1.3 (Universal Iterate Orchestration), SS2.1 (Asset Graph Engine)
- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) — Bedrock Runtime as platform (F_P cost model)
- [ADR-AB-002](ADR-AB-002-iterate-engine-step-functions.md) — Step Functions as iterate engine (state machine structure maps to functor composition)
- [ADR-AB-004](ADR-AB-004-human-review-api-gateway-callbacks.md) — API Gateway human review (F_H implementation via waitForTaskToken)
- [ADR-008](../../imp_claude/design/adrs/ADR-008-universal-iterate-agent.md) — Universal Iterate Agent (execution substrate concept)
- [ADR-009](../../imp_claude/design/adrs/ADR-009-graph-topology-as-configuration.md) — Graph Topology as Configuration (edge configs encode functor assignments in evaluator sections)
- [ADR-013](../../imp_claude/design/adrs/ADR-013-multi-agent-coordination.md) — Multi-Agent Coordination (orthogonal to functor model)
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding (configuration-only decision extended with mode and valence)
- [ADR-015](ADR-015-sensory-service-technology-binding.md) — Sensory Service Technology Binding (review boundary = F_H(Decide) is category-fixed)
- [ADR-016](ADR-016-design-tolerances-as-optimization-triggers.md) — Design Tolerances (tolerance monitoring = F_D(Sense) with escalation via eta)

---

## Requirements Addressed

- **REQ-SUPV-001**: IntentEngine interface — the functor model formalises how IntentEngine selects between deterministic (Lambda), probabilistic (Bedrock Converse), and human (API Gateway + waitForTaskToken) processing
- **REQ-EVAL-001**: Deterministic evaluator — F_D rendering of Evaluate via Lambda container images, always attempted first
- **REQ-EVAL-002**: Agent evaluator — F_P rendering of Evaluate via Bedrock Converse API, invoked via eta_D->P (Choice state) when ambiguity > 0
- **REQ-EVAL-003**: Human accountability — F_H(Decide) is category-fixed; the review boundary invariant is preserved structurally via waitForTaskToken (no autonomous approval)
