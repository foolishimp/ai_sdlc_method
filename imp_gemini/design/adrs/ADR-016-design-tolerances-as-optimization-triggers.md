# ADR-016: Design Tolerances as Optimization Triggers

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-SUPV-002, REQ-SENSE-001, REQ-SENSE-002
**Extends**: ADR-014 (IntentEngine Binding), ADR-015 (Sensory Service Technology Binding)

---

## Context

ADR-014 and ADR-015 capture technology bindings. These bindings imply tolerances. Every tolerance is a threshold the sensory system can monitor. Every breach is an optimization intent waiting to be raised.

---

## Decision

**Design documents (ADRs, design docs) should capture technology-specific tolerances alongside binding decisions. These tolerances are monitored by the sensory system (ADR-015) and breaches generate optimization intents via the IntentEngine (ADR-014).**

### Tolerance Structure

Each technology binding can declare tolerances in its configuration:

```yaml
# Example: design_tolerances.yml or within project_constraints.yml
tolerances:
  gemini_api:
    binding: ADR-001
    monitors:
      - metric: p99_latency
        threshold: 30s
        direction: below
      - metric: error_rate
        threshold: 0.05
        direction: below
  event_log:
    binding: ADR-013
    monitors:
      - metric: log_size
        threshold: 100MB
        direction: below
```

### Breach → Intent Pipeline

When a tolerance is breached, the standard IntentEngine pipeline fires:

```
Tolerance breached
    → Sensory monitor detects (signal event)
    → Affect triage classifies severity
    → IntentEngine evaluates ambiguity:
        Zero (reflex):     Log degradation
        Bounded (affect):  Generate optimization intent
        Persistent (escalate): Propose technology rebinding
    → Optimization intent enters graph as new feature vector
```

---

## Rationale

### Why Tolerances Belong in Design

Tolerances are technology-specific. Specifying them in the design layer (ADRs/Configs) allows the system to evaluate its own fitness against concrete thresholds.

---

## Consequences

### Positive

- **Living design** — ADRs evolve from static records to monitored constraints.
- **Proactive optimization** — breaches surface before users notice degradation.
- **Homeostatic** — the system evaluates its own performance.

### Negative

- **Tolerance specification burden** — added authoring overhead.
- **Monitor proliferation** — each tolerance needs a monitor.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../.ai-workspace/spec/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.5 (Sensory Systems)
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding
- [ADR-015](ADR-015-sensory-service-technology-binding.md) — Sensory Service Technology Binding
