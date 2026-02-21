# AI SDLC — Project Genesis: Intent

**Intent ID**: INT-AISDLC-001
**Date**: 2024-01-01 (originated), 2026-02-21 (v2.6 revision)
**Priority**: Critical
**Status**: v2.7 — Asset Graph Model complete, two-command UX layer, consciousness loop, processing phases, sensory systems, implementation Phase 1a

---

## The Problem

AI coding assistants are powerful but chaotic:

1. **No methodology** — ad-hoc usage, no traceability from intent to runtime
2. **Lost context** — no persistent memory of project decisions across sessions
3. **No quality enforcement** — TDD skipped, debt accumulates, no gates
4. **Enterprise gap** — can't prove AI-generated code meets specs (BCBS 239, SOC 2)
5. **No shared framework** — every team reinvents their own prompts

---

## What We Want

An AI SDLC methodology grounded in the [Constraint-Emergence Ontology](https://github.com/foolishimp/constraint_emergence_ontology), where:

- Software development is an **asset graph** — typed artifacts connected by admissible transitions
- A **universal iteration function** is the only operation — parameterised per edge
- **Feature vectors** (REQ keys) trace trajectories through the graph from intent to runtime
- **{Human, Agent, Tests}** evaluators compose per edge to define convergence
- **Context[]** (ADRs, data models, templates, policy) is the constraint surface preventing degeneracy
- The **full lifecycle** closes: CI/CD → telemetry → homeostasis → new intent → back into the graph

Four primitives. One operation. The rest is parameterisation.

---

## Business Value

**Developer Productivity**: Structured AI assistance, persistent context, no tool-switching
**Quality Assurance**: TDD/BDD as edge evaluators, feature vector traceability, constraint density prevents hallucination
**Enterprise Enablement**: Audit trails via feature vector trajectories, deterministic evaluators for compliance
**Cost Reduction**: Auto-generated documentation, standardised methodology, no vendor lock-in

---

## Key Documents

| Document | Purpose |
|----------|---------|
| [AI_SDLC_ASSET_GRAPH_MODEL.md](AI_SDLC_ASSET_GRAPH_MODEL.md) | Canonical methodology — the 4 primitives, ontology grounding |
| [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](AISDLC_IMPLEMENTATION_REQUIREMENTS.md) | 49 implementation requirements derived from the model |
| [Constraint-Emergence Ontology](https://github.com/foolishimp/constraint_emergence_ontology) | Parent theory |

---

## Current Status

**Asset Graph Model (v2.7)**: Complete — two-command UX, consciousness loop, processing phases, sensory systems, protocol hooks
**Implementation Requirements (v3.5)**: Complete — 49 requirements, 10 critical
**Tooling (Claude Code plugins)**: Phase 1a — iterate agent, 10 commands, 2 hooks, configurable graph
**Examples**: [ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples) — CDME dogfood (5/5 edges converged)

---

## History

- **v1.0** (2024): Key Principles + TDD workflow (ai_init)
- **v1.2** (2025-11): 7-stage pipeline model, 47 implementation requirements, ~4,400 lines across 4 methodology docs
- **v2.0** (2026-02): Asset Graph Model — 4 primitives, 1 operation, ontology-grounded. Prior version tagged `v2.0`.
- **v2.1** (2026-02): Revised framing — composite vectors, zoomable graph, scale-dependent assurance, 3-param iterate(). ~570-line canonical doc replaces 4,400 lines. 32 implementation requirements replace 47.
- **v2.5** (2026-02): Consciousness loop, protocol enforcement hooks, event sourcing, signal classification. 39 implementation requirements.
- **v2.6** (2026-02): Three processing phases (reflex/affect/conscious), two sensory systems (interoception/exteroception), affect triage pipeline, context sources. 44 implementation requirements.
- **v2.7** (2026-02): Two-command UX layer (Start + Status), §11 User Experience requirements (state-driven routing, progressive disclosure, observability, feature/edge selection, recovery). 49 implementation requirements.
