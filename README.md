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

## Getting Started

### 1. Install the Claude Code plugin

```bash
# From your project directory
claude plugin add foolishimp/ai_sdlc_method
```

### 2. Initialize your project workspace

```
/gen-init
```

This scaffolds the asset graph configuration, context store, project constraints, feature tracking, and task management directories.

### 3. Start working (two commands)

```
/gen-start            # Detects state, selects feature/edge, iterates — "Go."
/gen-status           # Project-wide state, "you are here", signals — "Where am I?"
```

Start handles everything: init, feature creation, edge selection, iteration. It detects your project state and routes to the right action automatically.

### Advanced (9 power-user commands)

```
/gen-iterate          # Advance an asset along a specific edge
/gen-spawn            # Spawn a new feature/spike/hotfix vector
/gen-trace            # Trace REQ keys across artifacts
/gen-gaps             # Find traceability gaps
/gen-checkpoint       # Save current progress
/gen-review           # Review an asset for promotion
/gen-release          # Prepare a release
```

### Reading the spec (no tooling needed)

If you just want to understand the methodology, start with:

1. [INTENT.md](specification/INTENT.md) — why this exists
2. [AI_SDLC_ASSET_GRAPH_MODEL.md](specification/AI_SDLC_ASSET_GRAPH_MODEL.md) — the formal system
3. [PROJECTIONS_AND_INVARIANTS.md](specification/PROJECTIONS_AND_INVARIANTS.md) — how it adapts to different scales

---

## Repository Structure

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
│   ├── design/                             #   AISDLC_V2_DESIGN.md + ADRs 008-013
│   ├── code/                               #   Plugin: 1 agent, 10 commands, configs
│   └── tests/                              #   326 tests (spec validation + implementation)
│
├── imp_gemini/                             # Gemini Genesis implementation
│   ├── design/                             #   GEMINI_GENESIS_DESIGN.md + ADRs GG-001-008
│   ├── code/                               #   (future)
│   └── tests/                              #   (future)
│
├── imp_codex/                              # Codex Genesis implementation
│   ├── design/                             #   CODEX_GENESIS_DESIGN.md + ADR-CG-001
│   ├── code/                               #   (future)
│   └── tests/                              #   (future)
│
├── docs/analysis/                          # Cross-cutting analysis
├── .ai-workspace/                          # Runtime workspace state
├── CLAUDE.md                               # Project guide
└── README.md                               # This file
```

---

## Documentation

| Document | What it covers |
|----------|---------------|
| [INTENT.md](specification/INTENT.md) | Business intent and motivation |
| [AI_SDLC_ASSET_GRAPH_MODEL.md](specification/AI_SDLC_ASSET_GRAPH_MODEL.md) | Formal system — 4 primitives, 1 operation, Hilbert space structure |
| [PROJECTIONS_AND_INVARIANTS.md](specification/PROJECTIONS_AND_INVARIANTS.md) | Projections, vector types, spawning, fold-back, time-boxing |
| [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) | Platform-agnostic implementation requirements |
| [FEATURE_VECTORS.md](specification/FEATURE_VECTORS.md) | Feature decomposition for building the methodology itself |
| [AISDLC_V2_DESIGN.md](imp_claude/design/AISDLC_V2_DESIGN.md) | Claude Code implementation design |
| [GEMINI_GENESIS_DESIGN.md](imp_gemini/design/GEMINI_GENESIS_DESIGN.md) | Gemini Genesis implementation design |
| [CODEX_GENESIS_DESIGN.md](imp_codex/design/CODEX_GENESIS_DESIGN.md) | Codex Genesis implementation design |

---

## Status

**Version**: 2.8.0 (Asset Graph Model — Multi-Tenant)

- Spec: Complete (formal system, projections, invariants, consciousness loop, processing phases, sensory systems, UX)
- Design: Complete (Claude ADRs 008-013, Gemini ADRs GG-001-008, Codex ADR-CG-001)
- Code: Phase 1a (Claude: configs, iterate agent, 10 commands, 2 hooks — no executable engine)
- Tests: 326 tests (Claude implementation — spec validation + implementation tests)
- UAT / CI/CD / Telemetry: Not started

**v1.x preserved at tag `v1.x-final`** — recoverable via `git checkout v1.x-final`

---

## License

MIT

---

## Acknowledgments

- **Foundation**: [Constraint-Emergence Ontology](https://github.com/foolishimp/constraint_emergence_ontology)
- **Prior work**: v1.x 7-stage pipeline (superseded), [ai_init](https://github.com/foolishimp/ai_init) (Key Principles, integrated as Context[])
- **Built with**: Claude Code, Gemini CLI, Codex
