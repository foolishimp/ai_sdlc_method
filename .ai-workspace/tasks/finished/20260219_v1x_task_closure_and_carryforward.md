# Task: v1.x Task Closure and Carry-Forward Analysis

**Status**: Completed
**Date**: 2026-02-19

**Task ID**: #35
**Purpose**: Review all active v1.x tasks, close what's superseded by v2.1, identify work worth carrying forward.

---

## Context

v2.1 (Asset Graph Model) replaced the v1.x 7-stage pipeline with 4 primitives and 1 universal operation. This fundamentally changes:
- **Agents**: 7 stage-specific agents → 1 universal iterate agent parameterised by edge config
- **Commands**: Stage-centric commands → graph-aware commands
- **Multi-platform**: Per-platform agent rewrites → same configs, different LLM backend
- **Workflow**: Fixed sequential pipeline → directed cyclic graph with projections

---

## Task-by-Task Review

### Task #18: Gemini Implementation Parity — CLOSED (Superseded)

**v1.x scope**: Rewrite all 7 agents + 41 skills for Gemini models. Deep prompt engineering per stage.

**Why superseded**: v2.1 has 1 iterate agent, not 7. Multi-platform parity becomes "can the LLM follow edge configs?" not "rewrite every agent persona." The edge configs (YAML) and iterate agent instructions (markdown) are LLM-agnostic by design.

**Carry-forward**: None specific. The general insight — that different LLMs need different prompting strategies — is valid but should be addressed as Context[] (a "prompting standards" context document per LLM family) rather than per-agent rewrites.

---

### Task #30: Roo Parity Phase 1A — CLOSED (Superseded)

**v1.x scope**: 17 sprint tasks to create Roo-specific modes, rules, installers, memory bank templates for the 7-stage model.

**Why superseded**: Roo's "custom modes" map to v2.1 edge configs, not stage-specific agents. The installer concept (scaffolding a workspace) survives as `/gen-init`. The rule files (REQ tagging, feedback protocol, workspace safeguards) are now edge parameterisations and project constraints.

**Carry-forward**:
- **Workspace safeguards** — the concept of protecting user work during framework updates is orthogonal to methodology version. Worth noting in v2.1 `/gen-init --force` behaviour (already partially addressed).
- **Memory bank pattern** — Roo's persistent context files map to v2.1's `.ai-workspace/context/` directory. Already covered.

---

### Task #26: Claude-AISDLC Code Implementation — CLOSED (Superseded, with carry-forwards)

**v1.x scope**: 43 work units implementing the v1.x design across 7 stages. 16/46 complete, 15 partial, 15 not started.

**Why superseded**: The work breakdown was for v1.x design docs (11 stage-specific design documents). v2.1 implementation (Phase 1a, commit ecced4f) already covers the core engine, and the architecture is fundamentally different.

**Carry-forward — concepts worth exploring in v2.1**:

| v1.x Work Unit | v2.1 Equivalent | Status | Worth Exploring? |
|---------------|-----------------|--------|-----------------|
| WU-001 Intent Capture | `/gen-iterate --edge "intent→requirements"` | Covered by iterate agent | No — already in v2.1 |
| WU-003 Eco-Intent Generation | See Task #12 analysis below | Not covered | **Yes** — as feedback loop edge |
| WU-005 Stage Transitions | Graph topology transitions | Covered | No — v2.1 graph topology |
| WU-007 Bidirectional Feedback | Cyclic graph edges | Covered | No — first-class in v2.1 |
| WU-011 Homeostasis Model | Running system → telemetry → new intent | Partially covered | **Yes** — formalise as v2.1 feedback loop edge config |
| WU-020 Code-Requirement Tagging | `code_tagging.yml` edge config | Covered | No — already in v2.1 |
| WU-030 Full Lifecycle Traceability | Emergent from 4 invariants | Covered | No — addressed in PROJECTIONS_AND_INVARIANTS.md §2.3 |
| WU-032 Traceability Validation (automated) | Deterministic evaluator check | **Not yet implemented** | **Yes** — as a deterministic check in edge configs |
| WU-042 Test Gap Analysis | Deterministic evaluator check | **Not yet implemented** | **Yes** — as a deterministic check |
| WU-043 Methodology Hooks | Claude Code hooks system | Partially covered | **Maybe** — hooks are platform-specific but useful |

**Key carry-forwards for v2.1**:
1. **Automated traceability validation** (WU-032) — implement as a deterministic evaluator that grep-checks REQ tags across code/tests. Already sketched in `code_tagging.yml` checklist.
2. **Test gap analysis** (WU-042) — implement as a deterministic evaluator that compares REQ keys in requirements vs REQ keys in test files.
3. **Homeostasis model** (WU-011) — formalise the running system's self-monitoring as a v2.1 feedback loop edge with specific evaluator checks.

---

### Task #14: Codex Command Layer — CLOSED (Superseded)

**v1.x scope**: Codex-specific CLI commands (`codex-sdlc-*`) and installers for the 7-stage pipeline.

**Why superseded**: v2.1 commands are graph-aware and platform-agnostic. The concept of platform-specific command layers is replaced by the universal iterate agent reading edge configs.

**Carry-forward**: None. The workspace installer concept survives as `/gen-init`.

---

### Task #13: Release Management Command — CLOSED (Carry forward to v2.1)

**v1.x scope**: Repurpose `/gen-release` for framework versioning, changelog generation, git tagging.

**Why not superseded**: Release management is orthogonal to methodology version. You still need to version, tag, and release the framework.

**Carry-forward**: Add to v2.1 backlog as a utility command. The spec from #13 (pre-release validation, version bump, changelog from commits, annotated git tag) is still valid. Low priority — nice-to-have, not blocking.

---

### Task #12: Ecosystem E(t) Tracking — CLOSED (Reframe for v2.1)

**v1.x scope**: 6-week implementation of ecosystem tracking: dependency scanners, deprecation monitors, cost alerts, compliance trackers, auto-generated Eco-Intents.

**Why reframed, not superseded**: E(t) is a genuinely valuable concept. In v2.1 terms:
- **E(t) changes** are detected at the `running_system → telemetry` edge (or a new `ecosystem → telemetry` edge)
- **Eco-Intents** are spawned via the `telemetry → new_intent` feedback edge
- **E(t) state** is Context[] — it's a constraint document like any other
- The **Eco-Intent flow** (Dependabot → INT-ECO-SEC-001 → REQ → Code → Deploy) is a standard feature vector spawned from the feedback loop

**Carry-forward for v2.1**:
1. Add `ecosystem` as an optional asset type in the graph topology (or treat E(t) as a Context[] document that gets periodically refreshed)
2. Define an `ecosystem_change → new_intent` edge parameterisation with deterministic evaluators (dependency scanner, cost monitor, compliance checker)
3. Define Eco-Intent format (INT-ECO-{TYPE}-{SEQ}) as a specialisation of the existing intent format
4. This is a **projection** — a team that doesn't need ecosystem tracking simply doesn't include this edge in their graph

---

## Summary

| Task | Disposition | Carry-Forward |
|------|------------|---------------|
| #18 Gemini Parity | **Closed — Superseded** | LLM-specific prompting as Context[] |
| #30 Roo Parity | **Closed — Superseded** | Workspace safeguards already in v2.1 |
| #26 Claude Code Impl | **Closed — Superseded** | Automated traceability validation, test gap analysis, homeostasis model |
| #14 Codex Commands | **Closed — Superseded** | None |
| #13 Release Management | **Closed — Carry forward** | Add `/gen-release` to v2.1 backlog (low priority) |
| #12 Ecosystem E(t) | **Closed — Reframe** | E(t) as Context[] + feedback loop edge. Valuable concept, needs v2.1 design. |

### Items worth exploring in v2.1 (informed by v1.x):

1. **Automated traceability validation** — deterministic evaluator that checks REQ tag coverage
2. **Test gap analysis** — deterministic evaluator comparing REQ keys in requirements vs tests
3. **Homeostasis model** — formalise as feedback loop edge config
4. **Ecosystem E(t) tracking** — E(t) as Context[], ecosystem changes as feedback loop spawning Eco-Intents
5. **Release management** — `/gen-release` command (orthogonal to methodology, low priority)
6. **LLM-specific prompting** — different LLM families may need different Context[] for optimal iterate performance
