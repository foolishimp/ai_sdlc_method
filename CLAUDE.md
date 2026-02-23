# CLAUDE.md - ai_sdlc_method Project Guide

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**ai_sdlc_method** defines a formal system for AI-augmented software development — the **Asset Graph Model** (v2.8).

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
│
├── specification/                          # SHARED — the formal system (tech-agnostic)
│   ├── INTENT.md
│   ├── AI_SDLC_ASSET_GRAPH_MODEL.md
│   ├── PROJECTIONS_AND_INVARIANTS.md
│   ├── AISDLC_IMPLEMENTATION_REQUIREMENTS.md
│   ├── FEATURE_VECTORS.md
│   └── presentations/
│
├── imp_claude/                             # Claude Code implementation
│   ├── design/
│   │   ├── AISDLC_V2_DESIGN.md
│   │   └── adrs/                           #   ADR-008 through ADR-017
│   ├── code/
│   │   └── .claude-plugin/plugins/genisis/
│   │       ├── agents/
│   │       ├── commands/
│   │       ├── config/
│   │       └── hooks/
│   └── tests/
│       ├── conftest.py                     #   Claude-specific path constants
│       ├── test_config_validation.py       #   YAML, edge params, profiles, plugin
│       └── test_methodology_bdd.py         #   BDD methodology scenarios
│
├── imp_gemini/                             # Gemini Genesis implementation
│   ├── design/
│   │   ├── GEMINI_GENESIS_DESIGN.md
│   │   └── adrs/                           #   ADR-GG-001 through ADR-GG-008
│   ├── code/                               #   (future)
│   └── tests/                              #   (future)
│
├── imp_codex/                              # Codex Genesis implementation
│   ├── design/
│   │   ├── CODEX_GENESIS_DESIGN.md
│   │   └── adrs/                           #   ADR-CG-001+
│   ├── code/                               #   (future)
│   └── tests/                              #   (future)
│
├── imp_bedrock/                            # AWS Bedrock Genesis implementation
│   ├── design/
│   │   ├── BEDROCK_GENESIS_DESIGN.md
│   │   └── adrs/                           #   ADR-AB-001 through ADR-AB-008
│   ├── code/                               #   (future)
│   └── tests/                              #   (future)
│
├── docs/
│   └── analysis/                           # Cross-cutting analysis
│
├── .ai-workspace/                          # Runtime workspace state
│   ├── spec/                               #   Derived spec views
│   ├── events/                             #   Shared event log (events.jsonl)
│   ├── features/                           #   Shared feature vectors
│   ├── agents/                             #   Per-agent working state (ADR-013)
│   ├── claude/                             #   Claude design tenant
│   ├── gemini/                             #   Gemini design tenant
│   └── codex/                              #   Codex design tenant
│   └── bedrock/                            #   Bedrock design tenant
│
├── CLAUDE.md                               # This file
└── README.md
```

---

## Key Documents

| Document | Path | What it covers |
|----------|------|---------------|
| Intent | specification/INTENT.md | Business motivation |
| Asset Graph Model | specification/AI_SDLC_ASSET_GRAPH_MODEL.md | Formal system, Hilbert space |
| Projections | specification/PROJECTIONS_AND_INVARIANTS.md | Projections, vector types, spawning |
| Implementation Reqs | specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md | 67 platform-agnostic reqs |
| Feature Vectors | specification/FEATURE_VECTORS.md | Feature decomposition |
| UX | specification/UX.md | User journeys, MVP features, validation scenarios |
| Claude Design | imp_claude/design/AISDLC_V2_DESIGN.md | Claude Code implementation |
| Claude ADRs | imp_claude/design/adrs/ADR-008..017 | 10 ADRs, fully cross-referenced |
| Iterate Agent | imp_claude/code/.../genisis/agents/gen-iterate.md | The universal agent |
| Graph Topology | imp_claude/code/.../genisis/config/graph_topology.yml | 10 asset types, 10 transitions |
| Gemini Design | imp_gemini/design/GEMINI_GENESIS_DESIGN.md | Gemini CLI implementation |
| Codex Design | imp_codex/design/CODEX_GENESIS_DESIGN.md | Codex implementation |
| Bedrock Design | imp_bedrock/design/BEDROCK_GENESIS_DESIGN.md | AWS Bedrock cloud-native implementation |
| Bedrock ADRs | imp_bedrock/design/adrs/ADR-AB-001..008 | 8 platform-specific ADRs |

---

## Current Status

**Version**: v3.0.0-beta.1 (Asset Graph Model)

| Stage | Status |
|-------|--------|
| Intent | Complete |
| Spec | Complete (formal system, IntentEngine §4.6, constraint tolerances §4.6.9, projections, invariants, UX, sensory systems) |
| Design | Complete (Claude: ADRs 008-017, Gemini: ADRs GG-001-008, Codex: ADR-CG-001) |
| Code | Phase 1a (Claude: configs, 4 agents, 13 commands, 4 hooks — no executable engine) |
| Tests | 502 tests (Claude: spec validation + implementation), 22 E2E |
| UAT | Not started |
| CI/CD | Not started |
| Telemetry | Not started |

**Next**: Functor execution model implementation — mode/valence config, affect schema, escalation tests (post ADR-017)

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

### Multi-Tenancy

The repository supports multiple implementations as peers:
- `specification/` — shared contract (WHAT)
- `imp_<name>/` — per-platform implementation (HOW), each owns its own design, code, and tests
- Maximum isolation: everything outside `specification/` belongs to the implementation that owns it

### Projections

The formal system generates valid methodologies. Each projection preserves 4 invariants while varying graph, evaluators, convergence, and context density. Named profiles: full, standard, poc, spike, hotfix, minimal.

### Vector Types

Feature, Discovery, Spike, PoC, Hotfix — each a different projection profile with different convergence criteria and fold-back mechanisms.

### The Iterate Agent

One agent for all edges. Behaviour is parameterised by edge config, not hard-coded. Reads graph topology, loads context, runs evaluator checklist, produces next candidate or reports convergence.

---

## Development Guidelines

### Running Tests

```bash
# All tests (spec + all implementations)
pytest tests/ imp_claude/tests/ -v

# Spec-level only (shared)
pytest tests/ -v

# Claude implementation only
pytest imp_claude/tests/ -v
```

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
