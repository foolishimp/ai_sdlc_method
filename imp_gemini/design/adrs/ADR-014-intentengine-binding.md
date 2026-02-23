# ADR-014: IntentEngine Binding — Gemini CLI Implementation

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-SUPV-001
**Extends**: ADR-008 (Universal Iterate Agent), ADR-011 (Consciousness Loop)

---

## Context

The specification (§4.6) introduces the **IntentEngine** as a composition law over the four primitives: `IntentEngine(intent + affect) = observer → evaluator → typed_output(reflex.log | specEventLog | escalate)`. This is not a fifth primitive but the universal processing unit that operates on every edge, at every scale, chaining fractally.

The Gemini CLI implementation must bind this abstract pattern to concrete platform mechanisms.

---

## Decision

**The IntentEngine is realised through the existing iterate agent (ADR-008) and edge configuration system (ADR-009). No new executable code is required. The iterate agent already implements the observer→evaluator→output pattern; edge configs parameterise ambiguity thresholds and affect weights. The three output types map to existing event types and control flow.**

### Output Type Mapping

| Spec output type | Gemini CLI realisation | Event type | Control flow |
|-----------------|----------------------|-----------|-------------|
| `reflex.log` | Event emission + continue/promote | `iteration_completed`, `edge_converged`, `interoceptive_signal` (within bounds) | Automatic — no human involvement |
| `specEventLog` | Deferred intent logged for next iteration | `iteration_completed` (with non-zero delta) | Iterate again, or queue for batch review |
| `escalate` | Human review or spawn | `intent_raised`, `convergence_escalated`, `spawn_created` | Block until human decides |

### Ambiguity Classification Binding

The three ambiguity regimes map to the three evaluator types already in the edge configs:

| Ambiguity regime | Evaluator type | Gemini CLI mechanism |
|-----------------|---------------|---------------------|
| **Zero** (reflex) | Deterministic Tests | `pytest`, `ruff`, `mypy`, schema validators — pass/fail, no LLM involved |
| **Bounded nonzero** (probabilistic) | Agent(intent, context) | Gemini LLM invocation with constrained context window — gap analysis, coherence check, candidate generation |
| **Persistent** (escalate) | Human | `ask_user` tool or automatic escalation after `max_iterations` exceeded |

### Ambiguity Threshold Configuration

Thresholds are configured per edge in the edge YAML files:

```yaml
# Example: tdd.yml
convergence:
  max_iterations: 5        # escalate to human after 5 non-converging iterations
  stuck_threshold: 3       # emit intent_raised after 3 iterations with same delta
```

### Affect Propagation

Affect (urgency, valence) is carried in the feature vector state and edge context:

- **Profile-derived urgency**: Hotfix profile sets high base urgency on all edges; spike profile sets low urgency.
- **Iteration-derived urgency**: Each non-converging iteration increases urgency.
- **Propagation mechanism**: The iterate agent reads the feature vector's `urgency` field.

```yaml
# In feature vector state
affect:
  urgency: normal        # low | normal | high | critical
  source: profile        # profile | signal | iteration | human
  escalation_count: 0    # how many times this vector has escalated
  valence: medium        # threshold for natural transformation
```

---

## Rationale

### Why Configuration-Only

1. **The iterate agent already IS the IntentEngine** — it observes, evaluates, and produces typed output.
2. **Edge configs already parameterise ambiguity** — `max_iterations`, evaluator composition, and convergence thresholds in YAML already control the boundary between deterministic and probabilistic and escalation.

---

## Consequences

### Positive

- **Zero new code** — IntentEngine binding is purely configurational.
- **Explicit ambiguity thresholds** — now understood as ambiguity classification boundaries.
- **Affect is observable** — urgency propagation is in the event log.

### Negative

- **Conceptual overhead** — developers must understand the IntentEngine model to tune thresholds effectively.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.6 (IntentEngine)
- [ADR-008](ADR-008-universal-iterate-agent.md) — Universal Iterate Agent
- [ADR-009](ADR-009-graph-topology-as-configuration.md) — Graph Topology as Configuration
