# CLAUDE.md - ai_sdlc_method Project Guide

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**ai_sdlc_method** defines a formal system for AI-augmented software development — the **Asset Graph Model** (v2.6).

### The Model

4 primitives, 1 operation:

| Primitive | What it is |
|-----------|-----------|
| **Graph** | Topology of typed assets with admissible transitions (zoomable) |
| **Iterate** | `iterate(Asset, Context[], Evaluators) → Asset'` — the only operation |
| **Evaluators** | Convergence test — {Human, Agent, Deterministic Tests} |
| **Spec + Context** | Constraint surface — what bounds construction |

The graph is not universal. The SDLC graph is one domain-specific instantiation. The four primitives are universal; the graph is parameterised.

### Bootstrap Graph (typical dev SDLC)

```
1. Intent
2. Spec (tech-agnostic — WHAT the system does)
3. Design (tech-bound — HOW architecturally, ADRs, ecosystem binding)
4. Code ↔ Unit Tests (TDD co-evolution)
5. UAT Tests
6. CI/CD
7. Telemetry / Observer → feedback → new Intent
```

### Feature Lineage

REQ keys thread from spec to runtime — in the code, in the telemetry:

```
Spec:       REQ-F-AUTH-001 defined
Design:     Implements: REQ-F-AUTH-001
Code:       # Implements: REQ-F-AUTH-001
Tests:      # Validates: REQ-F-AUTH-001
Telemetry:  logger.info("login", req="REQ-F-AUTH-001", latency_ms=42)
```

Feature views are generated at every stage by grepping REQ keys across artifacts.

---

## Project Structure

```
ai_sdlc_method/
├── docs/
│   ├── specification/                     # SPEC (tech-agnostic)
│   │   ├── INTENT.md                      #   Business intent
│   │   ├── AI_SDLC_ASSET_GRAPH_MODEL.md   #   Formal system (4 primitives)
│   │   ├── PROJECTIONS_AND_INVARIANTS.md   #   Projections, vector types
│   │   ├── AISDLC_IMPLEMENTATION_REQUIREMENTS.md  # 44 implementation reqs
│   │   ├── FEATURE_VECTORS.md             #   Feature decomposition
│   │   └── presentations/*.pdf            #   PDF versions (via md2pdf)
│   └── design/claude_aisdlc/              # DESIGN (Claude Code binding)
│       ├── AISDLC_V2_DESIGN.md            #   Implementation design
│       └── adrs/
│           ├── ADR-008-universal-iterate-agent.md
│           ├── ADR-009-graph-topology-as-configuration.md
│           └── ADR-010-spec-reproducibility.md
├── claude-code/.../v2/                    # IMPLEMENTATION (Claude Code)
│   ├── agents/aisdlc-iterate.md           #   The ONE agent
│   ├── commands/ (9 commands)             #   /aisdlc-* slash commands
│   └── config/
│       ├── graph_topology.yml             #   Default SDLC graph
│       ├── evaluator_defaults.yml         #   Evaluator types
│       ├── edge_params/ (9 configs)       #   Per-edge parameterisations
│       ├── project_constraints_template.yml
│       └── feature_vector_template.yml
├── .ai-workspace/tasks/                   # Task tracking
│   ├── active/ACTIVE_TASKS.md             #   Current work
│   └── finished/                          #   Completed task docs
├── CLAUDE.md                              # This file
└── README.md                              # Project overview
```

---

## Key Documents

| Document | Path | What it covers |
|----------|------|---------------|
| Intent | docs/specification/INTENT.md | Business motivation |
| Asset Graph Model | docs/specification/AI_SDLC_ASSET_GRAPH_MODEL.md | Formal system, Hilbert space |
| Projections | docs/specification/PROJECTIONS_AND_INVARIANTS.md | Projections, vector types, spawning |
| Implementation Reqs | docs/specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md | 32 platform-agnostic reqs |
| Feature Vectors | docs/specification/FEATURE_VECTORS.md | Feature decomposition |
| Design | docs/design/claude_aisdlc/AISDLC_V2_DESIGN.md | Claude Code implementation |
| Iterate Agent | claude-code/.../v2/agents/aisdlc-iterate.md | The universal agent |
| Graph Topology | claude-code/.../v2/config/graph_topology.yml | 10 asset types, 10 transitions |

---

## Current Status

**Version**: 2.1 (Asset Graph Model)

| Stage | Status |
|-------|--------|
| Intent | Complete |
| Spec | Complete (formal system, projections, invariants) |
| Design | Complete (Claude Code binding, ADRs 008-010) |
| Code | Phase 1a (configs, iterate agent, commands — no executable engine) |
| Tests | Not started |
| UAT | Not started |
| CI/CD | Not started |
| Telemetry | Not started |

**v1.x preserved at tag `v1.x-final`** — `git checkout v1.x-final`

---

## Task Tracking

- **Active tasks**: `.ai-workspace/tasks/active/ACTIVE_TASKS.md`
- **Finished tasks**: `.ai-workspace/tasks/finished/YYYYMMDD_description.md`

---

## Key Concepts

### Spec / Design Separation

- **Spec** = WHAT, tech-agnostic. One spec, many designs.
- **Design** = HOW architecturally, bound to technology (ADRs, ecosystem).
- Code disambiguation feeds back to **Spec** (business gap) or **Design** (tech gap).

### Projections

The formal system generates valid methodologies. Each projection preserves 4 invariants while varying graph, evaluators, convergence, and context density. Named profiles: full, standard, poc, spike, hotfix, minimal.

### Vector Types

Feature, Discovery, Spike, PoC, Hotfix — each a different projection profile with different convergence criteria and fold-back mechanisms.

### The Iterate Agent

One agent for all edges. Behaviour is parameterised by edge config, not hard-coded. Reads graph topology, loads context, runs evaluator checklist, produces next candidate or reports convergence.

---

## Development Guidelines

### Feature Traceability

- Tag code: `# Implements: REQ-*`
- Tag tests: `# Validates: REQ-*`
- Tag commits: include REQ key in message
- Tag telemetry: `req="REQ-*"` in logs/metrics
- Coverage check: `grep -r "Implements: REQ-" src/` vs spec feature list

### Working on This Project

1. Read ACTIVE_TASKS.md for current work items
2. Read relevant spec/design docs before making changes
3. Keep REQ key traceability when adding features
4. Commit with descriptive messages referencing REQ keys

---

## Related

- **Foundation**: [Constraint-Emergence Ontology](https://github.com/foolishimp/constraint_emergence_ontology)
- **Prior work**: v1.x 7-stage pipeline at tag `v1.x-final`
- **PDF generation**: Use `md2pdf` at `/Users/jim/bin/md2pdf` (handles Mermaid, MathJax)
