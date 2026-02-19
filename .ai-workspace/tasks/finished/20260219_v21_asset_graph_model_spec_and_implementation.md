# Task: v2.1 Asset Graph Model — Spec, Implementation, and Projections

**Status**: Completed
**Date**: 2026-02-19
**Actual Time**: ~3 sessions across multiple days

**Task ID**: #31
**Requirements**: All v2.1 requirements (REQ-GRAPH-*, REQ-ITER-*, REQ-EVAL-*, REQ-CTX-*, REQ-INTENT-*, REQ-FEAT-*, REQ-EDGE-*)

---

## Problem

The v1.x methodology was a 7-stage sequential pipeline with stage-specific agents. It worked but was conceptually rigid — fixed stages, fixed order, fixed agents. The formal system needed to be recast as an asset graph with a universal iteration function, where "stages" and "agents" are parameterisation of four primitives, not hard-coded concepts.

Additionally, the formal system needed to support **projections** — valid lighter instances that preserve invariants while varying in strictness and scope. A 10-minute spike and a regulated medical device should use the same four primitives with different parameterisation.

---

## What Was Done

### Phase 1: Formal Spec (commit 91f29bc)

Rewrote the formal system as **AI_SDLC_ASSET_GRAPH_MODEL.md** (~570 lines):
- 4 primitives: Graph, Iterate, Evaluators, Spec+Context
- 1 operation: `iterate(Asset<Tn>, Context[], Evaluators(edge_type)) → Asset<Tn.k+1>`
- Asset graph with 10 asset types, 10 transitions
- Feature vectors as composite trajectories through the graph
- Hilbert space structure with Hamiltonian cost dynamics
- Ontology traceability to constraint-emergence concepts

Created **FEATURE_VECTORS.md** — feature decomposition for implementing the methodology itself.

### Phase 2: Implementation Design (commit b6496b1)

Created Claude Code implementation design:
- Graph topology as YAML config
- Edge parameterisation configs
- Universal iterate agent
- 8 commands mapping to graph operations

### Phase 3: ADRs (commit c04c187)

Created 3 ADRs:
- ADR-008: Universal Iterate Agent (replaces 7 stage-specific agents)
- ADR-009: Graph Topology as Configuration
- ADR-010: Spec Reproducibility via Context Hashing

### Phase 4: Implementation Phase 1a (commit ecced4f)

Implemented in `claude-code/.claude-plugin/plugins/aisdlc-methodology/v2/`:
- `config/graph_topology.yml` — 10 asset types, 10 transitions
- `config/evaluator_defaults.yml` — 3 evaluator types
- `config/edge_params/*.yml` — 9 edge parameterisation configs (tdd, bdd, adr, intent_requirements, requirements_design, design_code, design_tests, feedback_loop, code_tagging)
- `agents/aisdlc-iterate.md` — Universal iterate agent
- `commands/aisdlc-*.md` — 8 commands (init, iterate, feature, status, checkpoint, graph, context, help)

### Phase 5: Constraint Binding Templates (commit 0685ad9, +1,092/-263 lines)

Closed the gap between abstract evaluators and concrete checks:
- `config/project_constraints_template.yml` (NEW) — binds to project tools, thresholds, standards
- `config/feature_vector_template.yml` (NEW) — template with constraints section
- Updated all 9 edge configs with structured evaluator checklists using `$variable` references
- Updated iterate agent with 7-step checklist composition algorithm
- Updated /aisdlc-init with auto-detection scaffolding
- Updated /aisdlc-iterate with effective checklist construction

4-layer composition: evaluator_defaults → edge checklist (with $variable refs) → project_constraints → feature acceptance_criteria

### Phase 6: Projections and Invariants (commit fa438be, +640 lines)

Created **PROJECTIONS_AND_INVARIANTS.md** addressing 6 identified gaps:
1. **Invariant definitions** — the 4 primitives are what must survive any valid projection
2. **Projection concept** — generalises Zoom to 4 dimensions (graph, evaluators, convergence, context)
3. **Vector types** — Feature, Discovery, Spike, PoC, Hotfix
4. **Spawning and fold-back** — child vectors fold back as Context[] enrichment
5. **Time-boxing** — convergence extended to `δ = 0 OR question_answered OR time_box_expired`
6. **Projection profiles** — named configurations (full, standard, poc, spike, hotfix, minimal)

---

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| `docs/requirements/AI_SDLC_ASSET_GRAPH_MODEL.md` | ~570 | Formal spec — 4 primitives, 1 operation |
| `docs/requirements/FEATURE_VECTORS.md` | ~120 | Feature decomposition |
| `docs/requirements/PROJECTIONS_AND_INVARIANTS.md` | ~640 | Projections, invariants, vector types |
| `v2/config/graph_topology.yml` | | 10 asset types, 10 transitions |
| `v2/config/evaluator_defaults.yml` | | 3 evaluator types, check schema |
| `v2/config/project_constraints_template.yml` | | Project tools/thresholds/standards |
| `v2/config/feature_vector_template.yml` | | Feature vector template with constraints |
| `v2/config/edge_params/*.yml` | 9 files | Structured evaluator checklists |
| `v2/agents/aisdlc-iterate.md` | | Universal iterate agent |
| `v2/commands/aisdlc-*.md` | 8 files | Graph-aware commands |
| `v2/design/*.md` | 3 files | ADRs 008, 009, 010 |

## Commits

```
fa438be docs: Add projections and invariants spec
0685ad9 feat: Add constraint binding templates and structured evaluator checklists
ecced4f feat: Implement Phase 1a — iterate agent, graph topology, 8 commands
c04c187 docs: Add v2.1 ADRs — iterate agent, graph topology, spec reproducibility
b6496b1 docs: Add v2.1 Claude Code implementation design
91f29bc docs: v2.1 Asset Graph Model — spec revision, feature vector decomposition
```

All pushed to origin/main.

---

## Key Insight

The formal system is a **generator of valid methodologies**, not a single methodology. Each valid instance (projection) preserves the 4 invariants while varying graph size, evaluator strictness, convergence criteria, and context density. The full SDLC graph is one projection. A 10-minute spike is another.

---

## Result

All 6 phases completed and pushed. The v2.1 formal system, implementation, and projections extension are complete.

---

## Traceability

- INT-AISDLC-001: AI SDLC Methodology Implementation
- All REQ-GRAPH-*, REQ-ITER-*, REQ-EVAL-*, REQ-CTX-* requirements addressed
- All REQ-EDGE-* requirements addressed via structured edge configs
- REQ-INTENT-004 (spec reproducibility) addressed via context hashing design

---

## Lessons Learned

1. **The spec is a generator, not a prescription** — the full graph is one projection, not THE system
2. **4-layer composition works** — evaluator_defaults → edge → project → feature is the right granularity
3. **$variable resolution** makes configs portable — same edge config, different projects
4. **Traceability is emergent** from the 4 invariants, not a 5th invariant
5. **Zoom is a special case of projection** — projection also varies evaluators, convergence, and context
