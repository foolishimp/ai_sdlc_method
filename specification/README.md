# Specification — Document Map

This directory contains the **shared contract** for the AI SDLC Asset Graph Model — the formal system that all platform implementations (`imp_claude/`, `imp_gemini/`, `imp_codex/`, `imp_bedrock/`) build against.

Everything here is **tech-agnostic**. No Claude, no MCP, no slash commands. Those belong to the implementation that uses them.

---

## Derivation Hierarchy

Documents derive from each other in a strict chain. Downstream documents must not contradict upstream ones.

```
Constraint-Emergence Ontology  (external — github.com/foolishimp/constraint_emergence_ontology)
        │
        ▼
   INTENT.md                          Why we're building this
        │
        ▼
AI_SDLC_ASSET_GRAPH_MODEL.md         The formal system — 4 primitives, 1 operation
        │
        ├──► EXECUTIVE_SUMMARY.md         5-minute digest of the formal system
        │
        ├──► GENESIS_BOOTLOADER.md        Compressed axiom set for LLM sessions
        │
        ├──► PROJECTIONS_AND_INVARIANTS.md  Graph subsets, profiles, spawn/fold-back
        │
        ├──► UX.md                         User journeys, MVP, validation scenarios
        │
        └──► AISDLC_IMPLEMENTATION_REQUIREMENTS.md   74 platform-agnostic requirements
                    │
                    ├──► FEATURE_VECTORS.md            13 features, dependency graph
                    │
                    └──► UAT_TEST_CASES.md              Acceptance tests (9 use cases)

USER_GUIDE.md                         Practitioner guide (Claude implementation)
```

---

## Document Reference

| Document | Role | Size | When to use |
|----------|------|------|-------------|
| [INTENT.md](INTENT.md) | **Foundation** — the why | 67 lines | Start here. Answers: what problem are we solving and what does success look like? |
| [AI_SDLC_ASSET_GRAPH_MODEL.md](AI_SDLC_ASSET_GRAPH_MODEL.md) | **Formal system** — the what | 1379 lines | The primary reference. Defines the 4 primitives (Graph, Iterate, Evaluators, Spec+Context), the IntentEngine, sensory systems, and the full lifecycle. Read this to understand the model deeply. |
| [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) | **Digest** — 5-minute read | 59 lines | Read first for orientation. Covers the entire system in one page: primitives, bootstrap graph, functor encoding, projections, multi-tenancy. |
| [GENESIS_BOOTLOADER.md](GENESIS_BOOTLOADER.md) | **LLM axiom set** — operational | 352 lines | Load this into an LLM session at the start of any work session. It replaces loading the full spec + design docs. Not a human reading document — it's structured for LLM constraint. |
| [PROJECTIONS_AND_INVARIANTS.md](PROJECTIONS_AND_INVARIANTS.md) | **Extension** — graph flexibility | 791 lines | Read when you need to: select a profile (full/standard/poc/spike/hotfix/minimal), understand invariants, design spawn/fold-back mechanics, or configure time-boxing. |
| [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](AISDLC_IMPLEMENTATION_REQUIREMENTS.md) | **Requirements** — build contract | 1402 lines | The authoritative list of 74 platform-agnostic requirements (REQ-INTENT through REQ-ROBUST). Every implementation must satisfy these. Each requirement has priority, rationale, and acceptance criteria. |
| [FEATURE_VECTORS.md](FEATURE_VECTORS.md) | **Build plan** — what to build when | 409 lines | Shows how requirements decompose into 13 buildable feature vectors with a dependency graph and compressed task graph. Use when planning implementation order. |
| [UX.md](UX.md) | **User experience** — journeys and scenarios | 1087 lines | Defines 7 user journeys, MVP feature set, and validation scenarios. Use when designing the user-facing interaction layer of any implementation. |
| [UAT_TEST_CASES.md](UAT_TEST_CASES.md) | **Acceptance tests** — 9 use cases | 3287 lines | BDD-style acceptance test cases derived from requirements. One use case per major domain (asset graph, evaluators, context, traceability, edges, lifecycle, sensory, tooling, UX). Use when writing implementation-level UAT suites. |
| [USER_GUIDE.md](USER_GUIDE.md) | **Practitioner guide** — how to use Genesis | 1194 lines | Step-by-step guide for using the Genesis methodology day-to-day: installation, first project, working through the graph, REQ key tagging. Specific to the Claude Code implementation. |

---

## Reading Paths

### "I'm new — what is this?"
1. [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) — 5 minutes
2. [INTENT.md](INTENT.md) — 5 minutes
3. [AI_SDLC_ASSET_GRAPH_MODEL.md](AI_SDLC_ASSET_GRAPH_MODEL.md) §0–§3 — 30 minutes

### "I'm building a new implementation (imp_X/)"
1. [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — full read
2. [FEATURE_VECTORS.md](FEATURE_VECTORS.md) — for build ordering
3. [UAT_TEST_CASES.md](UAT_TEST_CASES.md) — for acceptance criteria
4. [PROJECTIONS_AND_INVARIANTS.md](PROJECTIONS_AND_INVARIANTS.md) §3–§7 — for profile design

### "I'm starting a Genesis work session (LLM)"
1. Load [GENESIS_BOOTLOADER.md](GENESIS_BOOTLOADER.md) into context — replaces everything else for routine operation

### "I need to understand profiles / spawning / time-boxing"
1. [PROJECTIONS_AND_INVARIANTS.md](PROJECTIONS_AND_INVARIANTS.md) — full read

### "I want to use Genesis on my project today"
1. [USER_GUIDE.md](USER_GUIDE.md) — installation through first iteration

### "I'm writing UAT tests for my implementation"
1. [UAT_TEST_CASES.md](UAT_TEST_CASES.md) — use case structure as template
2. [FEATURE_VECTORS.md](FEATURE_VECTORS.md) — for coverage matrix

---

## What Belongs Here vs. in `imp_*/`

| Belongs in `specification/` | Belongs in `imp_*/design/` |
|-----------------------------|---------------------------|
| The 4 primitives definition | How Claude Code implements iterate() |
| Platform-agnostic REQ keys | ADRs binding to specific technology |
| Graph topology (abstract) | graph_topology.yml (concrete YAML) |
| Evaluator types (F_D/F_P/F_H) | Edge param configs (evaluator_defaults.yml) |
| User journeys (UX.md) | Slash command specs (gen-start.md) |
| UAT test cases (BDD scenarios) | pytest test files (test_uc01_asset_graph.py) |

If a document mentions Claude, MCP, Python, or any specific technology — it belongs in `imp_*/`, not here.
