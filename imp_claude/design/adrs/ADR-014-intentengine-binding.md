# ADR-014: IntentEngine Binding — Claude Code Implementation

**Status**: Accepted
**Date**: 2026-02-22
**Deciders**: Methodology Author
**Requirements**: REQ-SUPV-001
**Extends**: ADR-008 (Universal Iterate Agent), ADR-011 (Consciousness Loop)

---

## Context

The specification (§4.6) introduces the **IntentEngine** as a composition law over the four primitives: `IntentEngine(intent + affect) = observer → evaluator → typed_output(reflex.log | specEventLog | escalate)`. This is not a fifth primitive but the universal processing unit that operates on every edge, at every scale, chaining fractally.

The Claude Code implementation must bind this abstract pattern to concrete platform mechanisms. The key decisions are:

1. How do the three output types (`reflex.log`, `specEventLog`, `escalate`) map to Claude Code artifacts?
2. How is ambiguity classification (zero / bounded / persistent) implemented?
3. How does affect propagation work across chained invocations?
4. Where are the thresholds between deterministic and probabilistic compute configured?

### Options Considered

1. **New engine code** — build an IntentEngine runtime that wraps the iterate agent
2. **Configuration-only** — express IntentEngine semantics through existing edge configs and evaluator checklists
3. **Hybrid** — IntentEngine is a conceptual framework applied by the iterate agent; edge configs parameterise the ambiguity thresholds and affect weights

---

## Decision

**The IntentEngine is realised through the existing iterate agent (ADR-008) and edge configuration system (ADR-009). No new executable code is required. The iterate agent already implements the observer→evaluator→output pattern; edge configs parameterise ambiguity thresholds and affect weights. The three output types map to existing event types and control flow.**

### Output Type Mapping

| Spec output type | Claude Code realisation | Event type | Control flow |
|-----------------|----------------------|-----------|-------------|
| `reflex.log` | Event emission + continue/promote | `iteration_completed`, `edge_converged`, `interoceptive_signal` (within bounds) | Automatic — no human involvement |
| `specEventLog` | Deferred intent logged for next iteration | `iteration_completed` (with non-zero delta), `affect_triage` (deferred) | Iterate again, or queue for batch review |
| `escalate` | Human review or spawn | `intent_raised`, `convergence_escalated`, `spawn_created` | Block until human decides |

### Ambiguity Classification Binding

The three ambiguity regimes map to the three evaluator types already in the edge configs:

| Ambiguity regime | Evaluator type | Claude Code mechanism |
|-----------------|---------------|---------------------|
| **Zero** (reflex) | Deterministic Tests | `pytest`, `tsc`, `eslint`, schema validators — pass/fail, no LLM involved |
| **Bounded nonzero** (probabilistic) | Agent(intent, context) | Claude LLM invocation with constrained context window — gap analysis, coherence check, candidate generation |
| **Persistent** (escalate) | Human | `/aisdlc-review` or automatic escalation after `max_iterations` exceeded |

### Ambiguity Threshold Configuration

Thresholds are configured per edge in the edge YAML files (ADR-009):

```yaml
# Example: code_unit_tests.yml
edge:
  type: code_unit_tests
  evaluators:
    deterministic:
      - pytest_pass          # ambiguity = 0: pass/fail
      - coverage_threshold   # ambiguity = 0: above/below 80%
    agent:
      - code_coherence       # ambiguity bounded: LLM assesses design alignment
      - req_tag_coverage     # ambiguity bounded: LLM checks REQ key presence
    human:
      - design_approval      # ambiguity persistent: human judgment required
  convergence:
    max_iterations: 5        # escalate to human after 5 non-converging iterations
    stuck_threshold: 3       # emit intent_raised after 3 iterations with same delta
```

The `max_iterations` and `stuck_threshold` parameters are the **escalation boundaries** — they determine when bounded ambiguity is reclassified as persistent. These are tuneable per edge, per profile (ADR-009), and per project (`project_constraints.yml`).

### Affect Propagation

Affect (urgency, valence) is carried in the feature vector state and edge context:

- **Profile-derived urgency**: Hotfix profile sets high base urgency on all edges; spike profile sets low urgency
- **Signal-derived urgency**: Sensory signals (ADR-015) carry severity that propagates into affect when they trigger iterate
- **Iteration-derived urgency**: Each non-converging iteration increases urgency (the `stuck_threshold` is an urgency escalation point)
- **Propagation mechanism**: The iterate agent reads the feature vector's `urgency` field and the edge's `affect_weights` from config. These colour the evaluator's escalation decisions.

```yaml
# In feature vector state
affect:
  urgency: normal        # low | normal | high | critical
  source: profile        # profile | signal | iteration | human
  escalation_count: 0    # how many times this vector has escalated
```

### Consciousness-as-Relative in Claude Code

Level N's `escalate` becomes Level N+1's reflex:

| Level | Claude Code mechanism | N's escalate becomes N+1's... |
|-------|---------------------|------------------------------|
| Single iteration | iterate agent cycle | Input to next iteration (specEventLog) or spawn/review (escalate) |
| Edge convergence | Edge completion in `/aisdlc-iterate` | Automatic routing to next edge by `/aisdlc-start` (reflex at feature level) |
| Feature traversal | Feature vector state machine | Status update triggering `/aisdlc-status` health check (reflex at project level) |
| Sensory monitor | Sensory service signal (ADR-015) | Affect triage input — rule-based classification (reflex at triage level) |
| Spec review | `/aisdlc-review` output | New intent entering the graph — handled as standard feature creation (reflex at project level) |

---

## Rationale

### Why Configuration-Only (vs New Engine Code)

1. **The iterate agent already IS the IntentEngine** — it observes (runs constructor), evaluates (checks evaluators), and produces typed output (converge, iterate, or escalate). Naming the pattern doesn't require new runtime code.

2. **Edge configs already parameterise ambiguity** — `max_iterations`, evaluator composition, and convergence thresholds in YAML already control the boundary between deterministic and probabilistic and escalation. The IntentEngine formalisation explains WHY these parameters exist.

3. **No additional abstraction layer** — Adding an IntentEngine wrapper around the iterate agent would add indirection without capability. The iterate agent is already the single entry point (ADR-008).

### Why Explicit Affect in Feature Vector State

1. **Observable** — urgency stored in feature vector state is visible in `/aisdlc-status` and in events.jsonl
2. **Tuneable** — profiles adjust base urgency; project constraints can override
3. **Propagates** — child vectors inherit parent affect (spawn carries urgency forward)

---

## Consequences

### Positive

- **Zero new code** — IntentEngine binding is purely configurational, extending existing edge YAML schemas
- **Explicit ambiguity thresholds** — `max_iterations`, `stuck_threshold`, evaluator composition are now understood as ambiguity classification boundaries, not arbitrary parameters
- **Affect is observable** — urgency propagation is in the event log, enabling methodology self-observation (ADR-011)
- **Consciousness-as-relative is automatic** — the existing level hierarchy (iteration → edge → feature → project) already implements this via `/aisdlc-start` routing

### Negative

- **Conceptual overhead** — developers must understand the IntentEngine model to tune thresholds effectively. Mitigated by sensible defaults in the graph package.
- **Affect schema addition** — feature vector YAML gains an `affect` section. Mitigated by optional defaults (urgency: normal if omitted).

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.6 (IntentEngine)
- [ADR-008](ADR-008-universal-iterate-agent.md) — Universal Iterate Agent (the iterate agent IS the IntentEngine)
- [ADR-009](ADR-009-graph-topology-as-configuration.md) — Graph Topology as Configuration (edge configs encode ambiguity thresholds)
- [ADR-011](ADR-011-consciousness-loop-at-every-observer.md) — Consciousness Loop (signal sources are affect-phase observers)
- [ADR-015](ADR-015-sensory-service-technology-binding.md) — Sensory Service Technology Binding (continuous signal source feeding IntentEngine)
- [ADR-016](ADR-016-design-tolerances-as-optimization-triggers.md) — Design Tolerances (tolerance breaches generate optimization intents via the IntentEngine pipeline)

---

## Requirements Addressed

- **REQ-SUPV-001**: IntentEngine interface — observer → evaluator → typed_output, parameterised by intent+affect
