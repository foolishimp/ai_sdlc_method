# ADR-017: Functor-Based Execution Model — Deterministic / Probabilistic / Human Rendering

**Status**: Accepted
**Date**: 2026-02-22
**Deciders**: Methodology Author
**Requirements**: REQ-SUPV-001, REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003
**Extends**: ADR-008 (Universal Iterate Agent), ADR-014 (IntentEngine Binding)
**Resolves**: Actor Model Review (gates v3.0)

---

## Context

The active task gating v3.0 asks: **which IntentEngine flows become deterministic code-backed vs. agent-driven vs. human-driven?** (ACTIVE_TASKS.md, Key Questions 1–5).

ADR-014 established that the IntentEngine is realised through the iterate agent and edge configs — configuration-only, no new engine code. The spec (§4.6.2) defines three ambiguity regimes (zero, bounded, persistent) mapping to three processing phases (reflex, affect, conscious) and three evaluator types (deterministic, agent, human). ADR-016 established that design tolerances generate intents through the same pipeline.

The unresolved question: is the boundary between deterministic and probabilistic a **static design decision** (hardcoded per flow) or a **runtime parameter**? And if runtime, what controls it?

### The Insight

The three processing phases are not three different subsystems. They are **three renderings of the same objects**. Each functional unit in the system — evaluate, construct, classify, route, propose, sense — can be rendered as deterministic code, as a probabilistic agent, or as a human interaction. The choice of rendering is not fixed at design time; it is parameterised by:

1. **The current ambiguity level** — does this invocation have zero, bounded, or persistent ambiguity?
2. **The execution mode** — is the system running headless or interactive?
3. **The affect valence** — how aggressively should the system escalate between renderings?

This is a **functor** in the category-theoretic sense (ontology §V): a structure-preserving map from one category to another. The same object (same input type, same output type, same boundary) maps to different implementations that preserve the compositional structure.

---

## Decision

**Each functional unit in the IntentEngine has three renderings — deterministic (F_D), probabilistic (F_P), and human (F_H). The execution model is a functor composition: each unit starts in one category and escalates to the next via a natural transformation when ambiguity exceeds the current category's capacity. The starting category and escalation valence are runtime parameters, not static design choices.**

### The Three Categories

| Category | Symbol | Regime | Cost (T) | Speed | What it handles |
|----------|--------|--------|-----------|-------|----------------|
| **Deterministic** | F_D | Ambiguity = 0 | Cheap | Fast | Unambiguous observations — pass/fail, threshold check, rule match |
| **Probabilistic** | F_P | Ambiguity bounded | Moderate | Medium | Bounded disambiguation — gap analysis, coherence check, triage |
| **Human** | F_H | Ambiguity persistent | Expensive | Slow | Judgment — approval, spec modification, constraint resolution |

### The Rendering Table

Each functional unit maps to all three categories. The mapping preserves input/output types — the boundary (Markov blanket) is invariant across renderings:

| Functional Unit | F_D (deterministic) | F_P (probabilistic) | F_H (human) |
|----------------|--------------------|--------------------|-------------|
| **Evaluate** | pytest, coverage, schema validator, lint | LLM coherence/gap review, design alignment check | Human review, approval, judgment call |
| **Construct** | Template expansion, compiler, code generation from schema | LLM generates candidate from context + intent | Human writes artifact directly |
| **Classify** | Rule-based severity thresholds, regex pattern match | LLM classifies ambiguous signal, context-sensitive triage | Human triages manually |
| **Route** | Topological sort, priority queue, dependency resolution | LLM picks optimal next edge from heuristic context | Human chooses what to work on |
| **Propose** | Template-driven proposal from structured input | LLM drafts intent, diff, or spec modification | Human writes proposal from scratch |
| **Sense** | File watcher, cron, CVE poll, metric threshold | LLM interprets telemetry pattern, anomaly detection | Human notices something |
| **Emit** | Append to events.jsonl — **always deterministic** | — | — |
| **Decide** | — | — | Human reviews and approves — **always human** |

**Category-fixed units**: Emit is always F_D (it is a pure side effect — append structured data). Decide is always F_H (this is the review boundary invariant from ADR-015 / REQ-EVAL-003). All other units are **category-variable** — renderable in any category depending on ambiguity.

### Escalation as Natural Transformation

When a unit rendered in category C produces ambiguity that exceeds C's capacity, the **natural transformation η** re-renders the same unit in the next category:

```
η_D→P :  F_D(unit) produces ambiguity > 0        →  re-render as F_P(unit)
η_P→H :  F_P(unit) produces persistent ambiguity  →  re-render as F_H(unit)
```

The escalation preserves the unit's boundary — same input type, same output type. Only the implementation changes. This is the formal version of what §4.6.2 describes informally:

```
F_D(Evaluate) fails     →  η_D→P  →  F_P(Evaluate) tries    →  η_P→H  →  F_H(Evaluate) decides
  pytest says pass/fail       ↑        LLM says "gap found"       ↑        Human says "approved"
  but can't assess design     │        but can't resolve conflict  │
  coherence (ambiguity > 0)   │        (persistent ambiguity)      │
                               │                                    │
                          same boundary                        same boundary
                          same I/O types                       same I/O types
```

### The Starting Functor Determines the Mode

The execution mode is **which category the system starts in**:

**Headless mode (start F_D → escalate up):**
```
Direction: bottom-up — deterministic handles what it can, probabilistic handles the rest, human handles what's left

F_D(Route) → F_D(Construct) → F_D(Evaluate) → F_D(Emit)
                                    │
                              ambiguity > 0
                                    │
                              η_D→P fires
                                    ▼
                              F_P(Construct) → F_P(Evaluate) → F_D(Emit)
                                                    │
                                              persistent ambiguity
                                                    │
                                              η_P→H fires
                                                    ▼
                                              F_H(Decide) — surfaces to human
```

Maximum automation. The system runs autonomously until it **must** escalate. Well-constrained edges (high constraint density, §5.2) may never reach F_P. Only genuine ambiguity surfaces to the human.

**Interactive mode (start F_H → delegate down):**
```
Direction: top-down — human directs, probabilistic constructs, deterministic validates

F_H(Route) → human picks feature/edge
    │
    └──→ F_P(Construct) → F_D(Evaluate) → F_D(Emit)
                                │
                          ambiguity > 0
                                │
                          η_D→P fires
                                ▼
                          F_P(Evaluate) → results surface to F_H
```

Maximum control. The human directs everything, delegates construction to the agent, and deterministic tests validate. This is the current `/gen-iterate` flow — human invokes, agent constructs, tests evaluate.

**Autopilot mode (start F_D → valence-controlled escalation):**

The hybrid. Start deterministic, but the **affect valence** controls how aggressively η fires:

| Profile | Valence | Escalation behaviour |
|---------|---------|---------------------|
| **hotfix** | High (escalate aggressively) | F_D → η_D→P fires immediately on any nonzero → η_P→H fires quickly → human decides fast. Minimise autonomous iteration, maximise human attention. |
| **standard** | Medium (normal thresholds) | F_D → η_D→P after deterministic tests fail → F_P iterates up to `max_iterations` → η_P→H after `stuck_threshold`. Balanced automation and oversight. |
| **spike** | Low (suppress escalation) | F_D → F_P → iterate extensively before η_P→H fires. Explore the space. Tolerate ambiguity. Escalate only when truly stuck. |
| **poc** | Low | Similar to spike — optimise for exploration over convergence. |

The affect field in the feature vector (ADR-014) is the **control signal for the natural transformation**:

```yaml
# In feature vector state (from ADR-014)
affect:
  urgency: normal          # Controls η_P→H sensitivity
  source: profile          # What set the current valence
  escalation_count: 0      # Tracks how many times η has fired
  valence: medium          # Controls η_D→P sensitivity — NEW
```

The `valence` parameter is the threshold for the natural transformation. It determines how much ambiguity the current category tolerates before re-rendering in the next category.

### Configuration Binding

The functor composition is configured at three levels, matching the engine's three-layer architecture (§2.7):

| Layer | What it configures | Example |
|-------|-------------------|---------|
| **Engine** (Layer 1) | The natural transformation mechanism — how η_D→P and η_P→H fire | Escalation protocol: retry count, timeout, ambiguity threshold |
| **Graph Package** (Layer 2) | Default rendering per functional unit per edge | `code_unit_tests.evaluate: start_F_D` (tests are deterministic first), `intent_requirements.construct: start_F_P` (requirements need LLM) |
| **Project Binding** (Layer 3) | Mode override, valence override, per-edge rendering override | `mode: headless`, `valence: high`, `design_code.evaluate: start_F_H` (this project requires human design review) |

Edge configs (ADR-009) already encode this implicitly:

```yaml
# Existing edge config — now understood as functor assignment
edge:
  type: code_unit_tests
  evaluators:
    deterministic:           # ← F_D rendering of Evaluate
      - pytest_pass
      - coverage_threshold
    agent:                   # ← F_P rendering of Evaluate
      - code_coherence
      - req_tag_coverage
    human:                   # ← F_H rendering of Evaluate
      - design_approval
  convergence:
    max_iterations: 5        # ← η_P→H threshold
    stuck_threshold: 3       # ← urgency escalation trigger
```

The existing evaluator taxonomy in edge configs **already is** the functor rendering table. This ADR names the pattern and makes the execution mode (starting functor) and valence (escalation threshold) explicit configuration rather than implicit behaviour.

### Runtime Architecture

The functor model answers the active task's runtime architecture question (Key Question 4):

```
┌──────────────────────────────────────────────────────────────────┐
│  EXECUTION ENGINE (Layer 1)                                       │
│                                                                   │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐             │
│  │ F_D        │ η  │ F_P        │ η  │ F_H        │             │
│  │ Deterministic├──→│ Probabilistic├──→│ Human      │             │
│  │            │D→P │            │P→H │            │             │
│  │ • pytest   │    │ • Claude   │    │ • /review  │             │
│  │ • lint     │    │ • headless │    │ • approval │             │
│  │ • schema   │    │ • gap check│    │ • judgment │             │
│  │ • template │    │ • construct│    │ • spec mod │             │
│  │ • watcher  │    │ • triage   │    │ • direction│             │
│  └────────────┘    └────────────┘    └────────────┘             │
│        ↓                  ↓                  ↓                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  F_D(Emit) — always deterministic                        │    │
│  │  events.jsonl ← append(typed_event)                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  Starting functor: config.mode (headless | interactive | auto)   │
│  Valence: config.valence (high | medium | low) or affect.valence │
└──────────────────────────────────────────────────────────────────┘
```

**Process model**: Not an event loop or message passing system. The iterate agent already runs as a single-threaded sequence of tool calls within the Claude Code session. The functor model doesn't change the process model — it parameterises which implementation of each functional unit the iterate agent invokes at each step. The "engine" is the iterate agent (ADR-008) with the functor rendering as a dispatch table.

**Multi-agent coordination**: The serialiser (ADR-013) operates orthogonally to the functor model. Each agent runs its own functor composition. The serialiser coordinates **between** agents (claim protocol, inbox, event log). The functor controls **within** an agent (which rendering of each unit to invoke).

---

## Rationale

### Why This Answers the v3.0 Gate Questions

**Q1: Which flows should be deterministic code?**
Not a static answer. Each functional unit *starts* deterministic (F_D) where possible. The rendering table (above) enumerates the F_D implementation for each unit. If F_D can handle the invocation (ambiguity = 0), it does. No LLM involved.

**Q2: Which flows remain probabilistic?**
Same answer, inverted. F_P handles what F_D can't. The unit is the same; the rendering changes. The boundary is not "these flows are deterministic, those are probabilistic" — it is "this invocation's ambiguity determines which rendering fires."

**Q3: Where is the boundary?**
The natural transformation η. It fires when ambiguity exceeds the current category's capacity. The boundary moves per invocation, per edge, per profile. It is not a static line in the architecture.

**Q4: What is the runtime architecture?**
The iterate agent (ADR-008) with a functor dispatch table. No new event loop, no message passing system, no actor framework. The agent already sequences tool calls; the functor model parameterises which tool to call.

**Q5: How do tolerances wire to monitors?**
Tolerances (ADR-016) are F_D(Sense) invocations — deterministic threshold checks. When a threshold is breached, ambiguity > 0, and η_D→P fires: the breach enters the probabilistic triage (F_P(Classify)). If triage can resolve it (generate optimisation intent), done. If persistent, η_P→H fires: human reviews the proposed technology rebinding.

### Why a Functor (Not Static Assignment)

1. **The same edge needs different renderings in different contexts.** A `code_unit_tests` edge in a hotfix profile should escalate to human immediately on any test ambiguity. The same edge in a spike profile should let the agent iterate extensively. Static assignment can't express this — the rendering must be parameterised by affect.

2. **The direction of traversal matters.** Headless starts F_D and escalates up. Interactive starts F_H and delegates down. Both use the same functional units, the same event types, the same boundaries. Only the starting functor differs.

3. **The existing config already encodes it.** Edge YAML already separates `deterministic`, `agent`, and `human` evaluators. Profile configs already set `max_iterations` and urgency. The functor model names what's already there and adds the missing parameter: execution mode (starting functor) and valence (escalation sensitivity).

### Why Not New Engine Code (Yet)

This ADR extends ADR-014's "configuration-only" decision. The functor dispatch is a conceptual model that maps onto the iterate agent's existing tool-call sequence. The agent reads edge config, runs F_D evaluators first, then F_P if needed, then escalates to F_H. This is already what happens.

What's new: making `mode` and `valence` explicit config parameters, and understanding that the three evaluator sections in edge YAML are not "three different things to check" but "three renderings of the same check at different ambiguity levels." This understanding changes how we tune and compose edge configs without requiring new runtime code.

When the engine is built as executable code (v3.0+), the functor dispatch becomes a literal dispatch table: `render(unit, category) → implementation`. But the current iterate-agent-as-interpreter model handles it through the existing config-driven evaluator sequence.

### Ontology Grounding

The functor model maps to the ontology's formal programme:

| Ontology concept | Functor model instantiation |
|-----------------|---------------------------|
| **#58–64 Category theory / functors** | F_D, F_P, F_H are three categories. Each functional unit is an object. The functor maps objects between categories preserving composition (input/output types invariant). |
| **#45 Two compute regimes** | F_D = deterministic compute. F_P = probabilistic compute. F_H extends to human compute. The functor bridges all three. |
| **#49 Teleodynamic self-maintenance** | The natural transformation η is the self-repair mechanism. When one rendering fails (ambiguity too high), the system re-renders — it doesn't break, it adapts. |
| **#23 Scale-dependent observation** | The same unit at different scales may start in different categories. Iteration-level Evaluate starts F_D (tests). Feature-level Evaluate may start F_P (cross-edge coherence). Spec-level Evaluate starts F_H (human judgment). |

---

## Consequences

### Positive

- **Answers the v3.0 gate** — the boundary between deterministic and probabilistic is not a line to draw but a threshold to configure. The five key questions have principled answers.
- **No new code required** — the functor model is a design interpretation of existing config structures. Edge YAML evaluator sections, profiles, convergence thresholds already encode functor assignments.
- **Unified execution model** — headless, interactive, and autopilot are not three different architectures. They are three starting conditions for the same functor composition.
- **Composable** — valence can be tuned per edge, per profile, per project. A single project can have hotfix-valence edges (design review) and spike-valence edges (exploratory code).
- **Observable** — the affect field in the feature vector already records urgency and escalation count. Adding `valence` makes the functor control signal explicit and visible in `/gen-status`.
- **Future-proof** — when the engine becomes executable code (post v3.0), the functor dispatch becomes a literal dispatch table. The conceptual model maps directly to implementation.

### Negative

- **Conceptual density** — functor language adds abstraction overhead for developers unfamiliar with category theory. Mitigated: the rendering table is a concrete lookup; the category theory is explanatory, not operational.
- **Valence tuning** — initial valence values per profile will need calibration through use. Mitigated: sensible defaults (hotfix=high, standard=medium, spike=low) and the tolerance mechanism (ADR-016) auto-adjusts through feedback.
- **Testing the natural transformation** — escalation paths (η_D→P, η_P→H) need integration tests that verify re-rendering preserves boundaries. Added test burden.

---

## Impact on Active Tasks

This ADR resolves the "Actor Model Review and Deterministic Code Backing" active task:

| Key Question | Answer | ADR Section |
|-------------|--------|-------------|
| 1. Which flows are deterministic? | All units start F_D where ambiguity = 0 | Rendering Table |
| 2. Which flows are probabilistic? | Same units, rendered F_P when ambiguity > 0 | Rendering Table |
| 3. Where is the boundary? | The natural transformation η — a runtime threshold, not a static line | Escalation as Natural Transformation |
| 4. What is the runtime architecture? | Iterate agent + functor dispatch table | Runtime Architecture |
| 5. How do tolerances wire to monitors? | F_D(Sense) → η_D→P → F_P(Classify) → intent | Rationale, Q5 |

**Next steps post-ADR**:
1. Add `mode` and `valence` to project binding schema (`project_constraints.yml`)
2. Add `valence` field to feature vector affect schema
3. Annotate existing edge configs with starting-functor comments for clarity
4. Design integration tests for escalation paths (η_D→P and η_P→H)

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §2.7 (Three Layers), §4.1 (Evaluator Types), §4.3 (Three Processing Phases), §4.6 (IntentEngine), §4.6.2 (Ambiguity Classification), §4.6.6 (Consciousness as Relative), §11.1 (Hilbert Space — two compute regimes)
- [Constraint-Emergence Ontology](https://github.com/foolishimp/constraint_emergence_ontology) §V (Category Theory / Functors), #45 (Two Compute Regimes), #49 (Teleodynamic Self-Maintenance)
- [ADR-008](ADR-008-universal-iterate-agent.md) — Universal Iterate Agent (the execution substrate for all functor renderings)
- [ADR-009](ADR-009-graph-topology-as-configuration.md) — Graph Topology as Configuration (edge configs already encode functor assignments in evaluator sections)
- [ADR-013](ADR-013-multi-agent-coordination.md) — Multi-Agent Coordination (orthogonal to functor model — coordinates between agents, not within)
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding (this ADR extends the configuration-only decision with explicit mode and valence parameters)
- [ADR-015](ADR-015-sensory-service-technology-binding.md) — Sensory Service Technology Binding (review boundary = F_H(Decide) is category-fixed)
- [ADR-016](ADR-016-design-tolerances-as-optimization-triggers.md) — Design Tolerances (tolerance monitoring = F_D(Sense) with escalation via η)

---

## Requirements Addressed

- **REQ-SUPV-001**: IntentEngine interface — the functor model formalises how IntentEngine selects between deterministic, probabilistic, and human processing
- **REQ-EVAL-001**: Deterministic evaluator — F_D rendering of Evaluate, always attempted first
- **REQ-EVAL-002**: Agent evaluator — F_P rendering of Evaluate, invoked via η_D→P when ambiguity > 0
- **REQ-EVAL-003**: Human accountability — F_H(Decide) is category-fixed; the review boundary invariant is preserved structurally
