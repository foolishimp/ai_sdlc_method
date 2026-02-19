# AI SDLC: The Asset Graph Model

**A formal system for AI-augmented software development** — 4 primitives, 1 operation, valid projections at every scale.

**Foundation**: [Constraint-Emergence Ontology](https://github.com/foolishimp/constraint_emergence_ontology)

---

## What Is This?

A methodology that reduces all software development to:

| Primitive | What it is |
|-----------|-----------|
| **Graph** | Topology of typed assets with admissible transitions |
| **Iterate** | Convergence engine — the only operation |
| **Evaluators** | Convergence test — {Human, Agent, Deterministic Tests} |
| **Spec + Context** | Constraint surface — what bounds construction |

Everything else — stages, agents, TDD, BDD, projections — is parameterisation of these four primitives.

### The Core Operation

```
iterate(Asset, Context[], Evaluators) → Asset'

while not stable(candidate):
    candidate = iterate(candidate, context, evaluators)
return promote(candidate)    // candidate becomes stable Markov object
```

### The SDLC Graph (one projection)

```
Intent → Spec → Design → Code ↔ Tests → UAT → CI/CD → Telemetry
           ↑       ↑                                        │
           │       └── feedback (tech ambiguity) ───────────┤
           └──────── feedback (business ambiguity) ─────────┘
```

This graph is not universal — it is one domain-specific instantiation. The four primitives are universal; the graph is parameterised.

### Feature Lineage

Every asset carries REQ keys from spec to runtime:

```
Spec:       REQ-F-AUTH-001 defined
Design:     Implements: REQ-F-AUTH-001
Code:       # Implements: REQ-F-AUTH-001
Tests:      # Validates: REQ-F-AUTH-001
Telemetry:  logger.info("login", req="REQ-F-AUTH-001", latency_ms=42)
```

One identifier, end to end. Feature views are generated at every stage by grepping the REQ key across artifacts.

---

## Key Concepts

### Projections

The formal system is a **generator of valid methodologies**. Each valid instance preserves the 4 invariants while varying:
- **Graph** — from 2 nodes / 1 edge to the full SDLC
- **Evaluators** — which types are active per edge
- **Convergence** — what "done" means (all checks pass, question answered, time box expired)
- **Context** — how many constraints bound construction

A 10-minute spike and a regulated medical device both use the same four primitives with different parameterisation.

### Vector Types

| Type | Purpose | Convergence |
|------|---------|-------------|
| **Feature** | Deliver a capability | All required checks pass |
| **Discovery** | Answer a question | Question answered or time box expired |
| **Spike** | Assess technical risk | Risk assessed or time box expired |
| **PoC** | Validate feasibility | Hypothesis confirmed/rejected |
| **Hotfix** | Fix production issue | Fix verified in production |

### Spec / Design Separation

- **Spec** — WHAT the system does, tech-agnostic. One spec, many designs.
- **Design** — HOW architecturally, bound to technology. ADRs, ecosystem binding.
- **Code** — HOW concretely, eventually fully automated. Disambiguation feeds back to Spec (business gap) or Design (tech gap).

---

## Repository Structure

```
ai_sdlc_method/
├── docs/
│   ├── specification/                   # SPEC (tech-agnostic)
│   │   ├── INTENT.md                    #   Business intent
│   │   ├── AI_SDLC_ASSET_GRAPH_MODEL.md #   Formal system (4 primitives)
│   │   ├── PROJECTIONS_AND_INVARIANTS.md #   Projections, vector types
│   │   ├── AISDLC_IMPLEMENTATION_REQUIREMENTS.md  # Implementation reqs
│   │   ├── FEATURE_VECTORS.md           #   Feature decomposition
│   │   └── presentations/*.pdf          #   PDF versions
│   └── design/claude_aisdlc/            # DESIGN (Claude Code binding)
│       ├── AISDLC_V2_DESIGN.md          #   Implementation design
│       └── adrs/                        #   Architecture decisions
│           ├── ADR-008 (universal iterate agent)
│           ├── ADR-009 (graph topology as config)
│           └── ADR-010 (spec reproducibility)
├── claude-code/.../v2/                  # IMPLEMENTATION (Claude Code)
│   ├── agents/aisdlc-iterate.md         #   The ONE agent
│   ├── commands/ (8 commands)           #   /aisdlc-* slash commands
│   └── config/                          #   Graph + edge parameterisations
│       ├── graph_topology.yml
│       ├── evaluator_defaults.yml
│       ├── project_constraints_template.yml
│       ├── feature_vector_template.yml
│       └── edge_params/ (9 configs)
├── .ai-workspace/tasks/                 # Task tracking
├── CLAUDE.md                            # Project guide
└── README.md                            # This file
```

---

## Documentation

| Document | What it covers |
|----------|---------------|
| [INTENT.md](docs/specification/INTENT.md) | Business intent and motivation |
| [AI_SDLC_ASSET_GRAPH_MODEL.md](docs/specification/AI_SDLC_ASSET_GRAPH_MODEL.md) | Formal system — 4 primitives, 1 operation, Hilbert space structure |
| [PROJECTIONS_AND_INVARIANTS.md](docs/specification/PROJECTIONS_AND_INVARIANTS.md) | Projections, vector types, spawning, fold-back, time-boxing |
| [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](docs/specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) | Platform-agnostic implementation requirements |
| [FEATURE_VECTORS.md](docs/specification/FEATURE_VECTORS.md) | Feature decomposition for building the methodology itself |
| [AISDLC_V2_DESIGN.md](docs/design/claude_aisdlc/AISDLC_V2_DESIGN.md) | Claude Code implementation design |

---

## Status

**Version**: 2.1 (Asset Graph Model)

- Spec: Complete (formal system, projections, invariants)
- Design: Complete (Claude Code binding, ADRs)
- Code: Phase 1a (configs, iterate agent, commands — no executable engine)
- Tests: Not started
- UAT / CI/CD / Telemetry: Not started

**v1.x preserved at tag `v1.x-final`** — recoverable via `git checkout v1.x-final`

---

## License

MIT

---

## Acknowledgments

- **Foundation**: [Constraint-Emergence Ontology](https://github.com/foolishimp/constraint_emergence_ontology)
- **Prior work**: v1.x 7-stage pipeline (superseded), [ai_init](https://github.com/foolishimp/ai_init) (Key Principles, integrated as Context[])
- **Built with**: Claude Code
