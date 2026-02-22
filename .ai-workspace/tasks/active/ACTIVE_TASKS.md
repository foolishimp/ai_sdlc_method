# Active Tasks

*Last Updated: 2026-02-22*
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
| Claude Design (ADRs 008-016) | Complete — 9 ADRs, fully cross-referenced |
| Claude Code (Phase 1a) | 10 commands, 2 hooks, iterate agent, configurable graph |
| Tests | 502 non-e2e passing, 22 e2e |
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
