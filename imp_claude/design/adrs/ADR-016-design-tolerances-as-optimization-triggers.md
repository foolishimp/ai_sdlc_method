# ADR-016: Design Tolerances as Optimization Triggers

**Status**: Accepted
**Date**: 2026-02-22
**Deciders**: Methodology Author
**Requirements**: REQ-SUPV-002, REQ-SENSE-001, REQ-SENSE-002
**Extends**: ADR-014 (IntentEngine Binding), ADR-015 (Sensory Service Technology Binding)

---

## Context

ADR-014 and ADR-015 capture technology bindings — the decisions that map spec abstractions to Claude Code mechanisms (MCP server, Claude headless, edge YAML configs). These bindings are recorded as choices but not yet as **monitored constraints with tolerances**.

The insight: every technology binding implies tolerances. Every tolerance is a threshold the sensory system can monitor. Every breach is an optimization intent waiting to be raised.

### The Gap

Current design documents say WHAT was chosen but not:
- What performance, cost, or quality tolerances the choice implies
- What monitoring signals detect tolerance breaches
- What happens when a better option emerges or a tolerance is exceeded

Without explicit tolerances, design decisions are static. With them, the design layer becomes a homeostatic surface — it evaluates itself and generates intents when its own constraints shift.

---

## Decision

**Design documents (ADRs, design docs) should capture technology-specific tolerances alongside binding decisions. These tolerances are monitored by the sensory service (ADR-015) and breaches generate optimization intents via the IntentEngine (ADR-014).**

### Tolerance Structure

Each technology binding can declare tolerances:

```yaml
# Example: design_tolerances.yml
tolerances:
  mcp_server:
    binding: ADR-015  # which ADR made this choice
    monitors:
      - metric: sensory_service_startup_time
        threshold: 5s
        direction: below  # healthy when below
        signal: EXTRO-003  # which exteroceptive monitor watches this
      - metric: mcp_protocol_overhead_per_tool
        threshold: 100ms
        direction: below
        signal: INTRO-005

  claude_headless:
    binding: ADR-015
    monitors:
      - metric: probabilistic_classification_latency
        threshold: 10s
        direction: below
        signal: INTRO-006
      - metric: classification_cost_per_signal
        threshold: $0.02
        direction: below
        signal: EXTRO-004

  edge_yaml_configs:
    binding: ADR-009
    monitors:
      - metric: config_parse_time
        threshold: 500ms
        direction: below
        signal: INTRO-007
      - metric: topology_file_count
        threshold: 50
        direction: below
        signal: INTRO-008
```

### Breach → Intent Pipeline

When a tolerance is breached, the standard IntentEngine pipeline fires:

```
Tolerance breached
    → Sensory monitor detects (INTRO/EXTRO signal)
    → Affect triage classifies severity
    → IntentEngine evaluates ambiguity:
        Zero (reflex):     Log degradation, auto-tune threshold
        Bounded (affect):  Generate optimization intent — "reduce MCP overhead"
        Persistent (escalate): Propose technology rebinding — "replace MCP with X"
    → Optimization intent enters graph as new feature vector
```

The key insight: **a persistent escalation at the tolerance level means the binding decision itself should be revisited**. The ADR that made the choice becomes the target of a new design iteration. The methodology doesn't just maintain the system — it evolves the design.

### Examples of Tolerance-Driven Optimization

| Binding | Tolerance | Breach Signal | Generated Intent |
|---------|-----------|---------------|-----------------|
| MCP server (ADR-015) | Startup < 5s | Startup takes 12s after adding monitors | "Optimize sensory service startup: lazy-load monitors" |
| Claude headless (ADR-015) | Cost < $0.02/signal | Model price increase | "Evaluate local classifier for low-ambiguity triage" |
| Edge YAML (ADR-009) | Parse time < 500ms | 40+ edge configs | "Compile edge configs to binary format or merge related edges" |
| Context manifest (ADR-010) | Hash time < 2s | Context store grows to 500 files | "Implement incremental hashing or context pruning" |
| Event log (ADR-013) | Append latency < 50ms | events.jsonl exceeds 100MB | "Implement log rotation or archival" |
| Graph topology (ADR-009) | Edge count < 20 | Graph scaling (§2.5) adds edges | "Review edge granularity — merge or compose edges" |

### Relationship to Graph Scaling (§2.5)

Design tolerances connect directly to graph scaling. When the IntentEngine's escalation signal suggests the graph is too coarse, the new edges it generates have their own tolerances. If those edges consistently breach tolerances (too slow, too expensive, too complex), the scaling process receives negative feedback — the topology should be simplified, not grown.

This creates a **bidirectional pressure**:
- **Escalation pressure**: persistent ambiguity → graph needs more edges
- **Tolerance pressure** (this ADR): tolerance breaches → graph needs fewer/simpler edges

The equilibrium between these pressures is the optimal graph topology for the current ecosystem.

---

## Rationale

### Why Tolerances Belong in Design, Not Spec

Tolerances are inherently technology-specific:
- "MCP startup < 5s" is meaningless for a Gemini implementation using Cloud Functions
- "Claude headless cost < $0.02" is meaningless for a self-hosted LLM
- "YAML parse time < 500ms" is meaningless for a code-based registry

The spec says "the sensory system monitors" and "the IntentEngine evaluates ambiguity." Design tolerances fill in the WHAT with HOW MUCH — and HOW MUCH is always ecosystem-dependent.

### Why Tolerances Generate Intents (Not Just Alerts)

An alert is a notification. An intent is a first-class object in the asset graph — it carries REQ keys, spawns feature vectors, converges through edges, and produces auditable artifacts. By generating intents (not alerts), tolerance breaches enter the same pipeline as every other development activity. They are traceable, reviewable, and subject to the same convergence criteria.

### Why This Is Homeostatic

The design evaluates its own fitness. When ecosystem conditions change (new API pricing, better protocols, larger projects), the tolerances detect drift and generate corrective intents. The system doesn't wait for a human to notice degradation — it senses, classifies, and proposes action. The human approves or dismisses (review boundary, ADR-015), preserving the "no autonomous modification" invariant.

---

## Consequences

### Positive

- **Living design** — ADRs evolve from static records to monitored constraints
- **Proactive optimization** — tolerance breaches surface before users notice degradation
- **Principled technology evolution** — "replace X with Y" is an intent with traceability, not a Friday afternoon decision
- **Graph topology feedback** — tolerance pressure balances escalation pressure for optimal graph complexity

### Negative

- **Tolerance specification burden** — every ADR should declare tolerances, adding authoring overhead. Mitigated: tolerances are optional; start with the most performance-sensitive bindings.
- **Monitor proliferation** — each tolerance needs a sensory monitor. Mitigated: monitors can share infrastructure; many tolerances map to the same underlying metrics.
- **Threshold tuning** — initial tolerance values will be wrong. Mitigated: the IntentEngine's own affect mechanism adjusts urgency based on breach frequency; consistently-breached tolerances auto-escalate.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.5 (Sensory Systems), §4.6 (IntentEngine), §5.3 (Constraint Tolerances)
- [ADR-009](ADR-009-graph-topology-as-configuration.md) — Graph Topology as Configuration (tolerances on topology complexity)
- [ADR-010](ADR-010-spec-reproducibility.md) — Spec Reproducibility (tolerances on hash computation cost)
- [ADR-013](ADR-013-multi-agent-coordination.md) — Multi-Agent Coordination (tolerances on event log size and serialiser throughput)
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding (breach → ambiguity classification → optimization intent)
- [ADR-015](ADR-015-sensory-service-technology-binding.md) — Sensory Service Technology Binding (monitors that observe tolerance metrics)
