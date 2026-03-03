# Specification — Document Map

This directory contains the **shared contract** for the AI SDLC Asset Graph Model. All platform implementations (`imp_claude/`, `imp_gemini/`, `imp_codex/`, `imp_bedrock/`) build against it.

Everything here is **tech-agnostic**. No Claude, no MCP, no slash commands. Those belong to each implementation.

See [adrs/ADR-S-001-specification-document-hierarchy.md](adrs/ADR-S-001-specification-document-hierarchy.md) for the rationale behind this structure.

---

## Directory Structure

```
specification/
├── INTENT.md                    ← anchor: the why (upstream of everything)
│
├── core/                        ← PRIMARY: the formal system (inputs)
│   ├── AI_SDLC_ASSET_GRAPH_MODEL.md
│   ├── PROJECTIONS_AND_INVARIANTS.md
│   ├── EXECUTIVE_SUMMARY.md
│   └── GENESIS_BOOTLOADER.md
│
├── requirements/                ← DERIVED tier 1: what any implementation must do
│   └── AISDLC_IMPLEMENTATION_REQUIREMENTS.md
│
├── features/                    ← DERIVED tier 2: how requirements decompose into buildable units
│   └── FEATURE_VECTORS.md
│
├── ux/                          ← DERIVED tier 2: how the system presents to users
│   └── UX.md
│
├── verification/                ← DERIVED tier 3: how to verify an implementation satisfies requirements
│   └── UAT_TEST_CASES.md
│
└── adrs/                        ← Spec-level architectural decisions (ADR-S-* series)
    ├── ADR-S-001-specification-document-hierarchy.md
    ├── ADR-S-002-multi-tenancy-model.md
    ├── ...
    └── ADR-S-012-event-stream-as-formal-model-medium.md
```

---

## Derivation Chain

```
Constraint-Emergence Ontology  (external)
        │
        ▼
   INTENT.md                          Why we're building this
        │
        ▼
   core/AI_SDLC_ASSET_GRAPH_MODEL.md        The formal system — 4 primitives, 1 operation
        │
        ├──► core/PROJECTIONS_AND_INVARIANTS.md    Graph subsets, profiles, spawn/fold-back
        ├──► core/EXECUTIVE_SUMMARY.md             5-minute digest
        ├──► core/GENESIS_BOOTLOADER.md            LLM operational distillation
        │
        └──► requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md   74 requirements
                    │                   (spec/design boundary is downstream of here)
                    ├──► features/FEATURE_VECTORS.md      13 features, dependency DAG, build order, MVP scope
                    │           │
                    │           ├──► ux/UX.md              User journeys, MVP, validation
                    │           │
                    │           └──► verification/UAT_TEST_CASES.md   Acceptance contracts (9 use cases)
                    │
                    └──► (ux/ and verification/ also derive from requirements directly)
```

**Rule**: downstream documents may not contradict upstream ones. A conflict is always resolved by fixing the downstream document.

---

## Document Reference

### Primary (core/)

| Document | Role | Size |
|----------|------|------|
| [core/AI_SDLC_ASSET_GRAPH_MODEL.md](core/AI_SDLC_ASSET_GRAPH_MODEL.md) | The formal system — 4 primitives, 1 operation | 1379 lines |
| [core/PROJECTIONS_AND_INVARIANTS.md](core/PROJECTIONS_AND_INVARIANTS.md) | Graph subsets, profiles, spawn/fold-back, time-boxing | 791 lines |
| [core/EXECUTIVE_SUMMARY.md](core/EXECUTIVE_SUMMARY.md) | 5-minute digest — start here | 59 lines |
| [core/GENESIS_BOOTLOADER.md](core/GENESIS_BOOTLOADER.md) | LLM axiom set — load into sessions, not for human reading | 352 lines |

### Derived

| Document | Derives From | Role | Size |
|----------|-------------|------|------|
| [requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md](requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) | core model | 83 platform-agnostic requirements | 1402 lines |
| [features/FEATURE_VECTORS.md](features/FEATURE_VECTORS.md) | requirements | 13 features, dependency graph, build order | 409 lines |
| [ux/UX.md](ux/UX.md) | core model + requirements | User journeys, MVP, validation scenarios | 1087 lines |
| [verification/UAT_TEST_CASES.md](verification/UAT_TEST_CASES.md) | requirements + features | BDD acceptance contracts (9 use cases) | 3287 lines |

### Spec-Level Decisions (adrs/)

| ADR | Decision | Key Rule |
|-----|----------|----------|
| [ADR-S-001](adrs/ADR-S-001-specification-document-hierarchy.md) | Document hierarchy | Tiered subdirectories reflect derivation order |
| [ADR-S-002](adrs/ADR-S-002-multi-tenancy-model.md) | Multi-tenancy model | `specification/` shared; `imp_*/` isolated; one-way read dependency |
| [ADR-S-003](adrs/ADR-S-003-req-key-format.md) | REQ key format | `REQ-{CLASS}-{SEQ}` threads from spec to code to tests to telemetry |
| [ADR-S-004](adrs/ADR-S-004-derivation-constraint.md) | Derivation constraint | Downstream may not contradict upstream; fix the downstream doc |
| [ADR-S-005](adrs/ADR-S-005-spec-versioning-contract.md) | Spec versioning | Semantic versioning; breaking changes listed explicitly |
| [ADR-S-006](adrs/ADR-S-006-feature-decomposition-node.md) | Feature Decomposition node | Explicit graph node between Requirements and Design; spec/design boundary moves |
| [ADR-S-007](adrs/ADR-S-007-module-decomposition-basis-projections.md) | Module Decomposition node | Explicit nodes for mapping architecture to code; enables parallelism |
| [ADR-S-008](adrs/ADR-S-008-sensory-triage-intent-pipeline.md) | Sensory-Triage-Intent | The "Consciousness Loop": how signals become actionable intents |
| [ADR-S-009](adrs/ADR-S-009-feature-vector-lifecycle-spec-vs-trajectory.md) | Feature Vector Lifecycle | Spec layer = feature definitions; workspace layer = trajectory only; JOIN semantics |
| [ADR-S-010](adrs/ADR-S-010-event-sourced-spec-evolution.md) | Event-Sourced Spec Evolution | `feature_proposal` and `spec_modified` events; promotion path; Draft Features Queue |
| [ADR-S-011](adrs/ADR-S-011-openlineage-unified-metadata-standard.md) | OpenLineage Unified Metadata | All events follow OL RunEvent schema; custom facets; local-first; causal chaining via ParentRunFacet |
| [ADR-S-012](adrs/ADR-S-012-event-stream-as-formal-model-medium.md) | Event Stream Medium | All primitives operate on append-only event stream; Asset as projection; Saga invariant |


---

## Reading Paths

### "I'm new — what is this?"
1. [core/EXECUTIVE_SUMMARY.md](core/EXECUTIVE_SUMMARY.md) — 5 minutes
2. [INTENT.md](INTENT.md) — 5 minutes
3. [core/AI_SDLC_ASSET_GRAPH_MODEL.md](core/AI_SDLC_ASSET_GRAPH_MODEL.md) §0–§3 — 30 minutes

### "I'm building a new implementation (imp_X/)"
1. [requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md](requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — full read
2. [features/FEATURE_VECTORS.md](features/FEATURE_VECTORS.md) — for build ordering
3. [verification/UAT_TEST_CASES.md](verification/UAT_TEST_CASES.md) — for acceptance criteria
4. [core/PROJECTIONS_AND_INVARIANTS.md](core/PROJECTIONS_AND_INVARIANTS.md) §3–§7 — for profile design

### "I'm starting a Genesis work session (LLM)"
Load [core/GENESIS_BOOTLOADER.md](core/GENESIS_BOOTLOADER.md) into context — replaces loading the full spec for routine operation.

### "I need to understand profiles / spawning / time-boxing"
[core/PROJECTIONS_AND_INVARIANTS.md](core/PROJECTIONS_AND_INVARIANTS.md) — full read

### "I'm writing UAT tests for my implementation"
1. [verification/UAT_TEST_CASES.md](verification/UAT_TEST_CASES.md) — use case structure as template
2. [features/FEATURE_VECTORS.md](features/FEATURE_VECTORS.md) — for coverage matrix

---

## What Belongs Where

| `specification/core/` | `specification/requirements/` | `specification/features/` | `specification/verification/` | `imp_*/design/` |
|----------------------|------------------------------|--------------------------|------------------------------|----------------|
| Formal system | Platform-agnostic REQ keys | Feature decomposition | BDD acceptance contracts | Tech-bound ADRs |
| 4 primitives definition | Acceptance criteria per REQ | Dependency graph | Shared UAT contracts | Concrete configs |
| Projection profiles | | Build order | | Platform test files |
