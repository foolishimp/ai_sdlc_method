# ADR-S-019: Markov Blankets and Active Inference as Formal Theoretical Grounding

**Status**: Accepted
**Date**: 2026-03-07
**Deciders**: Methodology Author
**Requirements**: REQ-INTENT-001, REQ-SUPV-001, REQ-SUPV-002
**Extends**: ADR-S-001 (Specification Document Hierarchy), ADR-S-008 (Sensory-Triage-Intent Pipeline)
**References**: Friston (2010, 2013), Friston et al. (2022), Constraint-Emergence Ontology §VI

---

## Context

The Asset Graph Model's four primitives (Graph, Iterate, Evaluators, Spec+Context) were initially motivated by software engineering practice. The model worked — but without formal theoretical grounding it remained engineering intuition rather than a principled formal system.

Three independent intellectual threads converged at a point where their unification is both natural and load-bearing:

### Thread 1: Friston's Markov Blankets

Karl Friston's active inference framework (2010, 2013) defines a **Markov blanket** as the boundary of a self-organising system: a set of states that conditionally separate internal states from external states. Given the blanket, internal and external states become conditionally independent.

Friston observes that cells have Markov blankets — and that this is the formal definition of a living boundary, not merely a biological metaphor. Any system with an internal-external boundary that is maintained by the system itself satisfies the Markov blanket condition.

Four state classes in the active inference framework:
- **Internal states** (μ) — the system's own belief states, not directly observable from outside
- **External states** (η) — the environment, not directly controllable from inside
- **Sensory states** (s) — mediate internal←external: information flows inward
- **Active states** (a) — mediate internal→external: action flows outward

### Thread 2: The Asset Graph Model's Existing Structure

The Asset Graph Model already has these four structures:
- **Internal**: `specification/`, `events.jsonl`, feature vectors — the project's belief state
- **External**: running system, users, ecosystem changes, telemetry — the environment
- **Sensory**: interoceptive monitors (test health, coverage, feature staleness) and exteroceptive monitors (CVE feeds, API drift, user feedback) — §4.5
- **Active**: CI/CD, deployment pipelines — the methodology's actions on the environment

The workspace IS the Markov blanket of the project. This was implicit — it can now be made explicit.

### Thread 3: Active Inference as Discrete-Time Iterate()

Active inference is the process by which a system with a Markov blanket reduces its **free energy** (a bound on surprise — how unexpected the sensory states are, given the system's generative model).

The `iterate()` function is precisely discrete-time active inference:

| Active Inference | iterate() |
|-----------------|-----------|
| Belief state | Current asset (candidate) |
| Generative model | Spec + Context[] — what the world should look like |
| Free energy | Delta between asset and spec — failing evaluator count |
| Action | Construction step — next candidate produced |
| Minimisation | Convergence — delta → 0 |

The three evaluator types (F_D, F_P, F_H) are not arbitrary — they are the **exhaustive taxonomy of prediction error under irreducible uncertainty**:
- F_D (deterministic) — zero ambiguity: test passes or fails, no judgment needed
- F_P (agent) — bounded ambiguity: prediction error classifiable by inference
- F_H (human) — persistent ambiguity: prediction error requires judgment that exceeds current inference capacity

The escalation chain η: F_D→F_P→F_H is the system's response to increasing surprise — when the current evaluator type cannot reduce free energy, the next level is recruited.

### Thread 4: Nested Blankets and Evolutionary Stages

Markov blankets nest. A cell has a blanket; a tissue is cells-with-blankets forming a higher-order blanket; an organism is tissues-with-blankets. Each level is real at its own scale; none is more fundamental.

In the methodology:
- **Methodology level**: the formal system's blanket — axioms as internal states, instantiations as active states
- **Organisation level**: org ADRs and policy as internal states, the methodology as sensory input
- **Project level**: specification and events as internal states, the running system as external
- **Feature level**: feature vector trajectory as internal states, the build graph as external
- **Edge level**: candidate asset as internal state, evaluators as sensory input

This is the basis of the lineage DAG (**ADR-027**, implementation): live lineage connections ARE sensory couplings between Markov blankets at adjacent scales.

**Evolutionary stages** (where the methodology currently sits and where it is going):
- **Prokaryote** (current): single-cell, working blanket, no bounded nucleus — the project workspace IS the cell.
- **Eukaryote** (next): bounded sub-structures (e.g. design tenants) within the workspace — internal specialisation.
- **Multicellular** (future): projects coupled through live lineage — the first primitive multicellular structure; tournament pattern (ADR-S-018) is the first division of labour.

---

## Decision

### 1. Formally Ground the Spec in Active Inference and Markov Blanket Theory

The specification explicitly adopts the Friston active inference framework as the **formal theoretical foundation** of the methodology. This is not a metaphor or analogy — it is a structural identity:

- The Markov blanket definition IS the definition of a valid project workspace boundary.
- iterate() IS discrete-time active inference (free energy minimisation).
- The three evaluator types IS the exhaustive taxonomy of prediction error under irreducible uncertainty.
- Convergence IS free energy minimisation to a stable prior (the spec).

These identities are stated explicitly in the specification (§2.10, §3.3) and referenced from relevant sections.

### 2. The Workspace is the Markov Blanket — Not a File Container

The `.ai-workspace/` directory is not a cache directory. It is the **Markov blanket** of the project: the boundary that conditionally separates the project's internal belief states (spec, events, feature vectors) from the external environment (running system, users, ecosystem).

Consequence: the workspace must be observable. An unobservable workspace = a Markov blanket with no sensory states = a system that cannot perform active inference = a system that cannot converge. This is the formal basis for the observability-is-constitutive invariant (§XV of the bootloader).

### 3. Nested Blankets Define the Context Hierarchy

The lineage DAG (**ADR-027**, implementation) is the instantiation of nested Markov blankets in the methodology:
- Live lineage sources = sensory couplings between blankets at adjacent levels.
- Static lineage sources = information transferred at blanket formation (cell division / project inception).
- `load_context_hierarchy()` = the merge operation that collapses the DAG into an effective constraint surface.

The context hierarchy is not a configuration pattern — it is the formal expression of nested Markov blankets in the SDLC domain.

### 4. Evolutionary Stage Model as Architecture Roadmap

The prokaryote/eukaryote/multicellular classification is adopted as the **architecture roadmap** for the methodology's own development:

| Stage | Feature |
|-------|---------|
| Prokaryote | Working Markov blanket — workspace, events, monitors |
| Eukaryote | Bounded nucleus — internal specialisation (tenants) |
| Multicellular | Live lineage coupling between projects |

This framing supersedes vague "future work" descriptions — each stage has a formal biological analogue that predicts what must be implemented and why.

### 5. References Added to Specification

The specification now explicitly cites:
- Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127–138.
- Friston, K. (2013). Life as we know it. *Journal of the Royal Society Interface*, 10(86), 20130475.
- Friston, K. et al. (2022). Active inference: the free energy principle in mind, brain, and behavior. MIT Press.
- Constraint-Emergence Ontology (CEO) §VI — multi-domain mapping table

---

## Consequences

### Positive

- **Formal foundation**: The methodology is no longer engineering intuition — it is a principled formal system with a well-understood mathematical foundation (free energy minimisation)
- **Evaluator taxonomy justified**: The three evaluator types are no longer "three options we chose" — they are the exhaustive taxonomy of prediction error under irreducible uncertainty, provably complete
- **Workspace semantics clarified**: The workspace is the Markov blanket, not a file store — this has architectural consequences (observability-is-constitutive is a theorem, not a guideline)
- **Architecture roadmap**: Prokaryote→Eukaryote→Multicellular gives a formal trajectory for the methodology's own development
- **Lineage DAG justified**: Context hierarchy is nested Markov blankets — live/static distinction maps to sensory coupling vs. information transfer at formation

### Negative

- **Vocabulary overhead**: Readers unfamiliar with active inference must learn new terminology. Mitigated by the table in §3.3 mapping active inference terms to methodology terms.
- **Theoretical weight**: The methodology is now grounded in neuroscience literature, which may be unfamiliar to software engineers. This is intentional — the grounding is correct; the unfamiliarity is the reader's prior, not the methodology's fault.

### Neutral

- The Markov blanket formalisation does not change any existing implementation — it makes implicit structure explicit
- ADR-027 (lineage and context inheritance) is reframed as the implementation of nested Markov blankets — its content is unchanged, its motivation is now formally grounded

---

## References

- §2.10: Markov Blankets — Four State Classes
- §3.3: Active Inference — The Deep Grounding of iterate()
- §4.5: Two Sensory Systems (Interoception and Exteroception) — sensory states in the blanket
- ADR-027: Project Lineage and Context Inheritance — nested blankets in implementation
- Friston, K. (2010). The free-energy principle.
- Friston, K. (2013). Life as we know it.
- Friston, K. et al. (2022). Active inference.
- Constraint-Emergence Ontology §VI Multi-Domain Mapping Table
