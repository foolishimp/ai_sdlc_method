# Active Tasks

*Last Updated: 2025-12-16 12:30*

---

## Task #18: Gemini Implementation Parity

**Priority**: High
**Status**: In Progress
**Release Target**: 2.0
**Estimated Time**: 20-30 days
**Dependencies**: Gemini Scaffolding and Initial Design (Task #17)

**Requirements Traceability**:
- REQ-F-PLUGIN-001: Plugin System
- REQ-F-CMD-001: Slash Commands for Workflow
- REQ-NFR-TRACE-001: Requirement Key Tagging Enforcement
- REQ-NFR-REFINE-001: Iterative Refinement via Stage Feedback Loops

**SDLC Stages**: 2 - Design, 4 - Code
**Agents**: All

**Description**:
This master task tracks the work required to bring the `gemini-code` implementation to full functional parity with the `claude-code` reference implementation. This involves a deep prompt engineering effort to adapt all configurations, agent personas, and skills to be optimal for the Gemini family of models, and to implement the Gemini-native architecture defined in ADR-006.

**Work Breakdown**:

1.  **Adapt Core Methodology**: Rewrite agent personas and instructions in `stages_config.yml`.
2.  **Adapt All Skills**: Rewrite all ~41 skill files for Gemini.
3.  **Implement ADR-006**: Transition from the file-based system to the proposed "Blueprints" and "Workflows" architecture.
4.  **Update Tooling**: Adapt installers and project templates for the new architecture.

---

### Component Adaptation Status

| Component | File / Path | Status | Notes |
|---|---|---|---|
| **Core Methodology** | `gemini-code/.../config/stages_config.yml` | **Partially Complete** | Names and co-author updated. Deep prompt rewrite still required for all 7 agents. |
| **Agents** | | | |
| Requirements Agent | `gemini-code/plugins/aisdlc-methodology/config/stages_config.yml` | `Not Started` | Needs full rewrite of responsibilities and instructions. |
| Design Agent | `gemini-code/plugins/aisdlc-methodology/config/stages_config.yml` | `Not Started` | Needs full rewrite of responsibilities and instructions. |
| Tasks Agent | `gemini-code/plugins/aisdlc-methodology/config/stages_config.yml` | `Not Started` | Needs full rewrite of responsibilities and instructions. |
| Code Agent | `gemini-code/plugins/aisdlc-methodology/config/stages_config.yml` | `Not Started` | Needs full rewrite of responsibilities and instructions. |
| System Test Agent | `gemini-code/plugins/aisdlc-methodology/config/stages_config.yml` | `Not Started` | Needs full rewrite of responsibilities and instructions. |
| UAT Agent | `gemini-code/plugins/aisdlc-methodology/config/stages_config.yml` | `Not Started` | Needs full rewrite of responsibilities and instructions. |
| Runtime Feedback Agent | `gemini-code/plugins/aisdlc-methodology/config/stages_config.yml` | `Not Started` | Needs full rewrite of responsibilities and instructions. |
| **Code Skills** | `gemini-code/plugins/code-skills/skills/` | | |
| TDD Red Phase | `tdd/red-phase/SKILL.md` | **Partially Complete** | Initial adaptation done. Needs deeper review. |
| TDD Green Phase| `tdd/green-phase/SKILL.md`| `Not Started` | |
| TDD Refactor Phase|`tdd/refactor-phase/SKILL.md`| `Not Started` | |
| ... (all other skills) | `...` | `Not Started` | ~40 skills require full prompt engineering adaptation. |
| **Design Skills** | `gemini-code/plugins/design-skills/skills/` | `Not Started` | All skills need adaptation. |
| **Requirements Skills**| `gemini-code/plugins/requirements-skills/skills/`| `Not Started` | All skills need adaptation. |
| **Testing Skills**| `gemini-code/plugins/testing-skills/skills/`| `Not Started` | All skills need adaptation. |
| **Runtime Skills**| `gemini-code/plugins/runtime-skills/skills/`| `Not Started` | All skills need adaptation. |
| **Installers** | `gemini-code/installers/` | `Not Started` | Requires complete rewrite to support ADR-006 architecture. |
| **Project Template** | `gemini-code/project-template/` | `Not Started` | Requires update to support ADR-006 architecture. |

---

## Task #14: Implement Codex Command Layer and Installers (MVP)

**Priority**: High
**Status**: Not Started
**Release Target**: 1.0 MVP
**Estimated Time**: 2-3 days
**Dependencies**: Task #15 (plugin metadata for packaging)

**Requirements Traceability**:
- REQ-F-CMD-001: Slash Commands for Workflow (Codex CLI equivalents)
- REQ-F-WORKSPACE-001/002/003: Developer Workspace and Templates
- REQ-NFR-TRACE-001/002: Traceability Enforcement
- REQ-NFR-CONTEXT-001: Persistent Context Across Sessions

**SDLC Stages**: 2 - Design, 4 - Code
**Agents**: Design Agent, Code Agent

**Description**:
Deliver Codex-friendly CLI commands (`codex-sdlc-*`) plus installer scripts to set up `.ai-workspace/`, register commands/personas, and validate traceability, mirroring the Claude installer behavior.

**Current State**:
- No Codex command implementations or personas.
- Installers added as safe stubs (`codex-code/installers/setup_workspace.py`, `setup_commands.py`, `setup_plugins.py`, `validate_traceability.py`).
- Command helpers added: `codex_sdlc_context.py` (non-destructive context loader) and `codex_sdlc_workspace.py` (workspace validator/installer).

**Target State**:
```
codex-sdlc-context, codex-sdlc-workspace, codex-sdlc-checkpoint, codex-sdlc-finish
Setup scripts: setup_workspace.py, setup_commands.py, setup_plugins.py, validate_traceability.py
Persona presets under codex/project-template for 7 stages
Safe/idempotent writes to .ai-workspace/ and docs/TRACEABILITY_MATRIX.md
```

**Acceptance Criteria**:
- [ ] Commands implemented as console scripts callable by Codex (context helper added; more needed).
- [ ] Installers copy/validate `.ai-workspace/` and command/persona configs (currently stubbed).
- [ ] Traceability validator enforces REQ tags and updates matrix entries (currently stubbed).
- [ ] Docs updated to reference Codex commands/installers (aisdlc-methodology README updated with context helper).

**Work Breakdown**:
1. Scaffold Python package with console entrypoints for codex-sdlc-* commands.
2. Port Claude workspace installer behavior to `codex-code/installers/setup_workspace.py`. ✅ stub
3. Add `setup_commands.py`/`setup_plugins.py` and persona presets for the 7 stages. ✅ stubs for installers
4. Add `validate_traceability.py` to check REQ tags and refresh matrix rows. ✅ stub
5. Document usage and align with Codex design ADRs. ✅ (installer README stub status)

---

## Task #13: Repurpose /aisdlc-release for Framework Release Management

**Priority**: Medium
**Status**: Not Started
**Release Target**: 1.0 MVP
**Estimated Time**: 2-3 hours
**Dependencies**: None

**Requirements Traceability**:
- REQ-F-CMD-003: Release Management Command

**SDLC Stages**: 4 - Code
**Agents**: Code Agent

**Description**:
Repurpose the `/aisdlc-release` command from example project deployment (no longer applicable since examples moved to `ai_sdlc_examples` repo) to framework release management.

**Current State**:
- Command deploys framework to `examples/local_projects/` (directory no longer exists)
- Command is orphaned with no valid targets

**Target State**:
```
/aisdlc-release command:
├── Pre-release Validation
│   ├── Check for uncommitted changes
│   ├── Run tests (if any)
│   └── Validate version format
│
├── Version Management
│   ├── Display current version (from latest tag)
│   ├── Prompt for version bump type (major/minor/patch)
│   └── Update version references in codebase
│
├── Changelog Generation
│   ├── Collect commits since last tag
│   ├── Group by type (feat, fix, docs, etc.)
│   └── Generate CHANGELOG entry
│
├── Release Creation
│   ├── Create annotated git tag
│   ├── Generate release summary
│   └── Display next steps (push tag, create GH release)
│
└── Options
    ├── --dry-run (preview without changes)
    ├── --version <ver> (explicit version)
    └── --no-changelog (skip changelog)
```

**Acceptance Criteria**:
- [ ] Validates no uncommitted changes before release
- [ ] Displays current version from latest git tag
- [ ] Supports version bump: major, minor, patch
- [ ] Updates version in marketplace.json
- [ ] Generates changelog from git commits
- [ ] Creates annotated git tag with release notes
- [ ] Provides dry-run mode
- [ ] Generates release summary report

**Work Breakdown**:
1. Remove example project deployment logic
2. Add pre-release validation (git status check)
3. Add version detection (git describe --tags)
4. Add version bump logic (semver)
5. Add changelog generation (git log parsing)
6. Add tag creation (git tag -a)
7. Add release summary output
8. Add command options (--dry-run, --version)
9. Update command documentation

**Example Output**:
```
╔══════════════════════════════════════════════════════════════╗
║           AI SDLC Method Release - v0.2.0                    ║
╚══════════════════════════════════════════════════════════════╝

📦 Current Version: v0.1.4
🆕 New Version: v0.2.0 (minor bump)

✅ Pre-release Checks:
   - No uncommitted changes ✅
   - On main branch ✅

📝 Changelog (since v0.1.4):
   feat: Add release target tracking to requirements
   feat: Repurpose release command for framework releases
   fix: Update traceability matrix format
   docs: Move examples to separate repo

🏷️  Creating tag: v0.2.0
   git tag -a v0.2.0 -m "Release v0.2.0 - Release management"

📝 Next Steps:
   1. Review changes: git show v0.2.0
   2. Push tag: git push origin v0.2.0
   3. Create GitHub release (optional)
```

**Notes**:
- Examples moved to https://github.com/foolishimp/ai_sdlc_examples
- Original command logic preserved in git history
- Implements REQ-F-CMD-003

---

## Task #12: Incorporate Ecosystem E(t) Tracking and Management

**Priority**: Medium
**Status**: Not Started (Planned for v1.5)
**Release Target**: 1.5 (Beyond MVP)
**Estimated Time**: 4-6 weeks
**Dependencies**: MVP v1.0 complete
**Feature Flag**: ecosystem-tracking

**Requirements Traceability**:
- REQ-F-ECO-001: Ecosystem Constraint Vector E(t) Tracking (NEW - v1.5)
- REQ-F-ECO-002: Eco-Intent Generation (NEW - v1.5)
- REQ-F-ECO-003: ADR Integration with E(t) Context (NEW - v1.5)
- REQ-NFR-ECO-001: Ecosystem Change Detection (NEW - v1.5)

**SDLC Stages**: 1 - Requirements, 7 - Runtime Feedback
**Agents**: Requirements Agent, Runtime Feedback Agent

**Description**:
Implement comprehensive ecosystem tracking and management as described in Section 3.6 of AI_SDLC_REQUIREMENTS.md. The ecosystem E(t) represents the external operating environment - the totality of constraints, capabilities, and resources available at time t.

**Current State** (MVP 1.0):
- E(t) concept documented in requirements specification
- Manual acknowledgment of ecosystem constraints in ADRs
- No automated tracking or change detection
- No Eco-Intent generation

**Target State** (v1.5):
```
E(t) System Components:
├── Ecosystem Tracker
│   ├── runtime_platforms(t)     # Python, Node, Java versions
│   ├── cloud_providers(t)       # AWS, GCP, Azure APIs
│   ├── available_apis(t)        # OpenAI, Stripe, Auth0, etc.
│   ├── library_ecosystems(t)    # npm, PyPI, Maven registries
│   ├── compliance_reqs(t)       # GDPR, HIPAA, SOC2 changes
│   ├── cost_landscape(t)        # Pricing models, thresholds
│   └── team_capabilities(t)     # Skills, experience matrix
│
├── Change Detector
│   ├── Security scanners        # Dependabot, npm audit, Snyk
│   ├── Deprecation monitors     # AWS Trusted Advisor, GitHub
│   ├── Version trackers         # GitHub releases, changelog feeds
│   ├── Cost monitors            # Cloud cost alerts, thresholds
│   └── Compliance trackers      # Regulatory change feeds
│
├── Eco-Intent Generator
│   ├── Security vulnerabilities → INT-ECO-SEC-{n}
│   ├── Deprecation notices     → INT-ECO-DEP-{n}
│   ├── Version updates         → INT-ECO-VER-{n}
│   ├── Cost overruns           → INT-ECO-COST-{n}
│   └── Compliance changes      → INT-ECO-COMP-{n}
│
└── ADR Context Injection
    └── Auto-populate E(t) constraints in ADR templates
```

**Key Features**:

1. **Ecosystem State Capture**
   - Snapshot E(t) at project start and major milestones
   - Track changes over time: E(t₀) → E(t₁) → E(t₂)
   - Store in project context (config/ecosystem.yml)

2. **Automated Change Detection**
   - Integrate with Dependabot for dependency vulnerabilities
   - Monitor cloud provider deprecation notices
   - Track API version changes and breaking changes
   - Alert on cost threshold breaches
   - Monitor compliance requirement updates

3. **Eco-Intent Generation**
   - Automatically generate intents when E(t) changes
   - Priority based on impact (security → high, enhancement → low)
   - Feed into normal SDLC flow via Intent Manager

4. **ADR E(t) Context**
   - ADR templates pre-populated with current E(t) state
   - Decisions explicitly linked to ecosystem constraints
   - Traceability: Decision → E(t) state → Rationale

5. **Stage Integration**
   - Requirements: Check feasibility against E(t)
   - Design: ADRs acknowledge E(t) constraints
   - Tasks: Estimation considers ecosystem solutions
   - Code: Library/API contracts from E(t)
   - System Test: Environment constraints from E(t)
   - UAT: Third-party availability considerations
   - Runtime: SLA bounded by weakest E(t) dependency

**Acceptance Criteria**:
- [ ] REQ-F-ECO-001: Ecosystem state captured in config/ecosystem.yml
- [ ] REQ-F-ECO-002: Eco-Intents auto-generated from E(t) changes
- [ ] REQ-F-ECO-003: ADR templates include E(t) context section
- [ ] REQ-NFR-ECO-001: Change detection via Dependabot, npm audit, AWS TA
- [ ] Ecosystem dashboard shows current E(t) state
- [ ] Historical E(t) tracking (snapshots over time)
- [ ] Eco-Intent priority mapping (security=critical, version=low)
- [ ] Integration tests for change detection
- [ ] Documentation: E(t) tracking guide
- [ ] Example project with E(t) tracking enabled

**Work Breakdown**:
1. **Requirements Phase** (Week 1)
   - Create REQ-F-ECO-001, 002, 003
   - Create REQ-NFR-ECO-001
   - Define E(t) schema (ecosystem.yml format)
   - Define Eco-Intent format (INT-ECO-*)

2. **Design Phase** (Week 2)
   - Design Ecosystem Tracker component
   - Design Change Detector integrations
   - Design Eco-Intent Generator
   - Create ADR-006: Ecosystem Tracking Architecture
   - Update Design Agent with E(t) awareness

3. **Implementation Phase** (Weeks 3-4)
   - Implement ecosystem.yml schema and loader
   - Implement change detection (Dependabot, npm audit)
   - Implement Eco-Intent generation logic
   - Update ADR templates with E(t) section
   - Update Requirements Agent with E(t) feasibility checks

4. **Testing Phase** (Week 5)
   - Unit tests for E(t) tracking
   - Integration tests for change detection
   - End-to-end test: E(t) change → Eco-Intent → SDLC cycle
   - BDD scenarios for Eco-Intent workflow

5. **Documentation Phase** (Week 6)
   - User guide: Setting up E(t) tracking
   - Developer guide: Adding new E(t) monitors
   - Example project with E(t) tracking
   - Update ai_sdlc_method.md with implementation details

**Example Eco-Intent Flow**:
```
1. Dependabot detects: lodash 4.17.19 → CVE-2021-23337
   ↓
2. Change Detector generates: INT-ECO-SEC-001
   Intent: "Upgrade lodash to 4.17.21 (CVE-2021-23337)"
   Priority: Critical
   E(t) context: { vulnerability: CVE-2021-23337, current: 4.17.19, target: 4.17.21 }
   ↓
3. Requirements Agent creates: REQ-F-SEC-001
   "Update lodash dependency to 4.17.21 to address CVE-2021-23337"
   Release: 1.5.1 (hotfix)
   ↓
4. Normal SDLC flow: Design → Tasks → Code → Test → Deploy
   ↓
5. Runtime validates: E(t) updated, vulnerability resolved
```

**Notes**:
- E(t) tracking is conceptually complete in requirements doc (Section 3.6)
- Implementation deferred to v1.5 (beyond MVP scope)
- Builds on existing feedback loop architecture (REQ-NFR-REFINE-001)
- Complements Runtime Feedback Agent (Stage 7)
- Key differentiator: Proactive ecosystem monitoring vs reactive incident response

**Rationale**:
- ✅ Closes the loop from external ecosystem back to requirements
- ✅ Automates detection of security, deprecation, compliance changes
- ✅ Makes E(t) constraints explicit in architectural decisions
- ✅ Enables proactive maintenance (not just reactive)
- ✅ Provides "reality check" at every stage

**References**:
- docs/requirements/AI_SDLC_REQUIREMENTS.md Section 3.6 (E(t) definition)
- docs/requirements/AI_SDLC_REQUIREMENTS.md Section 10.2.2 (Eco-Intents)
- docs/requirements/AI_SDLC_REQUIREMENTS.md Section 5.2.1 (ADRs)

---

## Task #26: Claude-AISDLC Code Implementation (Complete Design → Code)

**Priority**: High
**Status**: Not Started
**Release Target**: 1.0 MVP
**Estimated Time**: 5-10 days
**Dependencies**: Task #25 (Design Coverage - COMPLETE)

**Requirements Traceability**:
- All 43 requirements in AISDLC_IMPLEMENTATION_REQUIREMENTS.md
- See: [TRACEABILITY_MATRIX.md](../../../docs/TRACEABILITY_MATRIX.md)

**SDLC Stages**: 3 - Tasks, 4 - Code
**Agent**: Tasks Agent → Code Agent

**Description**:
This task tracks all code development required to implement the claude-aisdlc design. The design stage is 100% complete (43/43 requirements). This task creates the formal work breakdown to move from Design → Code → System Test.

**Current State**:
- Requirements: 46/46 (100%) ✅ (now phased: 33 Phase 1, 13 Phase 2)
- Design: 46/46 (100%) ✅
- Tasks: 46/46 (100%) ✅
- Code (claude): 16/46 (35%) 🚧
- System Test (claude): 7/46 (15%) 🚧

**Target State**:
- Code (claude): 33/33 Phase 1 (100%) ✅
- System Test (claude): 33/33 Phase 1 (100%) ✅
- Phase 2 deferred to v2.0

---

### Work Breakdown Table

| ID | Requirement | Description | Design Doc | Priority | Status | Code Artifact |
|----|-------------|-------------|------------|----------|--------|---------------|
| **Intent Management** |
| WU-001 | REQ-INTENT-001 | Intent Capture (INTENT.md format) | INTENT_MANAGEMENT_DESIGN.md | Medium | Not Started | `skills/intent-capture/` |
| WU-002 | REQ-INTENT-002 | Intent Classification (INT-* types) | INTENT_MANAGEMENT_DESIGN.md | Medium | Not Started | `skills/intent-classification/` |
| WU-003 | REQ-INTENT-003 | Eco-Intent Generation (E(t) → INT-ECO-*) | INTENT_MANAGEMENT_DESIGN.md | Low | Not Started | `skills/eco-intent/` |
| **7-Stage Workflow** |
| WU-004 | REQ-STAGE-001 | Stage Definitions (7 stages) | WORKFLOW_STAGE_DESIGN.md | Critical | ✅ Complete | `config/stages_config.yml` |
| WU-005 | REQ-STAGE-002 | Stage Transitions (gate validation) | WORKFLOW_STAGE_DESIGN.md | High | Partial | `commands/aisdlc-status.md` |
| WU-006 | REQ-STAGE-003 | Signal Transformation (I/O mappings) | WORKFLOW_STAGE_DESIGN.md | Medium | Not Started | `skills/signal-transform/` |
| WU-007 | REQ-STAGE-004 | Bidirectional Feedback (loops) | WORKFLOW_STAGE_DESIGN.md | Critical | Partial | `agents/*/feedback_protocol` |
| **Requirements Stage** |
| WU-008 | REQ-REQ-001 | Requirement Key Generation (REQ-*) | REQUIREMENTS_STAGE_DESIGN.md | Critical | ✅ Complete | `skills/requirements/` |
| WU-009 | REQ-REQ-002 | Requirement Types (F/NFR/DATA/BR) | REQUIREMENTS_STAGE_DESIGN.md | High | ✅ Complete | `skills/requirement-extraction/` |
| WU-010 | REQ-REQ-003 | Requirement Refinement (versioning) | REQUIREMENTS_STAGE_DESIGN.md | Medium | Not Started | `skills/refine-requirements/` |
| WU-011 | REQ-REQ-004 | Homeostasis Model Definition | REQUIREMENTS_STAGE_DESIGN.md | Low | Not Started | `docs/HOMEOSTASIS_MODEL.md` |
| **Design Stage** |
| WU-012 | REQ-DES-001 | Component Design (diagrams) | DESIGN_STAGE_DESIGN.md | High | ✅ Complete | 11 design docs |
| WU-013 | REQ-DES-002 | ADR Creation (decisions) | DESIGN_STAGE_DESIGN.md | High | ✅ Complete | 7 ADRs |
| WU-014 | REQ-DES-003 | Design-Requirement Traceability | DESIGN_STAGE_DESIGN.md | High | Partial | `skills/design-with-traceability/` |
| **Tasks Stage** |
| WU-015 | REQ-TASK-001 | Work Breakdown (WU-* items) | TASKS_STAGE_DESIGN.md | High | Partial | This table |
| WU-016 | REQ-TASK-002 | Dependency Tracking (DAG) | TASKS_STAGE_DESIGN.md | Medium | Not Started | `docs/DEPENDENCY_GRAPH.md` |
| WU-017 | REQ-TASK-003 | Task-Requirement Traceability | TASKS_STAGE_DESIGN.md | High | Partial | TRACEABILITY_MATRIX.md |
| **Code Stage** |
| WU-018 | REQ-CODE-001 | TDD Workflow (RED→GREEN→REFACTOR) | CODE_STAGE_DESIGN.md | Critical | ✅ Complete | `skills-consolidated/tdd-complete-workflow.md` |
| WU-019 | REQ-CODE-002 | Key Principles Enforcement | CODE_STAGE_DESIGN.md | High | ✅ Complete | `skills-consolidated/key-principles.md` |
| WU-020 | REQ-CODE-003 | Code-Requirement Tagging | CODE_STAGE_DESIGN.md | Critical | Partial | `hooks/hooks.json` (PreToolUse) |
| WU-021 | REQ-CODE-004 | Test Coverage (≥80%) | CODE_STAGE_DESIGN.md | High | Partial | `skills-consolidated/test-coverage-management.md` |
| **System Test Stage** |
| WU-022 | REQ-SYSTEST-001 | BDD Scenario Creation | SYSTEM_TEST_STAGE_DESIGN.md | High | Partial | `tests/features/*.feature` |
| WU-023 | REQ-SYSTEST-002 | Integration Test Execution | SYSTEM_TEST_STAGE_DESIGN.md | High | Partial | `tests/features/steps/` |
| WU-024 | REQ-SYSTEST-003 | Test-Requirement Traceability | SYSTEM_TEST_STAGE_DESIGN.md | High | Not Started | `tests/specs/TCS-*.md` |
| **UAT Stage** |
| WU-025 | REQ-UAT-001 | Business Validation Tests | UAT_STAGE_DESIGN.md | Medium | Not Started | `tests/uat/` |
| WU-026 | REQ-UAT-002 | Sign-off Workflow | UAT_STAGE_DESIGN.md | Medium | Not Started | `commands/aisdlc-signoff.md` |
| **Runtime Feedback** |
| WU-027 | REQ-RUNTIME-001 | Telemetry Tagging | RUNTIME_FEEDBACK_DESIGN.md | Low | Not Started | `skills-consolidated/runtime-observability.md` |
| WU-028 | REQ-RUNTIME-002 | Deviation Detection | RUNTIME_FEEDBACK_DESIGN.md | Low | Not Started | `skills/trace-production-issue/` |
| WU-029 | REQ-RUNTIME-003 | Feedback Loop Closure | RUNTIME_FEEDBACK_DESIGN.md | Critical | ✅ Complete | `agents/aisdlc-runtime-feedback-agent.md` |
| **Traceability** |
| WU-030 | REQ-TRACE-001 | Full Lifecycle Traceability | TRACEABILITY_DESIGN.md | Critical | Partial | TRACEABILITY_MATRIX.md |
| WU-031 | REQ-TRACE-002 | Requirement Key Propagation | TRACEABILITY_DESIGN.md | Critical | Partial | `installers/validate_traceability.py` |
| WU-032 | REQ-TRACE-003 | Traceability Validation (automated) | TRACEABILITY_DESIGN.md | High | Not Started | `installers/validate_traceability.py` |
| **AI Augmentation** |
| WU-033 | REQ-AI-001 | AI Assistance Per Stage | AI_AUGMENTATION_DESIGN.md | High | ✅ Complete | 42 skills |
| WU-034 | REQ-AI-002 | Human Accountability | AI_AUGMENTATION_DESIGN.md | Critical | ✅ Complete | Agent design |
| WU-035 | REQ-AI-003 | Stage-Specific Agent Personas | AI_AUGMENTATION_DESIGN.md | Critical | ✅ Complete | 7 agents |
| **Tooling Infrastructure** |
| WU-036 | REQ-TOOL-001 | Plugin Architecture | ADR-006 | Critical | ✅ Complete | `aisdlc-methodology/` |
| WU-037 | REQ-TOOL-002 | Developer Workspace | ADR-002 | Critical | ✅ Complete | `.ai-workspace/` |
| WU-038 | REQ-TOOL-003 | Workflow Commands | ADR-002 | Critical | ✅ Complete | 10 commands |
| WU-039 | REQ-TOOL-004 | Configuration Hierarchy | ADR-006 | High | Partial | `config/config.yml` |
| WU-040 | REQ-TOOL-005 | Release Management | AISDLC_IMPL_DESIGN.md | Medium | Partial | `commands/aisdlc-release.md` |
| WU-041 | REQ-TOOL-006 | Framework Updates | AISDLC_IMPL_DESIGN.md | Medium | ✅ Complete | `commands/aisdlc-update.md` |
| WU-042 | REQ-TOOL-007 | Test Gap Analysis | SYSTEM_TEST_STAGE_DESIGN.md | High | Not Started | `installers/validate_traceability.py` |
| WU-043 | REQ-TOOL-008 | Methodology Hooks | ADR-007 | Medium | Partial | `hooks/hooks.json` |

---

### Work Unit Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Complete | 16 | 35% |
| 🚧 Partial | 15 | 33% |
| ❌ Not Started | 15 | 33% |
| **Total** | **46** | 100% |

### Phase Breakdown

| Phase | Scope | Requirements | Critical | Target |
|-------|-------|--------------|----------|--------|
| **Phase 1** | MVP: Intent → System Test | 33 | 7 | v1.0 |
| **Phase 2** | Ecosystem: Runtime + UAT | 13 | 3 | v2.0 |

### Priority Breakdown

| Priority | Complete | Partial | Not Started | Total |
|----------|----------|---------|-------------|-------|
| Critical | 8 | 4 | 0 | 12 |
| High | 6 | 7 | 3 | 16 |
| Medium | 2 | 4 | 6 | 12 |
| Low | 0 | 0 | 6 | 6 |

### Next Actions (Priority Order - Phase 1 Focus)

1. **REQ-TRACE-003** (High, Not Started) - Automated traceability validation
2. **REQ-SYSTEST-003** (High, Not Started) - Test-requirement traceability
3. **REQ-TOOL-007** (High, Not Started) - Test gap analysis
4. **REQ-TOOL-009** (High, Not Started) - Design-Impl structure validation
5. **REQ-TOOL-010** (High, Not Started) - Installer scaffolding

**Acceptance Criteria**:
- [ ] All 43 work units have status tracked
- [ ] Tasks column in TRACEABILITY_MATRIX.md updated to ✅
- [ ] Code coverage moves from 35% → 80%+
- [ ] System Test coverage moves from 12% → 80%+
- [ ] All Critical requirements complete

---

## Summary

**Total Active Tasks**: 5
- High Priority: 3
- Medium Priority: 2
- Not Started: 4
  - Task #26: Claude-AISDLC Code Implementation (1.0 MVP) - HIGH ← NEW
  - Task #14: Implement Codex Command Layer and Installers (1.0 MVP) - HIGH
  - Task #13: Repurpose /aisdlc-release for Release Management (1.0 MVP) - MEDIUM
  - Task #12: Ecosystem E(t) Tracking (v1.5 - planned) - MEDIUM
- In Progress: 1
  - Task #18: Gemini Implementation Parity (2.0) - HIGH

**Recently Completed**:
- ✅ Task #29: Phase Breakdown and Traceability Matrix Cleanup (2025-12-16 12:30)
  - Added Phase markers (1 or 2) to all 46 requirements
  - Phase 1: 33 requirements (MVP: Intent → System Test)
  - Phase 2: 13 requirements (Ecosystem: Runtime + UAT)
  - Completely restructured TRACEABILITY_MATRIX.md (430 → 220 lines)
  - Added Design Variants table (claude_aisdlc active, others planned)
  - Split matrix into Phase 1 and Phase 2 sections
  - Removed accumulated cruft (old mapping tables, review notes)
  - Implements: REQ-TRACE-001, REQ-TRACE-002, REQ-REQ-001
  - See: `.ai-workspace/tasks/finished/20251216_1200_phase_breakdown_and_traceability_cleanup.md`
- ✅ Task #28: Implement Requirement Versioning Convention (2025-12-10 12:00)
  - Added version suffix to all 43 requirements (`.0.1.0` baseline)
  - Added versioning convention documentation to requirements file
  - Format: `REQ-{TYPE}-{DOMAIN}-{SEQ}.{MAJOR}.{MINOR}.{PATCH}`
  - Made REQ-REQ-001 self-reflexive (bumped to `.0.2.0`)
  - Version aligns with git tags (`.0.1.0` ↔ `v0.1.0`)
  - "By exception" approach - no version = current requirement
  - Implements: REQ-REQ-001.0.2.0
  - See: `.ai-workspace/tasks/finished/20251210_1200_requirement_versioning_convention.md`
- ✅ Task #27: Mandatory Artifacts + Init Command + Status/Help Improvements (2025-12-04 17:30)
  - Added `mandatory_artifacts` section to stages_config.yml (v0.4.9)
  - Added `artifact_traceability_chain` showing full INT→REQ→Design→Code→Test→UAT→Runtime flow
  - Created `/aisdlc-version` command to display plugin version
  - Created `/aisdlc-init` command for corporate/manual workspace setup
  - Updated QUICKSTART.md with manual installation options (3 methods)
  - Updated `/aisdlc-status` with intelligent next-step suggestions
  - Updated `/aisdlc-help` with Getting Started flowchart
  - Updated TRACEABILITY_MATRIX.md - Tasks stage now 100% complete
  - Commands: 8 → 10 (added /aisdlc-version, /aisdlc-init)
  - Implements: REQ-TRACE-001, REQ-TRACE-002, REQ-TOOL-002, REQ-TOOL-003, REQ-TOOL-005
  - Commits: 4257e03, 0ad77c8, c5266cc, fafe220, 46456a9
- ✅ Task #25: Complete Design Coverage + Skills Consolidation (2025-12-03 03:00)
  - Rewrote AISDLC_IMPLEMENTATION_REQUIREMENTS.md (19 → 43 requirements)
  - Created 11 new design documents (100% design coverage)
  - Consolidated 42 skills → 11 comprehensive workflows
  - Updated TRACEABILITY_MATRIX.md with 7-stage tracking
  - Updated all 7 ADRs with new REQ-* keys
  - Moved test specs to claude-code/tests/specs/
  - Implements: REQ-DES-001, REQ-DES-002, REQ-DES-003
  - See: commit 858549a
- ✅ Task #24: Update docs/guides to Match Current Reality (2025-12-02 15:00)
  - Updated README.md, PLUGIN_GUIDE.md, NEW_PROJECT_SETUP.md, JOURNEY.md
  - Fixed plugin paths, installation method (curl one-liner), commands
  - Removed hardcoded line counts (maintenance burden)
  - Implements: REQ-F-WORKSPACE-002, REQ-NFR-CONTEXT-001
  - See: `.ai-workspace/tasks/finished/20251202_1500_update_docs_guides_to_match_reality.md`
- ✅ Task #23: Fix GitHub Marketplace Plugin Loading (2025-12-02 12:00)
  - Fixed plugin source path resolution (paths relative to repo root, not .claude-plugin/)
  - Created test plugin (`testmkt/plugins/hello-world/`) to validate structure
  - Both `hello-world@aisdlc` and `aisdlc-methodology@aisdlc` now load from GitHub
  - Documented cache clearing procedure (`~/.claude/plugins/marketplaces/`)
  - Verified `aisdlc-setup.py` generates correct bootstrap settings.json
  - Implements: REQ-F-PLUGIN-001
  - See: `.ai-workspace/tasks/finished/20251202_fix_github_marketplace_plugin_loading.md`
- ✅ Task #22: Simplify Installer to Single-Plugin Model (2025-11-27 17:15)
  - Simplified `aisdlc-setup.py`: removed bundles, 9-plugin selection → single `aisdlc-methodology`
  - Removed redundant files: `setup_settings.py`, `setup_hooks.py`, `common.py`, `tests/`
  - Updated `plugins/.claude-plugin/marketplace.json`: 8 entries → 1 entry
  - Updated `installers/README.md` and `QUICKSTART.md`
  - Dogfooded: added `.claude/settings.json` to this project
  - Released v0.4.2 and pushed to GitHub
  - Implements: REQ-F-PLUGIN-001
- ✅ Task #21: Consolidate All Skills into aisdlc-methodology Plugin (2025-11-27 16:40)
  - Consolidated 7 separate plugins + 4 bundles into single aisdlc-methodology (v4.0.0)
  - Moved 42 skills into `skills/` directory (core, principles, requirements, design, code, testing, runtime)
  - Removed aisdlc-core, principles-key, all *-skills plugins, and bundles/
  - Updated marketplace.json: 11 entries → 1 entry, no dependencies
  - Implements: REQ-F-PLUGIN-001, REQ-F-PLUGIN-002
  - See: `.ai-workspace/tasks/finished/20251127_1640_consolidate_skills_into_aisdlc_methodology.md`
- ✅ Task #20: Design and Implement Hooks System for Methodology Automation (2025-11-27 14:00)
  - Created HOOKS_SYSTEM.md design document (~370 lines) with 5 design principles
  - Created 4 lifecycle hooks in `claude-code/plugins/aisdlc-methodology/hooks/settings.json`
  - Created ADR-007 (Hooks for Methodology Automation)
  - Created setup_hooks.py installer (400 lines) following InstallerBase pattern
  - Deleted orphaned `.claude/settings.json` from v0.1.0
  - Implements: REQ-F-HOOKS-001 (NEW), REQ-NFR-CONTEXT-001
  - See: `.ai-workspace/tasks/finished/20251127_1400_hooks_system_design_implementation.md`
- ✅ Task #3: Complete Design Documentation for Command System (2025-11-27 12:00)
  - Created comprehensive COMMAND_SYSTEM.md (~300 lines) in docs/design/claude_aisdlc/
  - Documented all 7 v0.4 commands with decision rationale
  - Documented 9 removed commands with removal rationale
  - Established 5 design principles for command system
  - Updated ADR-002 to reflect v0.4 state
  - Implements: REQ-F-CMD-001
  - See: `.ai-workspace/tasks/finished/20251127_1200_command_system_design_documentation.md`
- ✅ Task #19: Fix Claude Code Plugin Configuration (2025-11-27 10:00)
  - Created `claude-code/plugins/.claude-plugin/marketplace.json` (was missing)
  - Fixed 8 plugin.json files (invalid schema: author, agents, invalid fields)
  - Updated 5 documentation files (QUICKSTART, README, JOURNEY, plugins README, installers README)
  - Plugins now load correctly: `/plugin` shows all 3 core plugins as "Installed"
  - Key learnings documented: marketplace.json required, plugin.json schema rules
  - Implements: REQ-F-PLUGIN-001, REQ-F-PLUGIN-002
  - See: `.ai-workspace/tasks/finished/20251127_fix_claude_code_plugin_configuration.md`
- ✅ Task #18: Implement Roo Code Installers - Full Suite (2025-11-26 14:00)
  - Created complete installer suite mirroring Claude Code pattern (10 Python files)
  - `common.py`, `setup_modes.py`, `setup_rules.py`, `setup_memory_bank.py`, `setup_workspace.py`
  - `setup_all.py`, `setup_reset.py`, `aisdlc-reset.py` (curl-friendly)
  - 36 unit tests (100% passing): `test_common.py`, `test_setup_reset.py`
  - Comprehensive README.md documentation (389 lines)
  - Implements: REQ-F-PLUGIN-001, REQ-F-WORKSPACE-001/002
  - See: `.ai-workspace/tasks/finished/20251126_1400_roo_code_installers_implementation.md`
- ✅ Task #15: Ship Codex Plugin Packaging and Marketplace Entries (2025-11-26 12:00)
  - Added `.codex-plugin/plugin.json` metadata for all Codex plugins/bundles with SemVer/deps
  - Updated `marketplace.json` with Codex entries (provider openai, Codex-suffixed names)
  - Documented discovery, federated loading, and parity in `codex-code/plugins/README.md`
  - Implements: REQ-F-PLUGIN-001/002/003/004
- ✅ Task #17: Design and Scaffold Gemini AISDLC Implementation (2025-11-26 00:00)
  - See: `.ai-workspace/tasks/finished/20251125_2353_design_and_scaffold_gemini_aisdlc.md`
- ✅ Task #15: Create Roo Code AISDLC Solution (roo-code-iclaude) (2025-11-25 15:45)
  - Created complete `roo-code-iclaude/` directory matching Claude/Codex quality
  - Design docs: `docs/design/roo_aisdlc/` with 370+ line implementation design
  - 4 ADRs: ADR-201 (Custom Modes), ADR-202 (Rules Library), ADR-203 (Memory Bank), ADR-204 (Workspace Safeguards)
  - 7 mode JSON files (one per SDLC stage)
  - 6 rule markdown files (key-principles, tdd-workflow, bdd-workflow, req-tagging, feedback-protocol, workspace-safeguards)
  - 4 memory bank templates (projectbrief, techstack, activecontext, methodref)
  - Created `ROOCODE.md` guidance file (equivalent to CODEX.md)
  - Updated `CODEX.md` to reference `codex_aisdlc`
  - Removed redundant `implementations/` folders from design directories
  - Implements: REQ-F-PLUGIN-001, REQ-F-CMD-002, REQ-NFR-CONTEXT-001, REQ-NFR-TRACE-001
  - See: `.ai-workspace/tasks/finished/20251125_1545_roo_code_aisdlc_solution.md`
- ✅ Task #14: Create Reset-Style Installer for Clean Updates (2025-11-25 14:30)
  - Created `installers/setup_reset.py` - full-featured reset installer
  - Created `installers/aisdlc-reset.py` - self-contained curl-friendly installer
  - Updated `installers/common.py` with version fetching from git tags
  - Updated `installers/setup_all.py` with `--reset` and `--version` options
  - Updated `installers/README.md` with documentation
  - Philosophy: Only immutable framework code replaced, user work preserved
  - Preserves: tasks/active/, tasks/finished/
  - Removes/reinstalls: commands/, agents/, templates/, config/
  - One-liner: `curl -sL .../aisdlc-reset.py | python3 - --version v0.2.0`
  - Implements: REQ-F-RESET-001 (New)
  - See: `.ai-workspace/tasks/finished/20251125_1430_reset_installer_for_clean_updates.md`
- ✅ Task #11: Refactor Directory Structure - Group Claude Code Assets (2025-11-25 12:00)
  - Moved plugins/ → claude-code/plugins/ (9 plugins + 4 bundles, 41 skills)
  - Moved templates/claude/ → claude-code/project-template/
  - Updated marketplace.json with new plugin paths
  - Updated 30+ documentation files with new paths
  - Updated 4 installer scripts
  - Updated all example projects
  - Created claude-code/README.md explaining structure
  - Updated claude-code/project-template/README.md
  - Preserved git history (111 files renamed using git mv)
  - Implements: REQ-F-PLUGIN-001, REQ-F-WORKSPACE-001
  - See: commit db173cd "REFACTOR: Reorganize Claude Code assets under claude-code/ directory"
- ✅ Task #9: Design Synthesis Document (2025-11-25 11:00)
  - Created AISDLC_IMPLEMENTATION_DESIGN.md (560+ lines)
  - Mapped all 17 requirements to design components
  - Referenced all 6 design docs (5,744 lines)
  - Summarized 5 ADRs
  - Created component architecture diagrams
  - Coverage: 71% implemented, 24% partial, 6% planned
  - See: `.ai-workspace/tasks/finished/20251125_1100_design_synthesis_document.md`
- ✅ Task #10: Update All Agents with Feedback Protocol (2025-11-25 03:32)
  - Added explicit feedback protocol to all 7 agents (+ 7 templates)
  - Created REQ-NFR-REFINE-001 (17th requirement)
  - Created ADR-005 (Iterative Refinement Architecture)
  - Demonstrated dogfooding (used feedback pattern to discover and fix requirement gap)
  - See: `.ai-workspace/tasks/finished/20251125_0332_update_agents_feedback_protocol.md`
- ✅ Task #6: Requirements Provenance & Completeness Validation (2025-11-25 03:24)
  - Validated 100% provenance (all 16 requirements → intent sections)
  - Confirmed 100% completeness (all MVP goals covered)
  - Passed all quality gates (unique keys, criteria, testability)
  - Corrected scope creep (MVP vs Year 1)
  - See: `.ai-workspace/tasks/finished/20251125_0324_requirements_provenance_completeness.md`
- ✅ Task #8: Rename Agents with aisdlc- Prefix (2025-11-25 03:18)
  - Renamed 21 agent files (7 main + 7 templates + 7 example)
  - Updated 30+ documentation references across 6 files
  - Achieved 100% namespace consistency (commands + agents + plugins)
  - See: `.ai-workspace/tasks/finished/20251125_0318_rename_agents_aisdlc_prefix.md`
- ✅ Task #7: Remove Vestigial Persona Commands (2025-11-25 03:15)
  - Deleted 8 persona command files (4 main + 4 templates)
  - Updated REQ-F-CMD-002 to show implemented by agents (not commands)
  - Removed persona references from documentation
  - Command count: 10 → 6 (40% reduction, 100% functional)
  - See: `.ai-workspace/tasks/finished/20251125_0310_remove_vestigial_persona_commands.md`

---

## Recovery Commands

If context is lost, run these commands to get back:
```bash
cat .ai-workspace/tasks/active/ACTIVE_TASKS.md  # This file
git status                                       # Current state
git log --oneline -5                            # Recent commits
/aisdlc-status                                   # Task queue status
```
