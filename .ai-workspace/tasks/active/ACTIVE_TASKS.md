# Active Tasks

*Last Updated: 2026-03-03*
*Methodology: AI SDLC Asset Graph Model v3.0.0-beta.1*

---

## Resolved: Actor Model Review and Deterministic Code Backing (gates v3.0)

**Priority**: High
**Status**: Resolved — ADR-017
**Release Target**: 3.0

**Description**:
Review the actor model (IntentEngine, sensory service, iterate agent, coordination serialiser) and decide which flows become deterministic code-backed vs. remain agent-driven. This is the architectural decision that gates v3.0.

**Resolution**: [ADR-017: Functor-Based Execution Model](../../imp_claude/design/adrs/ADR-017-functor-based-execution-model.md)

The boundary between deterministic and probabilistic is not a static line — it is a **functor composition** parameterised by execution mode and affect valence. Each functional unit (evaluate, construct, classify, route, propose, sense) has three renderings: F_D (deterministic), F_P (probabilistic), F_H (human). The natural transformation η re-renders units between categories when ambiguity exceeds the current category's capacity. The starting functor determines the execution mode (headless = start F_D, interactive = start F_H). Valence controls escalation sensitivity per profile (hotfix = high, standard = medium, spike = low).

**Key Questions — Answered**:
1. ~~Which flows are deterministic?~~ → All units start F_D where ambiguity = 0 (Rendering Table)
2. ~~Which flows are probabilistic?~~ → Same units, rendered F_P when ambiguity > 0 (Rendering Table)
3. ~~Where is the boundary?~~ → The natural transformation η — a runtime threshold, not a static line
4. ~~What is the runtime architecture?~~ → Iterate agent + functor dispatch table (no new process model)
5. ~~How do tolerances wire to monitors?~~ → F_D(Sense) → η_D→P → F_P(Classify) → intent

**Depends On**: All spec work complete (v3.0.0-beta.1)

---

## Next: Implement feature_proposal Pipeline — Consciousness Loop Stage 2+3

**Priority**: High
**Status**: Not Started
**Release Target**: 3.0
**Triggered by**: Gemini comparison review (2026-03-03) + `/gen-gaps` INT-GAPS-001..004

**Description**:
The consciousness loop in `imp_claude` stops at Stage 1 (`intent_raised`). Stages 2 and 3 are not implemented. Per ADR-011 confirmed gap:

- **Stage 2 (Affect Triage)**: Classify `intent_raised` signals by ambiguity regime, emit `feature_proposal` event (draft proposal, event log only, no spec write)
- **Stage 3 (Human Gate)**: `/gen-review-proposal` command — list pending proposals, approve → `spec_modified` + `FEATURE_VECTORS.md` append, dismiss → `feature_proposal_dismissed`

**Tasks**:
1. Add `feature_proposal` and `feature_proposal_dismissed` event types to event schema (fd_emit.py + events schema docs)
2. Add `feature_proposal` emission to `/gen-gaps` Stage 6 (currently emits `intent_raised` only; bounded-ambiguity signals should escalate to proposals)
3. Create `/gen-review-proposal` command (list | approve | dismiss) — distinct from `/gen-review` which handles edge convergence
4. Approval path: append-only write to `specification/features/FEATURE_VECTORS.md`, emit `spec_modified` with `previous_hash`/`new_hash`, run SpawnCommand to inflate workspace trajectory
5. Design test coverage for the pipeline (test_functor_construct.py pattern)

**Reference**:
- ADR-011 Confirmed Gap section (2026-03-03)
- Gemini reference: `imp_gemini/gemini_cli/engine/triage.py`, `imp_gemini/gemini_cli/commands/review.py`
- Spec: ADR-S-008 Stage 2+3

**Depends On**: Nothing blocking — can start immediately

---

## Next: Functor Execution Model Implementation (post ADR-017)

**Priority**: High
**Status**: Not Started
**Release Target**: 3.0

**Description**:
Implement the configuration and test scaffolding from ADR-017.

**Tasks**:
1. Add `mode` (headless | interactive | auto) and `valence` (high | medium | low) to project binding schema (`project_constraints.yml`)
2. Add `valence` field to feature vector affect schema
3. Annotate existing edge configs with starting-functor comments
4. Design integration tests for escalation paths (η_D→P and η_P→H)

**Depends On**: ADR-017 accepted

---

## In Progress: Instance Graph from Events — Monitor Zoom Model (ADR-022)

**Priority**: Medium
**Status**: Partially Complete (2026-03-03)
**Release Target**: 3.1
**Triggered by**: Genesis Monitor showing static topology instead of dynamic instance graph (2026-03-03)

**Description**:
The monitor currently shows `graph_topology.yml` as the graph (type system / schema). It should show the INSTANCE graph derived from the event log — feature vectors as positioned nodes on the topology, zoom levels 0/1/2. Per ADR-022.

**Tasks**:
1. ~~Replace Mermaid Gantt with HTML feature × edge matrix table~~ **DONE** — `build_feature_matrix()` in `projections/gantt.py`; `_gantt.html` now renders an HTML matrix with hierarchy, status symbols, iteration count, hover timestamps; 13 new tests
2. ~~Add Feature×Module bipartite map (Zoom 2 approximation)~~ **DONE** — `build_feature_module_map()` in `projections/feature_module_map.py`; new `_feature_module_map.html` + route `/fragments/.../feature-module-map`; REQ tag scan approximation pending `module_assigned` events; gap highlighting for untraced keys
3. ~~Fix test suite to OL v2 format~~ **DONE** — `tests/event_factory.py` (make_ol2_event helper); all 38 pre-existing failures fixed; 289/289 passing; added missing routes (`/fragments/project-list`, `/fragments/project/{id}/edges`); fixed `project_detail` + `fragment_gantt` to pass `matrix` context
4. Add `project_instance_graph(events) → InstanceGraph` projection — full event replay approach
5. Add zoom level 1 overlay to `graph.py` — position feature nodes on topology edges
6. Add topology version check to `on-session-start.sh` (warn when workspace stale vs plugin)

**Depends On**: Nothing blocking

---

## Backlog

- **Task #37**: Ecosystem E(t) as Feedback Loop Edge (Low — reframe v1.x E(t) for asset graph)
- **Task #34**: Propagate Insights Back to Ontology (Low — 4 insights for constraint-emergence repo)

---

## Current State (v3.0.0-beta.1)

| Artifact | Status |
|----------|--------|
| Spec (Asset Graph Model) | Complete — 4 primitives, IntentEngine, tolerances, sensory systems |
| Implementation Requirements | 60 requirements, 10 critical, full coverage |
| Feature Vectors | 11 vectors, 60/60 requirements covered |
| Claude Design (ADRs 008-021) | Complete — 14 ADRs, fully cross-referenced |
| Claude Code (Phase 1a) | 13 commands, 2 hooks, 4 agents, iterate agent, engine CLI (delta=0) |
| Tests | 950 non-e2e passing, 34 e2e |
| Gemini Design | Complete (ADRs GG-001-008) |
| Codex Design | Complete (ADR-CG-001) |

---

## Recovery Commands

```bash
cat .ai-workspace/tasks/active/ACTIVE_TASKS.md  # This file
git status                                       # Current state
git log --oneline -10                            # Recent commits
git tag -l                                       # All tags
git checkout v1.x-final                          # Recover v1.x if needed
```
