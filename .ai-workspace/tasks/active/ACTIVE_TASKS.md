# Active Tasks

*Last Updated: 2026-02-19 18:00*
*Methodology: AI SDLC Asset Graph Model v2.1*

---

## Task #32: Projection Profiles and Vector Type Support

**Priority**: High
**Status**: Not Started
**Release Target**: 2.1

**Description**:
Turn the projection and vector type concepts from PROJECTIONS_AND_INVARIANTS.md into working configs and agent support. Currently prose — needs to become implementation.

**Work Breakdown**:

1. Projection profile YAML configs — 6 named profiles (full, standard, poc, spike, hotfix, minimal) as `v2/config/profiles/*.yml`
2. Vector type support in iterate agent — extend `aisdlc-iterate.md` to handle discovery/spike/PoC convergence criteria
3. Spawning mechanism — `/aisdlc-feature --type spike` or `/aisdlc-spawn` to create child vectors with fold-back tracking
4. Fold-back mechanism — child vector outputs update parent's Context[] and unblock
5. Time-boxing support — `time_box` field in feature vector template, check-in cadence, expiry handling
6. "10-minute build" projection — simplest useful projection (intent → code, agent evaluator only). Prove it works.

**Acceptance Criteria**:
- [ ] At least 3 projection profile YAMLs pass validation
- [ ] Iterate agent handles discovery vector convergence (question_answered)
- [ ] Time-box field in feature vector template
- [ ] End-to-end: spawn a spike from a feature, fold back results

---

## Task #33: Dogfood on Real Project

**Priority**: High
**Status**: Not Started
**Release Target**: 2.1

**Description**:
Use `/aisdlc-init` on an actual codebase, run `/aisdlc-iterate` on real edges, validate that the checklist composition and $variable resolution actually work. First real test of v2.1.

**Work Breakdown**:

1. Pick a small real project (or create a test project)
2. Run `/aisdlc-init` — verify scaffolding, auto-detection, project_constraints
3. Create a feature vector for a simple feature
4. Traverse at least 3 edges end-to-end with `/aisdlc-iterate`
5. Verify checklist composition resolves $variables correctly
6. Verify iteration report displays structured pass/fail table
7. Document what works, what breaks, what's missing

---

## Task #36: Automated Traceability Validation

**Priority**: Medium
**Status**: Not Started
**Release Target**: 2.1
**Informed by**: v1.x WU-032 (REQ-TRACE-003), WU-042 (REQ-TOOL-007)

**Description**:
Implement deterministic evaluator checks that automatically validate REQ key coverage. These compose into edge checklists wherever code or test assets are produced.

Two checks:
1. **REQ tag coverage** — grep code files for `Implements: REQ-*`, grep test files for `Validates: REQ-*`, compare against requirements document. Report missing coverage.
2. **Test gap analysis** — for each REQ key in requirements, verify at least one test file references it via `Validates: REQ-*`. Report untested requirements.

Already sketched in `code_tagging.yml` checklist — needs concrete implementation as shell commands with pass criteria.

---

## Task #37: Ecosystem E(t) as Feedback Loop Edge

**Priority**: Low
**Status**: Not Started
**Release Target**: 2.2+
**Informed by**: v1.x Task #12 (Ecosystem E(t) Tracking)

**Description**:
Reframe the v1.x E(t) concept for v2.1. Ecosystem state (dependency versions, cloud APIs, compliance requirements, cost thresholds) is Context[]. Ecosystem *changes* (CVE detected, API deprecated, cost threshold breached) spawn new intents via the feedback loop.

In v2.1 terms:
- E(t) state → a Context[] document (`.ai-workspace/context/ecosystem.yml`)
- Ecosystem change detection → deterministic evaluators on the feedback loop edge
- Eco-Intents (INT-ECO-*) → standard intents spawned from the feedback loop
- Teams that don't need this simply don't include the ecosystem edge in their projection

**Work Breakdown**:
1. Design `ecosystem.yml` schema as a Context[] document
2. Define `ecosystem_monitoring` edge parameterisation (or extend `feedback_loop.yml`)
3. Define Eco-Intent format (INT-ECO-{TYPE}-{SEQ})
4. Sketch deterministic evaluators: dependency scanner, cost monitor, compliance checker
5. This is a natural candidate for the first "optional edge" in a projection profile

---

## Task #34: Propagate Insights Back to Ontology

**Priority**: Low
**Status**: Not Started
**Informed by**: PROJECTIONS_AND_INVARIANTS.md §10.3

**Description**:
Four insights from v2.1 that should propagate to the constraint-emergence ontology repo:
1. Invariants as projection survival criteria (extends #9)
2. Vector type diversity (extends #15)
3. Fold-back as context enrichment (extends #16)
4. Time-boxing as bounded iteration (extends #15)

---

## Backlog (Low Priority)

- **Release management command** — `/aisdlc-release` for framework versioning, changelog, git tagging. Orthogonal to methodology version. (Informed by v1.x Task #13)
- **LLM-specific prompting Context[]** — different LLM families may need different Context[] documents for optimal iterate performance. (Informed by v1.x Task #18 Gemini parity analysis)
- **Homeostasis model** — formalise the running system's self-monitoring as a feedback loop edge with specific evaluator checks. (Informed by v1.x WU-011)

---

## Summary

| Status | Count |
|--------|-------|
| Not Started | 5 |
| In Progress | 0 |
| Backlog | 3 |

**Priority**:
- High: #32 (Projection Profiles), #33 (Dogfood)
- Medium: #36 (Traceability Validation)
- Low: #37 (Ecosystem E(t)), #34 (Ontology Propagation)

**v1.x Closure**: All 6 v1.x tasks (Tasks #12, #13, #14, #18, #26, #30) closed 2026-02-19.
See: `.ai-workspace/tasks/finished/20260219_v1x_task_closure_and_carryforward.md`

---

## Recently Completed

- Task #35: v1.x Task Closure and Carry-Forward Analysis (2026-02-19)
  - Reviewed all 6 active v1.x tasks against v2.1
  - Closed 4 as superseded (#14, #18, #26, #30)
  - Closed 1 as carry-forward (#13 → backlog)
  - Closed 1 as reframe (#12 → Task #37)
  - Identified 6 carry-forward items for v2.1
  - See: `.ai-workspace/tasks/finished/20260219_v1x_task_closure_and_carryforward.md`
- Task #31: v2.1 Asset Graph Model — Spec, Implementation, and Projections (2026-02-19)
  - Rewrote formal system: 4 primitives, 1 operation, asset graph
  - Implemented v2.1 plugin: iterate agent, graph topology, 9 edge configs, 8 commands
  - Added constraint binding: 4-layer checklist composition with $variable resolution
  - Added projections and invariants spec: vector types, spawning, fold-back, time-boxing, profiles
  - 6 commits: 91f29bc → fa438be (all pushed)
  - See: `.ai-workspace/tasks/finished/20260219_v21_asset_graph_model_spec_and_implementation.md`

---

## Recovery Commands

```bash
cat .ai-workspace/tasks/active/ACTIVE_TASKS.md  # This file
git status                                       # Current state
git log --oneline -10                            # Recent commits
```
