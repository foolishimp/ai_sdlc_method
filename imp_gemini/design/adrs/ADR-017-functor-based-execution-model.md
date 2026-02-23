# ADR-017: Functor-Based Execution Model — Deterministic / Probabilistic / Human Rendering

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-SUPV-001, REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003
**Extends**: ADR-008 (Universal Iterate Agent), ADR-014 (IntentEngine Binding)

---

## Context

How do we decide which flows are deterministic vs probabilistic vs human? ADR-014 established that the IntentEngine is realised through the iterate agent and edge configs.

The execution model needs a principled way to select the implementation (rendering) for each functional unit.

---

## Decision

**Each functional unit in the IntentEngine has three renderings — deterministic (F_D), probabilistic (F_P), and human (F_H). The execution model is a functor composition: each unit starts in one category and escalates to the next via a natural transformation when ambiguity exceeds the current category's capacity.**

### The Three Categories

| Category | Symbol | Regime | Cost | Speed |
|----------|--------|--------|-----------|-------|
| **Deterministic** | F_D | Ambiguity = 0 | Cheap | Fast |
| **Probabilistic** | F_P | Ambiguity bounded | Moderate | Medium |
| **Human** | F_H | Ambiguity persistent | Expensive | Slow |

### The Rendering Table

| Functional Unit | F_D (deterministic) | F_P (probabilistic) | F_H (human) |
|----------------|--------------------|--------------------|-------------|
| **Evaluate** | pytest, ruff, mypy | LLM coherence check | Human review |
| **Construct** | Template expansion | LLM candidate generation | Human writes artifact |
| **Classify** | Rule-based triage | LLM signal classification | Human manual triage |
| **Route** | Topological routing | LLM next-edge choice | Human chooses task |
| **Propose** | Template-driven | LLM drafts intent/diff | Human writes proposal |
| **Sense** | File watcher, cron | LLM pattern detection | Human notices |
| **Emit** | Event log append | — | — |
| **Decide** | — | — | Human approval |

### Escalation as Natural Transformation

When a unit rendered in category C produces ambiguity that exceeds C's capacity, it is re-rendered in the next category:

```
η_D→P :  F_D(unit) produces ambiguity > 0        →  re-render as F_P(unit)
η_P→H :  F_P(unit) produces persistent ambiguity  →  re-render as F_H(unit)
```

### Starting Functor and Mode

- **Headless mode:** Start F_D → escalate up.
- **Interactive mode:** Start F_H → delegate down.
- **Autopilot mode:** Start F_D → valence-controlled escalation.

---

## Rationale

The functor model allows the same edge to be rendered differently depending on context (profile, affect). It unifies headless and interactive execution into a single conceptual framework.

---

## Consequences

### Positive

- **Principled boundary selection** — not a static line but a runtime threshold.
- **Unified execution model** — headless and interactive share the same logic.
- **Scalable** — can be tuned per project and per feature via valence.

### Negative

- **Conceptual density** — requires understanding the IntentEngine model.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../.ai-workspace/spec/AI_SDLC_ASSET_GRAPH_MODEL.md)
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding
