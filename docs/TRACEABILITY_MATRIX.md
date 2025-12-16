# Requirements Traceability Matrix

**Project**: ai_sdlc_method
**Version**: 2.1
**Last Updated**: 2025-12-15
**Requirements Document**: [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md)

---

## Executive Summary

**Total Requirements**: 47 (34 Phase 1 + 13 Phase 2)

### Phase Overview

| Phase | Scope | Count | Critical | Target |
|-------|-------|-------|----------|--------|
| **Phase 1** | MVP: Intent → System Test | 34 | 7 | v1.0 |
| **Phase 2** | Ecosystem: Runtime + UAT | 13 | 3 | v2.0 |

### Design Variants

Requirements are platform-agnostic. Design and implementation are per-variant:

| Variant | Platform | Design Location | Status |
|---------|----------|-----------------|--------|
| claude_aisdlc | Claude Code | `docs/design/claude_aisdlc/` | 🚧 Active |
| codex_aisdlc | OpenAI Codex | `docs/design/codex_aisdlc/` | 📋 Planned |
| roo_aisdlc | Roo Code | `docs/design/roo_aisdlc/` | 📋 Planned |
| gemini_aisdlc | Google Gemini | `docs/design/gemini_aisdlc/` | 📋 Planned |
| copilot_aisdlc | GitHub Copilot | `docs/design/copilot_aisdlc/` | 📋 Planned |

---

## Phase 1: MVP Requirements (33)

**Scope**: Given intent → Build code through System Test

| Req ID | Description | Priority | Req | claude |
|--------|-------------|----------|-----|--------|
| **Intent Management** |||||
| REQ-INTENT-001 | Intent Capture | Critical | ✅ | 🚧 |
| **7-Stage Workflow** |||||
| REQ-STAGE-001 | Stage Definitions | Critical | ✅ | ✅ |
| REQ-STAGE-002 | Stage Transitions | High | ✅ | 🚧 |
| REQ-STAGE-003 | Signal Transformation | High | ✅ | 🚧 |
| REQ-STAGE-004 | Bidirectional Feedback | Critical | ✅ | 🚧 |
| **Requirements Stage** |||||
| REQ-REQ-001 | Requirement Key Generation | Critical | ✅ | ✅ |
| REQ-REQ-002 | Requirement Types | High | ✅ | ✅ |
| REQ-REQ-003 | Requirement Refinement | High | ✅ | 🚧 |
| **Design Stage** |||||
| REQ-DES-001 | Component Design | High | ✅ | ✅ |
| REQ-DES-002 | Architecture Decision Records | High | ✅ | ✅ |
| REQ-DES-003 | Design-to-Requirement Traceability | High | ✅ | 🚧 |
| **Tasks Stage** |||||
| REQ-TASK-001 | Work Breakdown | High | ✅ | 🚧 |
| REQ-TASK-003 | Task-to-Requirement Traceability | High | ✅ | 🚧 |
| **Code Stage** |||||
| REQ-CODE-001 | TDD Workflow | Critical | ✅ | ✅ |
| REQ-CODE-002 | Key Principles Enforcement | High | ✅ | ✅ |
| REQ-CODE-003 | Code-to-Requirement Tagging | Critical | ✅ | 🚧 |
| REQ-CODE-004 | Test Coverage | High | ✅ | 🚧 |
| **System Test Stage** |||||
| REQ-SYSTEST-001 | BDD Scenario Creation | High | ✅ | 🚧 |
| REQ-SYSTEST-002 | Integration Test Execution | High | ✅ | 🚧 |
| REQ-SYSTEST-003 | Test-to-Requirement Traceability | High | ✅ | 🚧 |
| **Traceability** |||||
| REQ-TRACE-001 | Full Lifecycle Traceability | Critical | ✅ | 🚧 |
| REQ-TRACE-002 | Requirement Key Propagation | Critical | ✅ | 🚧 |
| **AI Augmentation** |||||
| REQ-AI-001 | AI Assistance Per Stage | High | ✅ | ✅ |
| REQ-AI-002 | Human Accountability | Critical | ✅ | ✅ |
| REQ-AI-003 | Stage-Specific Agent Personas | High | ✅ | ✅ |
| **Tooling Infrastructure** |||||
| REQ-TOOL-001 | Plugin Architecture | High | ✅ | ✅ |
| REQ-TOOL-002 | Developer Workspace | High | ✅ | ✅ |
| REQ-TOOL-003 | Workflow Commands | Medium | ✅ | ✅ |
| REQ-TOOL-005 | Release Management | High | ✅ | 🚧 |
| REQ-TOOL-006 | Framework Updates | Medium | ✅ | ✅ |
| REQ-TOOL-007 | Test Gap Analysis | High | ✅ | ❌ |
| REQ-TOOL-008 | Methodology Hooks | Medium | ✅ | 🚧 |
| REQ-TOOL-009 | Design-Impl Structure | High | ✅ | ❌ |
| REQ-TOOL-010 | Installer Scaffolding | High | ✅ | ❌ |
| REQ-TOOL-011 | Design-Impl Validation | High | ✅ | ❌ |
| REQ-TOOL-012 | Context Snapshot & Recovery | Medium | ✅ | ✅ |

**Phase 1 Summary (claude_aisdlc)**:
- ✅ Complete: 15/34 (44%)
- 🚧 Partial: 15/34 (44%)
- ❌ Not Started: 4/34 (12%)

---

## Phase 2: Ecosystem Requirements (13)

**Scope**: Runtime feedback loop + UAT formalization

| Req ID | Description | Priority | Req | claude |
|--------|-------------|----------|-----|--------|
| **Intent Management** |||||
| REQ-INTENT-002 | Intent Classification | High | ✅ | ❌ |
| REQ-INTENT-003 | Eco-Intent Generation | Medium | ✅ | ❌ |
| **Requirements Stage** |||||
| REQ-REQ-004 | Homeostasis Model Definition | High | ✅ | ❌ |
| **Tasks Stage** |||||
| REQ-TASK-002 | Dependency Tracking | Medium | ✅ | ❌ |
| **UAT Stage** |||||
| REQ-UAT-001 | Business Validation Tests | High | ✅ | ❌ |
| REQ-UAT-002 | Sign-off Workflow | High | ✅ | ❌ |
| **Runtime Feedback** |||||
| REQ-RUNTIME-001 | Telemetry Tagging | High | ✅ | ❌ |
| REQ-RUNTIME-002 | Deviation Detection | High | ✅ | ✅ |
| REQ-RUNTIME-003 | Feedback Loop Closure | Critical | ✅ | ✅ |
| **Traceability** |||||
| REQ-TRACE-003 | Traceability Validation | High | ✅ | ❌ |
| **Tooling Infrastructure** |||||
| REQ-TOOL-004 | Configuration Hierarchy | Medium | ✅ | 🚧 |

**Phase 2 Summary (claude_aisdlc)**:
- ✅ Complete: 2/13 (15%)
- 🚧 Partial: 1/13 (8%)
- ❌ Not Started: 10/13 (77%)

**Note**: REQ-RUNTIME-002/003 implemented early as foundational infrastructure.

---

## Critical Requirements (10)

| Req ID | Name | Phase | claude |
|--------|------|-------|--------|
| REQ-INTENT-001 | Intent Capture | 1 | 🚧 |
| REQ-STAGE-001 | Stage Definitions | 1 | ✅ |
| REQ-STAGE-004 | Bidirectional Feedback | 1 | 🚧 |
| REQ-REQ-001 | Requirement Key Generation | 1 | ✅ |
| REQ-CODE-001 | TDD Workflow | 1 | ✅ |
| REQ-CODE-003 | Code-to-Requirement Tagging | 1 | 🚧 |
| REQ-TRACE-001 | Full Lifecycle Traceability | 1 | 🚧 |
| REQ-TRACE-002 | Requirement Key Propagation | 1 | 🚧 |
| REQ-AI-002 | Human Accountability | 1 | ✅ |
| REQ-RUNTIME-003 | Feedback Loop Closure | 2 | ✅ |

**Critical Summary**: 5/10 Complete, 5/10 Partial

---

## Design Variant: claude_aisdlc

**Platform**: Claude Code
**Design Location**: `docs/design/claude_aisdlc/`
**Implementation Location**: `claude-code/`

### Stage Coverage

| Stage | Coverage | Status |
|-------|----------|--------|
| Requirements | 46/46 | ✅ Complete |
| Design | 46/46 | ✅ Complete |
| Tasks | 46/46 | ✅ Complete |
| Code | 19/46 (41%) | 🚧 In Progress |
| System Test | 7/46 (15%) | 🚧 In Progress |
| UAT | 0/46 | ⏳ Phase 2 |
| Runtime | 0/46 | ⏳ Phase 2 |

### Design Documents

| Document | Requirements |
|----------|--------------|
| AISDLC_IMPLEMENTATION_DESIGN.md | Synthesis |
| INTENT_MANAGEMENT_DESIGN.md | REQ-INTENT-* |
| WORKFLOW_STAGE_DESIGN.md | REQ-STAGE-* |
| REQUIREMENTS_STAGE_DESIGN.md | REQ-REQ-* |
| DESIGN_STAGE_DESIGN.md | REQ-DES-* |
| TASKS_STAGE_DESIGN.md | REQ-TASK-* |
| CODE_STAGE_DESIGN.md | REQ-CODE-* |
| SYSTEM_TEST_STAGE_DESIGN.md | REQ-SYSTEST-* |
| UAT_STAGE_DESIGN.md | REQ-UAT-* |
| RUNTIME_FEEDBACK_DESIGN.md | REQ-RUNTIME-* |
| TRACEABILITY_DESIGN.md | REQ-TRACE-* |
| AI_AUGMENTATION_DESIGN.md | REQ-AI-* |
| ADR-001 through ADR-007 | REQ-TOOL-* |

### Implementation Artifacts

| Artifact | Location | Requirements |
|----------|----------|--------------|
| Agents (7) | `agents/*.md` | REQ-AI-003, REQ-STAGE-001 |
| Commands (8) | `commands/*.md` | REQ-TOOL-003 |
| Skills (42) | `skills/*/SKILL.md` | REQ-AI-001 |
| Stages Config | `config/stages_config.yml` | REQ-STAGE-* |
| Plugin | `.claude-plugin/plugin.json` | REQ-TOOL-001 |
| Workspace | `.ai-workspace/` | REQ-TOOL-002 |
| Runtime Agent | `runtime_feedback/*.py` | REQ-RUNTIME-002, 003 |

### Test Coverage

| Suite | Tests | Requirements |
|-------|-------|--------------|
| Commands | 22 | REQ-TOOL-003 |
| Skills | 19 | REQ-TRACE-002 |
| BDD Steps | 7 | REQ-SYSTEST-001 |
| Installer | 67 | REQ-TOOL-001, 002 |
| Runtime | 3 | REQ-RUNTIME-002, 003 |
| **Total** | **118** | 7 requirements |

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete |
| 🚧 | Partial / In Progress |
| ❌ | Not Started |
| ⏳ | Planned (future phase) |
| 📋 | Design planned |

---

**Owned By**: Requirements Agent (Traceability Hub)
