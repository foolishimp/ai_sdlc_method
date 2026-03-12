# STRATEGY: Industrial cloud substrate for Genesis on AWS vs GCP

**Author**: codex
**Date**: 2026-03-13T03:39:51+11:00
**Addresses**: future industrial deployment direction for Genesis; event bus + workflow durability + model execution architecture
**For**: all

## Summary
If Genesis is to operate as an industrial, fault-tolerant system, the architecture should not be organized around agent frameworks first. It should be organized around four layers:
- canonical Genesis event authority
- robust cloud event transport
- durable workflow orchestration
- probabilistic model execution

In that structure, AWS and GCP are both viable. The important design rule is invariant across providers: the bus transports events, the workflow engine coordinates work, and Genesis retains authority through its append-only event log and deterministic projections.

## Core Architectural Rule
Genesis should preserve this separation:

1. **Authority layer**
   - append-only canonical Genesis event log
   - deterministic projections
   - convergence and evidence checks
   - traceability and auditability

2. **Event transport layer**
   - durable fan-out
   - retries
   - dead-letter handling
   - decoupling between observers and workers

3. **Workflow orchestration layer**
   - long-running sagas
   - retries and compensation
   - timeout handling
   - human gates and callback waits
   - supervision of distributed work

4. **Model / agent execution layer**
   - LLM calls
   - tool use
   - bounded probabilistic work
   - provider-specific execution contracts

The most important point is:

**The event bus is not the source of truth.**

The canonical Genesis event log remains the truth substrate. Cloud transport moves events around that truth; it does not replace it.

## Why This Split Matters
Without this split, the system collapses into one of two bad shapes:

- `agent framework as authority`
  - poor replay guarantees
  - weak auditability
  - semantic drift between runtime and formal model

- `event bus as authority`
  - transport concerns leak into methodology semantics
  - ordering/retry behavior becomes mistaken for truth
  - projection equivalence becomes harder to guarantee

Genesis should instead work like this:
1. canonical event is appended to the Genesis authority log
2. event is published onto the transport layer
3. observers and workflows consume it
4. work executes
5. resulting state transitions emit new canonical events back into the authority log

That preserves replay, audit, and convergence semantics.

## AWS Shape
AWS is the stronger default fit if the priority is durable orchestration and industrial reliability.

### Transport layer
- `EventBridge` for routing and coarse-grained event distribution
- `SQS` for buffering, consumer isolation, retry behavior, and DLQ
- `SNS` only where broad fan-out is helpful

### Workflow layer
- `Step Functions Standard` as the durable saga engine
- callback tasks / human approval for F_H boundaries
- retries, wait states, supervision, and compensation policies at workflow level

### Model layer
- `Amazon Bedrock` or Bedrock Agents as probabilistic worker execution
- model/tool calls inside bounded workflow steps
- not the authority substrate

### Authority layer
- append-only Genesis event log retained separately
- projections built from Genesis events, not from Step Functions history alone

### Why AWS is attractive
- strong long-running orchestration semantics
- good DLQ and retry primitives
- mature event-routing stack
- straightforward human-in-the-loop patterns
- good fit for fault-tolerant sagas

## GCP Shape
GCP is a strong alternative if Gemini/Vertex AI is strategically preferred.

### Transport layer
- `Pub/Sub` for event delivery and fan-out
- dead-letter topics and retry control

### Workflow layer
- `Cloud Workflows` for orchestration
- callback endpoints for human gate / wait semantics
- Cloud Run for worker execution boundaries

### Model layer
- `Vertex AI Gemini` for probabilistic work
- function/tool calling inside controlled worker surfaces

### Authority layer
- append-only Genesis event log retained separately
- deterministic projections remain Genesis-owned

### Why GCP is attractive
- strong Gemini integration
- clean managed event transport with Pub/Sub
- workable orchestration path with Workflows + Cloud Run
- good fit if model platform preference points to Google

## Provider-Neutral Genesis Contract
A cloud substrate is acceptable only if it preserves these Genesis properties:

1. `Projection authority`
   - workspace state and convergence claims must remain derivable from canonical Genesis events

2. `Replay equivalence`
   - the same event stream must produce the same projected state independent of cloud runtime history

3. `Deterministic F_D boundaries`
   - deterministic checks must remain explicit, inspectable, and replay-visible

4. `REQ-threaded evidence`
   - requirements, features, runs, artifacts, tests, and decisions must remain linked through the event/evidence surface

5. `Human gate integrity`
   - F_H boundaries must be explicit, auditable, and non-silent

6. `Idempotent orchestration`
   - retries at transport/workflow level must not corrupt the authority layer

If a proposed cloud stack cannot preserve those, it is not a valid Genesis substrate regardless of its agent tooling.

## Suggested Industrial Reference Shape
The likely long-term industrial architecture is:

```text
Genesis canonical event log
  -> projection/evidence layer
  -> publish canonical events to event bus
  -> workflow engine consumes + coordinates
  -> worker/model services execute bounded steps
  -> results emit new canonical Genesis events
  -> projections refresh from canonical events only
```

This keeps Genesis semantically stable while allowing cloud-native resilience.

## Where the Event Bus Belongs
The event bus should be used for:
- observer fan-out
- decoupled processing
- retries and backpressure
- consumer isolation
- dead-letter handling
- multi-service coordination

The event bus should not be used as:
- the sole audit source
- the projection substrate
- the methodology authority surface
- the sole evidence of convergence

That distinction should become an explicit architectural invariant.

## Cloud Comparison Criteria
A serious spike should compare AWS and GCP only on criteria that matter to Genesis:

1. replayability of canonical event authority
2. idempotent retry behavior
3. DLQ and failure isolation quality
4. human gate / callback support
5. workflow durability for long-running sagas
6. observability of workflow and worker behavior
7. ease of preserving deterministic F_D boundaries
8. ease of preserving REQ-threaded evidence
9. operational complexity and maintenance burden
10. fit with future multi-project / multi-tenant operation

This is a better evaluation frame than generic model quality or generic agent framework popularity.

## Recommendation
The best next move is not to build immediately. It is to frame two future spike vectors:

### Spike A: AWS industrial Genesis substrate
Evaluate:
- EventBridge + SQS + DLQ
- Step Functions Standard
- Bedrock for probabilistic workers
- Genesis-owned canonical event log and projections

### Spike B: GCP industrial Genesis substrate
Evaluate:
- Pub/Sub + DLQ
- Cloud Workflows + Cloud Run
- Vertex AI Gemini for probabilistic workers
- Genesis-owned canonical event log and projections

## Position
If the goal is industrial fault-tolerant workflows, this is the right direction.

Not:
- agent framework first
- model vendor first
- UI first

But:
- authority first
- orchestration second
- transport third
- model execution fourth

Genesis should remain the methodology authority and event-sourced truth layer. Cloud infrastructure should make it robust, scalable, and fault-tolerant without becoming the semantic source of truth.

## Recommended Action
1. Treat robust cloud deployment as a future substrate investigation, not a current implementation task.
2. Make `event bus != authority log` an explicit architecture rule.
3. Define future AWS and GCP spike vectors using the same Genesis invariants.
4. Evaluate each provider by replay/projection integrity and workflow resilience, not by agent-framework convenience.
5. Preserve Genesis canonical events as the single truth surface across all cloud implementations.
