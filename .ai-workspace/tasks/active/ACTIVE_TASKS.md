# Active Tasks

*Last Updated: 2026-02-22*
*Methodology: AI SDLC Asset Graph Model v3.0.0-beta.1*

---

## Next: Actor Model Review and Deterministic Code Backing (gates v3.0)

**Priority**: High
**Status**: Not Started
**Release Target**: 3.0

**Description**:
Review the actor model (IntentEngine, sensory service, iterate agent, coordination serialiser) and decide which flows become deterministic code-backed vs. remain agent-driven. This is the architectural decision that gates v3.0.

**Key Questions**:
1. Which IntentEngine flows (reflex, affect, escalate routing) should be deterministic code (guaranteed behaviour, testable, fast)?
2. Which flows remain probabilistic/agent-driven (require LLM classification, context-sensitive)?
3. Where is the boundary between the deterministic engine and the agent layer?
4. What is the runtime architecture? (event loop, message passing, process model)
5. How do constraint tolerances (REQ-SUPV-002) get wired to monitors in code?

**Context**:
- Spec §4.6 defines IntentEngine as composition law: observer → evaluator → typed_output
- Spec §4.6.9 defines constraint tolerances as the mechanism producing delta
- ADR-014 binds IntentEngine to Claude Code (currently config-only, no engine code)
- ADR-016 binds tolerances to design-level monitoring
- The decision: which parts of this become a runtime engine vs. remaining as agent-interpreted config

**Depends On**: All spec work complete (v3.0.0-beta.1)

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
