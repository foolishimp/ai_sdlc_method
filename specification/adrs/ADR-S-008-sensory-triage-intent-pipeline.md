# ADR-S-008: The Sensory-Triage-Intent Pipeline (Consciousness Loop)

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-02
**Revised**: 2026-03-14 (adds Stage 3 requires_spec_change branch — ADR-S-027 Resolution 2)
**Scope**: Methodology observability — `core/AI_SDLC_ASSET_GRAPH_MODEL.md` §7.3, `requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` §8, §13

---

## Context

The formal system (v2.6) was a **reflexive system**: it responded to human-authored intents by traversing the graph. But it lacked a formal mechanism for **self-initiated work** — it could not "discover" a gap and decide to fix it without external instruction.

Gaps in the reflexive model:
1. **Dormant Dysfunction**: A test failure or a build break could persist indefinitely if no human ran the command.
2. **Ecosystem Decay**: A security vulnerability in a dependency would remain unaddressed until the next scheduled human review.
3. **Implicit Triage**: Decisions about which signals were "important" were made informally by humans or hard-coded into specific tools.
4. **Disconnected Observation**: Telemetry was collected but not formally fed back as a driver of the iteration engine.

---

## Decision

### Formalise the Sensory-Triage-Intent Pipeline

The methodology becomes a **conscious system** by implementing a three-stage pipeline that runs independently of (and concurrent with) feature iteration.

#### Stage 1: Continuous Sensing (Interoception + Exteroception)

The system maintains continuous awareness through two sensory subsystems:
- **Interoception**: Self-sensing (test health, event freshness, vector stalls, build status, spec/code drift).
- **Exteroception**: Environment-sensing (dependency updates, CVE feeds, runtime telemetry, user feedback).

Every sensor emits a structured signal event (`interoceptive_signal` or `exteroceptive_signal`) to the canonical log.

#### Stage 2: Affect Triage (Valence and Routing)

Signals are triaged by an **Affect Engine** that assigns a **valence vector** (severity, urgency, priority) to each signal.
- **Zero Ambiguity**: Deterministic threshold breach (e.g., build failed) → **Reflex** (immediate action/log).
- **Non-zero, Bounded Ambiguity**: Probabilistic classification needed (e.g., "is this CVE relevant to us?") → **Agent Triage**.
- **Persistent Ambiguity**: Escalation required → **Human Gate**.

The output of triage is either a `reflex.log` entry or an escalation to the next stage.

#### Stage 3: Intent Generation (Conscious Review)

Escalated signals are reviewed at the "conscious" scale. This stage:
1. Computes the **delta** between observed state and specification.
2. Emits an **intent_raised** event (INT-*) if the delta exceeds the threshold.
3. Spawns a new **feature vector** (Feature, Discovery, Spike, or Hotfix) to address the intent.

### Implementation Invariants

1. **No Silent Failure**: If sensing fails (meta-monitoring), a reflex signal is emitted.
2. **Draft-Only Autonomy**: Homeostatic responses (fixing the gap) are generated as **draft proposals** only. No autonomous modification of production assets without human approval.
3. **Event-Sourced Provost**: The triage decision and intent generation are recorded as immutable events with a full causal chain (trace back to the sensory signal).

### Stage 3 Amendment: requires_spec_change Branch

Every `intent_raised` event MUST carry a `requires_spec_change: true | false` field. This field determines the routing out of Stage 3:

```
intent_raised
  │
  ├── requires_spec_change: false ──→ DISPATCHABLE
  │                                   composition_dispatched event emitted
  │                                   no feature_proposal required
  │                                   no human gate required
  │                                   (implementation resolves macro from registry)
  │
  └── requires_spec_change: true  ──→ PROMOTION REQUIRED
                                      feature_proposal event emitted (ADR-S-010)
                                      enters Draft Features Queue
                                      F_H gate required before any work begins
```

**Classification rule**:

| Delta type | requires_spec_change |
|-----------|---------------------|
| Gap in existing spec coverage (code, tests, telemetry missing for a defined REQ key) | false |
| New capability not represented in spec (new REQ key, new feature, new requirement) | true |
| Ecosystem change requiring spec response (new CVE, breaking API change) | true if spec must change; false if implementation can adapt within existing spec |

**Invariant**: An `intent_raised` event with `requires_spec_change: true` MUST NOT result in `composition_dispatched` without an intervening `spec_modified` event that references its `feature_proposal`.

---

## Consequences

**Positive:**
- **Homeostasis**: The system maintains itself toward the specification without waiting for human instruction.
- **Observability**: Every gap, signal, and triage decision is auditable in the event log.
- **Proactive Security**: Ecosystem changes (CVEs) are automatically triaged and turned into intents.

**Negative / Trade-offs:**
- **Signal Noise**: Requires careful tuning of triage rules and agent prompts to prevent "intent storms."
- **Computational Cost**: Continuous sensing and agent triage increase LLM/compute usage.

---

## Alternatives Considered

**Poll-on-demand**: Run sensory checks only when a human triggers them (e.g., `/gen-status --health`). What the original system did. Rejected — gaps that aren't observed aren't fixed. A build failure that no human checks is invisible to the methodology. Without continuous sensing, the system can only respond; it cannot self-maintain.

**Single-stage pipeline (sense → intent, no triage)**: Skip affect triage; every signal becomes an intent directly. Rejected — produces intent storms. A flapping test generates a new feature vector on every failure. The triage stage is the gate that converts noise into signal. Without it, the homeostatic loop is unstable.

**Human-curated triage only**: Humans decide which signals become intents. Rejected for routine signals (build failures, dependency updates) — requires continuous human attention that defeats the purpose of automation. The hybrid model (deterministic reflex for zero-ambiguity signals, agent triage for bounded ambiguity, human gate for persistent ambiguity) gives humans oversight without burdening them with classification work that is automatable.

**Separate observability system**: Use an external tool (Datadog, PagerDuty) for sensing and triage. Considered. The formal system integrates sensing as a first-class primitive (§4.5) because external tools cannot emit structured `intent_raised` events with causal chains traceable to spec REQ keys. External observability remains valuable for runtime monitoring; it is complementary, not a replacement for the methodology's own feedback loop.

---

## References

- [core/AI_SDLC_ASSET_GRAPH_MODEL.md](../core/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.3, §4.5, §4.6, §7.3
- [requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) §8 (REQ-SENSE-*), §13 (REQ-SUPV-*)
- [ADR-S-004](ADR-S-004-derivation-constraint.md) — intent derives from delta between observed state and spec
