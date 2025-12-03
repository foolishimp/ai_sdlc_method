# AI SDLC Method Implementation Design

**Document Type**: Design Synthesis Document
**Project**: ai_sdlc_method (self-implementation)
**Version**: 3.0
**Date**: 2025-12-03
**Status**: Active

---

## Purpose

This document synthesizes all design artifacts into a **coherent technical solution** that implements the 43 platform-agnostic requirements defined in [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md).

**Meta Note**: We are **dogfooding** - using the AI SDLC methodology to build the AI SDLC methodology tooling.

**Traceability**: For requirement coverage tracking across all SDLC stages, see [TRACEABILITY_MATRIX.md](../TRACEABILITY_MATRIX.md).

---

## Executive Summary

The AI SDLC Method is implemented as a **Claude Code plugin ecosystem** with three core subsystems:

1. **Plugin System** - Modular, composable context delivery to AI assistants
2. **Agent System** - 7-stage SDLC personas with bidirectional feedback loops
3. **Workspace System** - File-based task and session management

**Key Design Decisions**:
- Claude Code as MVP platform (ADR-001)
- Slash commands for workflow integration (ADR-002)
- Agents for stage personas (ADR-003)
- Skills for reusable capabilities (ADR-004)
- Iterative refinement via feedback loops (ADR-005)
- Plugin configuration and discovery (ADR-006)
- Hooks for methodology automation (ADR-007)

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER (Developer)                                │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLAUDE CODE                                      │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    PLUGIN SYSTEM                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │              aisdlc-methodology (v0.4.8)                     │  │   │
│  │  │  ├─ 7 agents    ├─ 11 consolidated skills    ├─ 8 commands  │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    AGENT SYSTEM                                    │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    │   │
│  │  │ Reqmts │→ │ Design │→ │ Tasks  │→ │ Code   │→ │ Test   │    │   │
│  │  │ Agent  │  │ Agent  │  │ Agent  │  │ Agent  │  │ Agents │    │   │
│  │  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘    │   │
│  │      │           │           │           │           │          │   │
│  │      └───────────┴───────────┴───────────┴───────────┘          │   │
│  │                    Bidirectional Feedback Loops                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    COMMAND SYSTEM                                  │   │
│  │  /aisdlc-status  /aisdlc-checkpoint-tasks  /aisdlc-release       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROJECT WORKSPACE                                │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    .ai-workspace/                                  │   │
│  │  ├─ tasks/           (task management)                            │   │
│  │  ├─ templates/       (methodology templates)                      │   │
│  │  └─ config/          (workspace configuration)                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    .claude/                                        │   │
│  │  ├─ agents/          (7 SDLC stage agents)                        │   │
│  │  └─ commands/        (8 workflow commands)                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Overview

| Component | Purpose | Design Document |
|-----------|---------|-----------------|
| Intent Management | Capture and classify intents | [INTENT_MANAGEMENT_DESIGN.md](INTENT_MANAGEMENT_DESIGN.md) |
| 7-Stage Workflow | Stage definitions and transitions | [WORKFLOW_STAGE_DESIGN.md](WORKFLOW_STAGE_DESIGN.md) |
| Requirements Stage | Intent → structured requirements | [REQUIREMENTS_STAGE_DESIGN.md](REQUIREMENTS_STAGE_DESIGN.md) |
| Design Stage | Requirements → technical solution | [DESIGN_STAGE_DESIGN.md](DESIGN_STAGE_DESIGN.md) |
| Tasks Stage | Design → work breakdown | [TASKS_STAGE_DESIGN.md](TASKS_STAGE_DESIGN.md) |
| Code Stage | TDD implementation | [CODE_STAGE_DESIGN.md](CODE_STAGE_DESIGN.md) |
| System Test Stage | BDD integration testing | [SYSTEM_TEST_STAGE_DESIGN.md](SYSTEM_TEST_STAGE_DESIGN.md) |
| UAT Stage | Business validation | [UAT_STAGE_DESIGN.md](UAT_STAGE_DESIGN.md) |
| Runtime Feedback | Production monitoring | [RUNTIME_FEEDBACK_DESIGN.md](RUNTIME_FEEDBACK_DESIGN.md) |
| Traceability | Full lifecycle tracking | [TRACEABILITY_DESIGN.md](TRACEABILITY_DESIGN.md) |
| AI Augmentation | AI assistance patterns | [AI_AUGMENTATION_DESIGN.md](AI_AUGMENTATION_DESIGN.md) |

---

## 2. Component Design

### 2.1 Plugin System

**Requirements**: REQ-TOOL-001, REQ-TOOL-004

**Purpose**: Enable modular, composable context delivery to AI assistants through a plugin architecture with marketplace support.

**Current Structure**:
```
claude-code/.claude-plugin/plugins/
└── aisdlc-methodology/          # Single consolidated plugin (v4.4.0)
    ├── .claude-plugin/
    │   └── plugin.json          # Metadata (name, version)
    ├── config/
    │   ├── config.yml           # Main configuration
    │   └── stages_config.yml    # 7-stage agent specifications
    ├── agents/                  # 7 SDLC stage agents
    ├── commands/                # 8 workflow commands
    ├── skills/                  # 42 granular skills (legacy)
    ├── skills-consolidated/     # 11 comprehensive workflows
    └── docs/                    # Methodology documentation
```

**Key Design Decisions**:
- Single plugin consolidation (was 9 plugins + 4 bundles)
- NPM-style SemVer versioning
- Federated loading (Corporate → Division → Team → Project)

---

### 2.2 Agent System

**Requirements**: REQ-STAGE-001, REQ-AI-003

**Design Document**: [AI_AUGMENTATION_DESIGN.md](AI_AUGMENTATION_DESIGN.md)

**7-Stage Agent Architecture**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          AGENT LAYER                                     │
│                     (.claude/agents/*.md)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Stage 1         Stage 2         Stage 3         Stage 4                │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐         │
│  │ aisdlc-   │   │ aisdlc-   │   │ aisdlc-   │   │ aisdlc-   │         │
│  │ require-  │──▶│ design-   │──▶│ tasks-    │──▶│ code-     │         │
│  │ ments-    │   │ agent     │   │ agent     │   │ agent     │         │
│  │ agent     │   │           │   │           │   │           │         │
│  └─────┬─────┘   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘         │
│        │               │               │               │                │
│        │◀──────────────┴───────────────┴───────────────┘                │
│        │           FEEDBACK LOOPS (REQ-STAGE-004)                       │
│                                                                          │
│  Stage 5         Stage 6         Stage 7                                │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐                          │
│  │ aisdlc-   │   │ aisdlc-   │   │ aisdlc-   │                          │
│  │ system-   │──▶│ uat-      │──▶│ runtime-  │                          │
│  │ test-     │   │ agent     │   │ feedback- │                          │
│  │ agent     │   │           │   │ agent     │                          │
│  └─────┬─────┘   └─────┬─────┘   └─────┬─────┘                          │
│        │               │               │                                 │
│        └───────────────┴───────────────┴──────▶ New Intent              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Agent Files**:
| Agent | File | Stage | Role |
|-------|------|-------|------|
| Requirements | `aisdlc-requirements-agent.md` | 1 | Intent Store & Traceability Hub |
| Design | `aisdlc-design-agent.md` | 2 | Architecture & Data Design |
| Tasks | `aisdlc-tasks-agent.md` | 3 | Work Breakdown & Orchestration |
| Code | `aisdlc-code-agent.md` | 4 | TDD Implementation |
| System Test | `aisdlc-system-test-agent.md` | 5 | BDD Integration Testing |
| UAT | `aisdlc-uat-agent.md` | 6 | Business Validation |
| Runtime Feedback | `aisdlc-runtime-feedback-agent.md` | 7 | Production Monitoring |

---

### 2.3 Skills System

**Requirements**: REQ-AI-001

**Design Document**: [AI_AUGMENTATION_DESIGN.md](AI_AUGMENTATION_DESIGN.md)

**Consolidated Skills** (11 comprehensive workflows):

| Skill | Purpose | Consolidates |
|-------|---------|--------------|
| tdd-complete-workflow | TDD RED→GREEN→REFACTOR | 5 TDD skills |
| bdd-complete-workflow | BDD Given/When/Then | 5 BDD skills |
| requirements-extraction | Intent → REQ-* keys | 6 requirements skills |
| requirements-validation | SMART validation | 2 validation skills |
| design-with-traceability | ADRs + components | 3 design skills |
| code-generation | Generate from BR-*/C-*/F-* | 4 generation skills |
| technical-debt-management | Detect + eliminate debt | 4 debt skills |
| test-coverage-management | Coverage + gap analysis | 5 testing skills |
| runtime-observability | Telemetry + feedback | 3 runtime skills |
| traceability-core | REQ-* propagation | 3 core skills |
| key-principles | 7 principles checklist | 2 principles skills |

**Location**: `claude-code/.claude-plugin/plugins/aisdlc-methodology/skills-consolidated/`

---

### 2.4 Command System

**Requirements**: REQ-TOOL-003

**Commands** (8 total):
| Command | Purpose |
|---------|---------|
| `/aisdlc-status` | Show task queue status |
| `/aisdlc-checkpoint-tasks` | Save work context |
| `/aisdlc-finish-task` | Complete and document task |
| `/aisdlc-commit-task` | Generate commit message |
| `/aisdlc-release` | Create release notes |
| `/aisdlc-refresh-context` | Reload methodology context |
| `/aisdlc-update` | Check for framework updates |
| `/aisdlc-help` | Show available commands and usage |

**Location**: `.claude/commands/*.md`

---

### 2.5 Workspace System

**Requirements**: REQ-TOOL-002

**Workspace Structure**:
```
.ai-workspace/
├── config/
│   └── workspace_config.yml      # Configuration
├── tasks/
│   ├── active/
│   │   └── ACTIVE_TASKS.md       # Current tasks
│   ├── finished/                 # Completed docs
│   │   └── YYYYMMDD_HHMM_*.md
│   └── archive/                  # Old tasks
└── templates/
    ├── TASK_TEMPLATE.md
    ├── FINISHED_TASK_TEMPLATE.md
    └── AISDLC_METHOD_REFERENCE.md
```

---

### 2.6 Traceability System

**Requirements**: REQ-TRACE-001, REQ-TRACE-002, REQ-TRACE-003

**Design Document**: [TRACEABILITY_DESIGN.md](TRACEABILITY_DESIGN.md)

**Requirement Key Format**:
```
REQ-{CATEGORY}-{SEQ}

Categories:
- INTENT    = Intent Management
- STAGE     = 7-Stage Workflow
- REQ       = Requirements Stage
- DES       = Design Stage
- TASK      = Tasks Stage
- CODE      = Code Stage
- SYSTEST   = System Test Stage
- UAT       = UAT Stage
- RUNTIME   = Runtime Feedback
- TRACE     = Traceability
- AI        = AI Augmentation
- TOOL      = Tooling Infrastructure

Examples:
- REQ-INTENT-001: Intent Capture
- REQ-CODE-001: TDD Workflow
- REQ-TOOL-001: Plugin Architecture
```

**Traceability Flow**:
```
Intent (INT-001)
    ↓
Requirements: REQ-F-AUTH-001, REQ-NFR-PERF-001
    ↓
Design: AuthenticationService → REQ-F-AUTH-001
    ↓
Tasks: PORTAL-123 → REQ-F-AUTH-001
    ↓
Code: # Implements: REQ-F-AUTH-001
    ↓
Tests: # Validates: REQ-F-AUTH-001
    ↓
Runtime: logger.info({requirement: 'REQ-F-AUTH-001'})
    ↓
Feedback: Alert: "REQ-F-AUTH-001 - Error rate spike"
    ↓
New Intent: INT-042 "Fix auth error rate"
```

---

## 3. Architecture Decision Records

### 3.1 ADR Summary

| ADR | Decision | Requirements |
|-----|----------|--------------|
| [ADR-001](adrs/ADR-001-claude-code-as-mvp-platform.md) | Claude Code as MVP Platform | REQ-TOOL-001 |
| [ADR-002](adrs/ADR-002-commands-for-workflow-integration.md) | Commands for Workflow Integration | REQ-TOOL-003 |
| [ADR-003](adrs/ADR-003-agents-for-stage-personas.md) | Agents for Stage Personas | REQ-AI-003, REQ-STAGE-001 |
| [ADR-004](adrs/ADR-004-skills-for-reusable-capabilities.md) | Skills for Reusable Capabilities | REQ-AI-001 |
| [ADR-005](adrs/ADR-005-iterative-refinement-feedback-loops.md) | Iterative Refinement Feedback Loops | REQ-STAGE-004 |
| [ADR-006](adrs/ADR-006-plugin-configuration-and-discovery.md) | Plugin Configuration and Discovery | REQ-TOOL-004 |
| [ADR-007](adrs/ADR-007-hooks-for-methodology-automation.md) | Hooks for Methodology Automation | REQ-TOOL-008 |

### 3.2 Key Decisions Summary

1. **Platform Choice** (ADR-001): Claude Code as MVP platform
   - Native plugin support
   - Markdown-first design
   - No external infrastructure required

2. **Workflow Integration** (ADR-002): Slash commands
   - 8 workflow commands
   - File-based operations
   - Claude Code native integration

3. **Stage Personas** (ADR-003): Agent markdown files
   - 7 SDLC stage agents
   - Context-specific instructions
   - Bidirectional feedback

4. **Reusable Capabilities** (ADR-004): Skills plugins
   - 11 consolidated skills (was 42 granular)
   - Agent-independent execution
   - Sensor/actuator pattern

5. **Feedback Loops** (ADR-005): Iterative refinement
   - Bidirectional feedback protocol
   - Gap/ambiguity detection
   - Requirements versioning

6. **Plugin Discovery** (ADR-006): Configuration hierarchy
   - Federated loading
   - Deep merge strategy
   - Marketplace support

7. **Methodology Hooks** (ADR-007): Lifecycle automation
   - Session start/end hooks
   - Commit hooks for traceability
   - Pre-push validation

---

## 4. Design Documents

### 4.1 Stage Design Documents (11)

These comprehensive design documents cover all 43 requirements:

| Document | Requirements Covered |
|----------|---------------------|
| [INTENT_MANAGEMENT_DESIGN.md](INTENT_MANAGEMENT_DESIGN.md) | REQ-INTENT-001, 002, 003 |
| [WORKFLOW_STAGE_DESIGN.md](WORKFLOW_STAGE_DESIGN.md) | REQ-STAGE-001, 002, 003, 004 |
| [REQUIREMENTS_STAGE_DESIGN.md](REQUIREMENTS_STAGE_DESIGN.md) | REQ-REQ-001, 002, 003, 004 |
| [DESIGN_STAGE_DESIGN.md](DESIGN_STAGE_DESIGN.md) | REQ-DES-001, 002, 003 |
| [TASKS_STAGE_DESIGN.md](TASKS_STAGE_DESIGN.md) | REQ-TASK-001, 002, 003 |
| [CODE_STAGE_DESIGN.md](CODE_STAGE_DESIGN.md) | REQ-CODE-001, 002, 003, 004 |
| [SYSTEM_TEST_STAGE_DESIGN.md](SYSTEM_TEST_STAGE_DESIGN.md) | REQ-SYSTEST-001, 002, 003 |
| [UAT_STAGE_DESIGN.md](UAT_STAGE_DESIGN.md) | REQ-UAT-001, 002 |
| [RUNTIME_FEEDBACK_DESIGN.md](RUNTIME_FEEDBACK_DESIGN.md) | REQ-RUNTIME-001, 002, 003 |
| [TRACEABILITY_DESIGN.md](TRACEABILITY_DESIGN.md) | REQ-TRACE-001, 002, 003 |
| [AI_AUGMENTATION_DESIGN.md](AI_AUGMENTATION_DESIGN.md) | REQ-AI-001, 002, 003 |

**Note**: REQ-TOOL-001 through REQ-TOOL-008 (Tooling Infrastructure) are covered by ADRs 001-007 and the stage design documents.

### 4.2 Deprecated Documents

Legacy design documents have been moved to `deprecated/`:
- `AI_SDLC_UX_DESIGN.md` - Exploratory UX design
- `AGENTS_SKILLS_INTEROPERATION.md` - Superseded by AI_AUGMENTATION_DESIGN.md
- `CLAUDE_AGENTS_EXPLAINED.md` - Superseded by AI_AUGMENTATION_DESIGN.md
- `COMMAND_SYSTEM.md` - Tooling-focused, covered by stage designs
- `FOLDER_BASED_ASSET_DISCOVERY.md` - Tooling-focused
- `HOOKS_SYSTEM.md` - Tooling-focused, covered by ADR-007
- `PLUGIN_ARCHITECTURE.md` - Tooling-focused, covered by ADR-006
- `TEMPLATE_SYSTEM.md` - Tooling-focused

---

## 5. Integration Points

### 5.1 Plugin-Agent Integration

Plugins provide configuration, agents use it:

```yaml
# claude-code/plugins/aisdlc-methodology/config/stages_config.yml
stages:
  code:
    agent:
      role: "TDD-Driven Implementation"
      responsibilities:
        - "Execute TDD cycle (RED → GREEN → REFACTOR)"
        - "Tag code with requirement keys"
```

```markdown
<!-- .claude/agents/aisdlc-code-agent.md -->
## Role
TDD-Driven Implementation

## Responsibilities
1. Execute TDD cycle (RED → GREEN → REFACTOR)
2. Tag code with requirement keys (# Implements: REQ-*)
```

### 5.2 Agent-Skill Integration

Agents invoke skills for execution:

```
User: "Implement user login"
       ↓
Code Agent (loads context)
       ↓
Invokes: tdd-complete-workflow skill
       ↓
├─ Phase 1: RED (write failing tests)
├─ Phase 2: GREEN (minimal implementation)
├─ Phase 3: REFACTOR (quality + tech debt)
└─ Phase 4: COMMIT (with REQ-* traceability)
```

### 5.3 Command-Workspace Integration

Commands operate on workspace files:

```
/aisdlc-status → Reads .ai-workspace/tasks/active/ACTIVE_TASKS.md
/aisdlc-checkpoint-tasks → Writes .ai-workspace/tasks/finished/*.md
/aisdlc-commit-task → Reads finished task, generates commit message
```

---

## 6. Coverage Tracking

**For full requirement coverage across all SDLC stages, see**:

📊 **[TRACEABILITY_MATRIX.md](../TRACEABILITY_MATRIX.md)**

The traceability matrix is the single source of truth for:
- Requirement coverage by stage (Requirements → Design → Tasks → Code → Test → UAT → Runtime)
- Implementation status (Complete, Partial, Not Started)
- Gap analysis and next steps

---

## 7. References

### Requirements
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) - 43 platform-agnostic requirements

### Coverage Tracking
- [TRACEABILITY_MATRIX.md](../TRACEABILITY_MATRIX.md) - Full lifecycle traceability

### Architecture Decision Records
- [adrs/](adrs/) - 7 ADRs documenting key decisions

### Implementation
- `claude-code/.claude-plugin/plugins/aisdlc-methodology/` - Plugin implementation
- `.claude/agents/` - Agent files
- `.claude/commands/` - Command files
- `.ai-workspace/` - Workspace structure

---

**Document Status**: Active (v3.0)
**Last Updated**: 2025-12-03
**Next Review**: After next major release

**Version History**:
- v1.0 (2025-11-25): Initial design synthesis for 17 tooling-focused requirements
- v2.0 (2025-12-02): Updated for 42 platform-agnostic requirements, added gap analysis
- v3.0 (2025-12-03): Removed coverage tables (moved to TRACEABILITY_MATRIX.md), updated to reference 11 new stage design documents, added REQ-TOOL-008

---

**"Excellence or nothing"**
