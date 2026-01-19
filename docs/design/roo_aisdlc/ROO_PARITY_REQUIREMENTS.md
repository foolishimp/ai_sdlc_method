# Roo AISDLC - Parity Requirements

**Document Type**: Requirements Specification
**Project**: roo_aisdlc
**Version**: 1.0
**Date**: 2026-01-20
**Status**: Draft
**Purpose**: Define Phase 1 (MVP) requirements to achieve feature parity with Claude AISDLC implementation

---

## Executive Summary

This document defines the requirements to bring the Roo Code implementation of AI SDLC methodology to **Phase 1 (MVP) parity** with the Claude Code reference implementation. The Claude implementation is mature with 9 commands, 7 agents, 2 hooks, full workspace scaffolding, and validation tools. The Roo implementation currently has design documents and stub files but minimal implementation.

**Scope**: Phase 1 (MVP) only - Requirements → Design → Tasks → Code → System Test stages with core traceability.

---

## Gap Analysis Summary

| Component | Claude (Reference) | Roo (Current) | Gap |
|-----------|-------------------|---------------|-----|
| **Modes/Agents** | 7 agents (full implementations) | 7 mode JSONs (stubs only) | Need full role definitions with 400-600 line instructions each |
| **Commands** | 9 commands (561 lines total) | 0 commands | Need all 9 commands adapted for Roo |
| **Rules** | Embedded in commands | 6 rule files (partial) | Need validation and completion |
| **Hooks** | 2 hooks (Stop, PreToolUse) | 0 hooks | Roo doesn't support hooks - need alternative |
| **Installers** | 2 Python scripts (1,100 lines) | 0 installers | Need Python installer for Roo structure |
| **Validation** | Traceability validator (700 lines) | 0 validation | Need validator adapted for Roo |
| **Workspace** | Full scaffolding | Partial templates | Need complete workspace setup |
| **Documentation** | Complete guides | Minimal docs | Need user guides |

---

## Requirement Categories

1. [Mode Definitions](#1-mode-definitions) - 7 stage-specific modes
2. [Command System](#2-command-system) - Workflow automation via custom instructions
3. [Rule System](#3-rule-system) - Shared instructions across modes
4. [Installer System](#4-installer-system) - Project scaffolding automation
5. [Validation System](#5-validation-system) - Traceability and compliance checks
6. [Workspace Structure](#6-workspace-structure) - File organization and templates
7. [Documentation](#7-documentation) - User guides and examples

---

## 1. Mode Definitions

### Rationale

Roo Code uses "modes" (custom agent personas) to deliver stage-specific AI assistance. Each mode needs complete role definition, instructions, tool permissions, and integration with the shared workspace and rules system.

Claude has 7 fully-implemented agents averaging 400-600 lines each. Roo has 7 mode JSON stubs with ~10 lines each.

---

### REQ-ROO-MODE-001: Requirements Stage Mode

**Priority**: Critical
**Type**: Functional
**Phase**: 1

**Description**: Implement complete Requirements Agent mode for transforming intent into structured requirements with REQ-* keys.

**Acceptance Criteria**:
- Mode JSON at `roo/modes/aisdlc-requirements.json` is fully populated
- `roleDefinition` matches Claude agent's role (400+ lines converted to Roo format)
- `customInstructions` include:
  - Context loading from rules (@rules/req-tagging.md, @rules/feedback-protocol.md)
  - Requirement key format specification (REQ-F-*, REQ-NFR-*, REQ-DATA-*, REQ-BR-*)
  - Requirement structure template (key, description, acceptance criteria, priority, source)
  - Quality gates checklist (uniqueness, testability, traceability, no ambiguity)
  - Output file specifications (docs/requirements/*.md, TRACEABILITY_MATRIX.md, ACTIVE_TASKS.md)
  - Feedback protocol (how to accept from downstream stages)
- `groups` specify tool permissions: ["read", "browser"]
- Mode activatable with `@mode aisdlc-requirements`
- Integration with memory bank (@memory-bank/projectbrief.md)

**Rationale**: Requirements Agent is the entry point to the SDLC - must be fully functional for methodology to work.

**Traces To**:
- REQ-REQ-001 (Requirement Key Generation)
- REQ-REQ-002 (Requirement Types)
- REQ-AI-003 (Stage-Specific Agent Personas)
- Claude: `/agents/aisdlc-requirements-agent.md`

---

### REQ-ROO-MODE-002: Design Stage Mode

**Priority**: Critical
**Type**: Functional
**Phase**: 1

**Description**: Implement complete Design Agent mode for transforming requirements into technical solution architecture.

**Acceptance Criteria**:
- Mode JSON at `roo/modes/aisdlc-design.json` is fully populated
- `roleDefinition` defines Tech Lead persona with architecture responsibilities
- `customInstructions` include:
  - Context loading from rules (@rules/req-tagging.md, @rules/feedback-protocol.md)
  - Component design workflow (read requirements → design components → map to REQ-*)
  - ADR creation template (context, decision, consequences, alternatives, requirements addressed)
  - Design artifact specifications (AISDLC_IMPLEMENTATION_DESIGN.md, component diagrams, traceability matrix)
  - Quality gates (all requirements have design, all design maps to requirements)
  - Ecosystem awareness (E(t) context from memory bank)
- `groups` specify tool permissions: ["read", "edit", "browser"]
- Mode activatable with `@mode aisdlc-design`

**Rationale**: Design bridges requirements and implementation - critical for technical planning.

**Traces To**:
- REQ-DES-001 (Component Design)
- REQ-DES-002 (Architecture Decision Records)
- REQ-DES-003 (Design-to-Requirement Traceability)
- Claude: `/agents/aisdlc-design-agent.md`

---

### REQ-ROO-MODE-003: Tasks Stage Mode

**Priority**: High
**Type**: Functional
**Phase**: 1

**Description**: Implement complete Tasks Agent mode for breaking design into work units.

**Acceptance Criteria**:
- Mode JSON at `roo/modes/aisdlc-tasks.json` is fully populated
- `roleDefinition` defines Scrum Master/PM persona with task breakdown responsibilities
- `customInstructions` include:
  - Work breakdown workflow (read design → create tasks → map to REQ-*)
  - Task template (id, title, description, acceptance criteria, dependencies, REQ-* tags)
  - ACTIVE_TASKS.md structure and update protocol
  - Dependency tracking (blocks, is-blocked-by, relates-to)
  - Estimation guidance (story points, hours)
  - Quality gates (all design elements have tasks, all tasks have REQ-* tags)
- `groups` specify tool permissions: ["read", "edit"]
- Mode activatable with `@mode aisdlc-tasks`

**Rationale**: Task breakdown enables parallel work and progress tracking.

**Traces To**:
- REQ-TASK-001 (Work Breakdown)
- REQ-TASK-003 (Task-to-Requirement Traceability)
- Claude: `/agents/aisdlc-tasks-agent.md`

---

### REQ-ROO-MODE-004: Code Stage Mode

**Priority**: Critical
**Type**: Functional
**Phase**: 1

**Description**: Implement complete Code Agent mode with TDD workflow and Key Principles enforcement.

**Acceptance Criteria**:
- Mode JSON at `roo/modes/aisdlc-code.json` is fully populated
- `roleDefinition` defines Developer persona with TDD expertise
- `customInstructions` include:
  - Context loading from rules (@rules/tdd-workflow.md, @rules/key-principles.md, @rules/req-tagging.md)
  - TDD workflow (RED → GREEN → REFACTOR → COMMIT)
  - Key Principles checklist (7 questions before coding)
  - Code tagging format (# Implements: REQ-*, # Validates: REQ-*)
  - Test coverage requirements (minimum 80%, configurable)
  - Quality gates (tests first, REQ-* tags, coverage threshold)
  - Seven Questions integration (ask before every implementation)
- `groups` specify tool permissions: ["read", "edit", "command"]
- Mode activatable with `@mode aisdlc-code`

**Rationale**: Code stage is where methodology delivers value - must enforce TDD and Key Principles.

**Traces To**:
- REQ-CODE-001 (TDD Workflow)
- REQ-CODE-002 (Key Principles Enforcement)
- REQ-CODE-003 (Code-to-Requirement Tagging)
- REQ-CODE-004 (Test Coverage)
- Claude: `/agents/aisdlc-code-agent.md`

---

### REQ-ROO-MODE-005: System Test Stage Mode

**Priority**: High
**Type**: Functional
**Phase**: 1

**Description**: Implement complete System Test Agent mode for BDD integration testing.

**Acceptance Criteria**:
- Mode JSON at `roo/modes/aisdlc-system-test.json` is fully populated
- `roleDefinition` defines QA Engineer persona with BDD expertise
- `customInstructions` include:
  - Context loading from rules (@rules/bdd-workflow.md, @rules/req-tagging.md)
  - BDD scenario creation (Given/When/Then Gherkin format)
  - Test artifact specifications (*.feature files, step definitions, coverage matrix)
  - Quality gates (all requirements have scenarios, scenarios map to REQ-*)
  - Test execution guidance (how to run BDD tests)
- `groups` specify tool permissions: ["read", "edit", "command"]
- Mode activatable with `@mode aisdlc-system-test`

**Rationale**: System Test validates requirements are correctly implemented via integration testing.

**Traces To**:
- REQ-SYSTEST-001 (BDD Scenario Creation)
- REQ-SYSTEST-002 (Integration Test Execution)
- REQ-SYSTEST-003 (Test-to-Requirement Traceability)
- Claude: `/agents/aisdlc-system-test-agent.md`

---

### REQ-ROO-MODE-006: UAT Stage Mode

**Priority**: Medium
**Type**: Functional
**Phase**: 2 (out of scope for Phase 1 MVP)

**Description**: Implement complete UAT Agent mode for business validation.

**Acceptance Criteria**:
- Mode JSON at `roo/modes/aisdlc-uat.json` is fully populated
- Business validation in non-technical language
- Sign-off workflow

**Rationale**: UAT is Phase 2 (Ecosystem) feature - deferred to v2.0.

**Traces To**:
- REQ-UAT-001 (Business Validation Tests)
- REQ-UAT-002 (Sign-off Workflow)
- Claude: `/agents/aisdlc-uat-agent.md`

---

### REQ-ROO-MODE-007: Runtime Feedback Stage Mode

**Priority**: Medium
**Type**: Functional
**Phase**: 2 (out of scope for Phase 1 MVP)

**Description**: Implement complete Runtime Feedback Agent mode for production monitoring and feedback loop closure.

**Acceptance Criteria**:
- Mode JSON at `roo/modes/aisdlc-runtime.json` is fully populated
- Telemetry tagging with REQ-* keys
- Deviation detection
- Feedback loop closure (production → intent)

**Rationale**: Runtime Feedback is Phase 2 (Ecosystem) feature - deferred to v2.0.

**Traces To**:
- REQ-RUNTIME-001 (Telemetry Tagging)
- REQ-RUNTIME-002 (Deviation Detection)
- REQ-RUNTIME-003 (Feedback Loop Closure)
- Claude: `/agents/aisdlc-runtime-feedback-agent.md`

---

## 2. Command System

### Rationale

Roo Code doesn't have native slash commands like Claude Code. Commands must be delivered as **mode-embedded custom instructions** that the user invokes via natural language or @mode directives.

Alternative: Create dedicated "command modes" (e.g., `@mode aisdlc-checkpoint`) that execute single operations.

Claude has 9 commands totaling 561 lines. Roo needs equivalent functionality adapted for mode-based invocation.

---

### REQ-ROO-CMD-001: Task Checkpoint Functionality

**Priority**: Critical
**Type**: Functional
**Phase**: 1

**Description**: Provide task checkpointing functionality equivalent to Claude's `/aisdlc-checkpoint-tasks` command.

**Acceptance Criteria**:
- Invocable via natural language: "Checkpoint my tasks" or dedicated mode `@mode aisdlc-checkpoint`
- Implementation:
  - Option A: Add checkpoint instructions to ALL modes (modes check for "checkpoint" keyword)
  - Option B: Create dedicated `aisdlc-checkpoint.json` mode that only does checkpointing
  - Option C: Embed in Rules as @rules/checkpoint-protocol.md referenced by all modes
- Functionality matches Claude command:
  - Phase 1: Analyze conversation context for completed work
  - Phase 2: Evaluate each task in ACTIVE_TASKS.md (completed, in_progress, blocked, not_started)
  - Phase 3: Update ACTIVE_TASKS.md, create finished task docs, update timestamps
  - Phase 4: Report summary with counts and next steps
- Output: Updated ACTIVE_TASKS.md, new files in tasks/finished/, summary report

**Rationale**: Checkpointing is critical for maintaining accurate task state across sessions.

**Traces To**:
- REQ-TOOL-003 (Workflow Commands)
- REQ-TASK-001 (Work Breakdown)
- Claude: `/commands/aisdlc-checkpoint-tasks.md`

**Recommendation**: **Option B (Dedicated Mode)** - cleanest separation, most explicit invocation.

---

### REQ-ROO-CMD-002: Workspace Initialization Functionality

**Priority**: Critical
**Type**: Functional
**Phase**: 1

**Description**: Provide workspace initialization functionality equivalent to Claude's `/aisdlc-init` command.

**Acceptance Criteria**:
- Invocable via natural language: "Initialize AI SDLC workspace" or dedicated mode `@mode aisdlc-init`
- Functionality matches Claude command:
  - Determine project name (ask user or infer from directory/package.json/pyproject.toml)
  - Create directory structure (.ai-workspace/, docs/requirements/, docs/design/, etc.)
  - Create placeholder files:
    - ACTIVE_TASKS.md
    - workspace_config.yml
    - TASK_TEMPLATE.md
    - INTENT.md
    - AISDLC_IMPLEMENTATION_REQUIREMENTS.md
    - AISDLC_IMPLEMENTATION_DESIGN.md
    - ADR-000-template.md
    - TRACEABILITY_MATRIX.md
  - Report summary of created files
  - Show version info
- Support modes:
  - Default: Create missing files only (safe)
  - `--force` equivalent: Overwrite framework files (preserve user work)
  - `--backup` equivalent: Create backup before changes
- Output: Complete scaffolded project structure

**Rationale**: Init is the entry point for new projects - must be fully automated.

**Traces To**:
- REQ-TOOL-002 (Developer Workspace)
- REQ-TOOL-010 (Installer Project Scaffolding)
- Claude: `/commands/aisdlc-init.md`

**Recommendation**: **Dedicated Mode + Python Installer** - complex logic better in Python, mode invokes installer.

---

### REQ-ROO-CMD-003: Status Report Functionality

**Priority**: High
**Type**: Functional
**Phase**: 1

**Description**: Provide status reporting functionality equivalent to Claude's `/aisdlc-status` command.

**Acceptance Criteria**:
- Invocable via natural language: "Show project status" or dedicated mode `@mode aisdlc-status`
- Functionality matches Claude command:
  - Read ACTIVE_TASKS.md and display task summary (counts by status)
  - Read TRACEABILITY_MATRIX.md and display coverage summary
  - Show recent commits with REQ-* tags
  - Identify gaps (requirements without tests, tasks without REQ-* tags)
  - Display recent finished tasks
  - Suggest next actions based on current state
- Output: Formatted status report with actionable recommendations

**Rationale**: Status provides situational awareness - critical for ongoing work.

**Traces To**:
- REQ-TOOL-003 (Workflow Commands)
- REQ-TRACE-001 (Full Lifecycle Traceability)
- Claude: `/commands/aisdlc-status.md`

**Recommendation**: **Dedicated Mode** - read-only operation, pure display logic.

---

### REQ-ROO-CMD-004: Context Refresh Functionality

**Priority**: High
**Type**: Functional
**Phase**: 1

**Description**: Provide context refresh functionality equivalent to Claude's `/aisdlc-refresh-context` command.

**Acceptance Criteria**:
- Invocable via natural language: "Refresh my context" or dedicated mode `@mode aisdlc-refresh`
- Functionality matches Claude command:
  - Read ACTIVE_TASKS.md to show current work items
  - Read TRACEABILITY_MATRIX.md to show requirement coverage
  - Read recent finished tasks to show what was completed
  - Display memory bank contents (projectbrief.md, techstack.md, activecontext.md)
  - Suggest next actions based on active tasks
- Output: Contextual summary optimized for "cold start" sessions

**Rationale**: Refresh restores context after breaks - enables session continuity.

**Traces To**:
- REQ-TOOL-003 (Workflow Commands)
- REQ-TOOL-002 (Developer Workspace)
- Claude: `/commands/aisdlc-refresh-context.md`

**Recommendation**: **Dedicated Mode** - leverage Roo's memory bank (@memory-bank) for persistence.

---

### REQ-ROO-CMD-005: Help System Functionality

**Priority**: Medium
**Type**: Functional
**Phase**: 1

**Description**: Provide help system functionality equivalent to Claude's `/aisdlc-help` command.

**Acceptance Criteria**:
- Invocable via natural language: "Help with AI SDLC" or dedicated mode `@mode aisdlc-help`
- Functionality matches Claude command:
  - Display all available modes and their purposes
  - Show invocation examples ("@mode aisdlc-requirements", "Checkpoint my tasks")
  - List available rules (@rules/tdd-workflow.md, @rules/bdd-workflow.md, etc.)
  - Explain workflow (Requirements → Design → Tasks → Code → System Test)
  - Link to documentation (GitHub, methodology docs)
- Output: Formatted help guide with examples

**Rationale**: Help enables self-service discovery - reduces learning curve.

**Traces To**:
- REQ-TOOL-003 (Workflow Commands)
- Claude: `/commands/aisdlc-help.md`

**Recommendation**: **Dedicated Mode + Static Doc** - display pre-written help content.

---

### REQ-ROO-CMD-006: Commit Helper Functionality

**Priority**: Medium
**Type**: Functional
**Phase**: 1

**Description**: Provide commit helper functionality equivalent to Claude's `/aisdlc-commit` command.

**Acceptance Criteria**:
- Invocable via natural language: "Help me commit" or dedicated mode `@mode aisdlc-commit`
- Functionality matches Claude command:
  - Run `git status` and `git diff` to see changes
  - Extract REQ-* tags from changed files
  - Suggest commit message including REQ-* tags
  - Guide user through commit (stage files, create commit with proper message)
- Output: Properly tagged commit with REQ-* keys

**Rationale**: Commit helper ensures REQ-* tag propagation in version control.

**Traces To**:
- REQ-CODE-003 (Code-to-Requirement Tagging)
- REQ-TRACE-002 (Requirement Key Propagation)
- Claude: `/commands/aisdlc-commit.md`

**Recommendation**: **Dedicated Mode** - simple git workflow assistance.

---

### REQ-ROO-CMD-007: Release Management Functionality

**Priority**: Low
**Type**: Functional
**Phase**: 1

**Description**: Provide release management functionality equivalent to Claude's `/aisdlc-release` command.

**Acceptance Criteria**:
- Invocable via natural language: "Create a release" or dedicated mode `@mode aisdlc-release`
- Functionality matches Claude command:
  - Determine version (ask user or infer from git tags, semantic versioning)
  - Generate changelog from commits and finished tasks
  - Create release notes with requirement coverage summary
  - Tag release in git
  - Update version in package files (package.json, pyproject.toml)
- Output: Tagged release with changelog and release notes

**Rationale**: Release management enables versioned distribution.

**Traces To**:
- REQ-TOOL-005 (Release Management)
- Claude: `/commands/aisdlc-release.md`

**Recommendation**: **Dedicated Mode** - complex workflow, guide user step-by-step.

---

### REQ-ROO-CMD-008: Context Snapshot Functionality

**Priority**: Medium
**Type**: Functional
**Phase**: 1

**Description**: Provide context snapshot functionality equivalent to Claude's `/aisdlc-snapshot-context` command.

**Acceptance Criteria**:
- Invocable via natural language: "Snapshot my context" or dedicated mode `@mode aisdlc-snapshot`
- Functionality matches Claude command:
  - Create immutable snapshot in `.ai-workspace/context_history/`
  - Filename format: `{YYYYMMDD}_{HHMM}_{label}.md`
  - Include: timestamp, active tasks summary, current work context, recovery guidance
  - Integrate with checkpoint mechanism
  - Archive old snapshots after retention period (default: 30 days)
- Output: Snapshot file with recovery instructions

**Rationale**: Snapshots enable session recovery and team handoffs.

**Traces To**:
- REQ-TOOL-012 (Context Snapshot and Recovery)
- Claude: `/commands/aisdlc-snapshot-context.md`

**Recommendation**: **Dedicated Mode** - complements Roo's memory bank with explicit snapshots.

---

### REQ-ROO-CMD-009: Version Display Functionality

**Priority**: Low
**Type**: Functional
**Phase**: 1

**Description**: Provide version display functionality equivalent to Claude's `/aisdlc-version` command.

**Acceptance Criteria**:
- Invocable via natural language: "Show AISDLC version" or dedicated mode `@mode aisdlc-version`
- Functionality matches Claude command:
  - Display current plugin/mode version
  - Show last update date
  - Link to GitHub repository
  - Show changelog summary
- Output: Version info with links

**Rationale**: Version display enables troubleshooting and update tracking.

**Traces To**:
- REQ-TOOL-003 (Workflow Commands)
- Claude: `/commands/aisdlc-version.md`

**Recommendation**: **Dedicated Mode** - simple display logic.

---

## 3. Rule System

### Rationale

Roo Code's "rules" are custom instructions loaded into modes via `@rules/filename.md` syntax. They provide shared behavior across multiple modes.

Roo currently has 6 rule files with partial content. Need validation and completion to match Claude's embedded instruction quality.

---

### REQ-ROO-RULE-001: TDD Workflow Rule

**Priority**: Critical
**Type**: Functional
**Phase**: 1

**Description**: Complete and validate the TDD workflow rule for use in Code stage mode.

**Acceptance Criteria**:
- File: `roo/rules/tdd-workflow.md`
- Content matches Claude's TDD guidance:
  - RED phase: Write failing test first (how to structure test, what makes a good test)
  - GREEN phase: Minimal code to pass (resist over-engineering)
  - REFACTOR phase: Improve quality (when to refactor, what to improve)
  - COMMIT phase: Save with REQ-* tag (commit message format)
- Examples provided for each phase
- Checklist for agent to follow
- Integrated into Code mode via `@rules/tdd-workflow.md`

**Rationale**: TDD is Principle #1 - must be rigorously defined.

**Traces To**:
- REQ-CODE-001 (TDD Workflow)
- Claude: `/docs/processes/TDD_WORKFLOW.md` (embedded in code agent)

---

### REQ-ROO-RULE-002: BDD Workflow Rule

**Priority**: High
**Type**: Functional
**Phase**: 1

**Description**: Complete and validate the BDD workflow rule for use in System Test stage mode.

**Acceptance Criteria**:
- File: `roo/rules/bdd-workflow.md`
- Content matches Claude's BDD guidance:
  - Given/When/Then structure (how to write scenarios)
  - Step definition patterns (how to implement steps)
  - Scenario organization (feature files, tags, examples)
  - Coverage tracking (ensure all requirements have scenarios)
- Examples provided (login scenario, error handling scenario)
- Integrated into System Test mode via `@rules/bdd-workflow.md`

**Rationale**: BDD is System Test methodology - must be clearly defined.

**Traces To**:
- REQ-SYSTEST-001 (BDD Scenario Creation)
- Claude: Embedded in system-test agent

---

### REQ-ROO-RULE-003: REQ Tagging Rule

**Priority**: Critical
**Type**: Functional
**Phase**: 1

**Description**: Complete and validate the REQ-* tagging rule for use across all modes.

**Acceptance Criteria**:
- File: `roo/rules/req-tagging.md`
- Content defines:
  - REQ-* key format (REQ-{TYPE}-{DOMAIN}-{SEQ})
  - Types: F, NFR, DATA, BR
  - Where to use tags:
    - Code comments: `# Implements: REQ-F-AUTH-001`
    - Test comments: `# Validates: REQ-F-AUTH-001`
    - Commit messages: `"Add login (REQ-F-AUTH-001)"`
    - Task descriptions: `**Implements**: REQ-F-AUTH-001`
    - Design docs: `**Implements**: REQ-F-AUTH-001`
  - Validation checklist (tag present, tag valid format, tag traceable)
- Examples provided for each artifact type
- Integrated into ALL modes via `@rules/req-tagging.md`

**Rationale**: REQ-* tagging is the traceability mechanism - must be consistent everywhere.

**Traces To**:
- REQ-TRACE-002 (Requirement Key Propagation)
- REQ-CODE-003 (Code-to-Requirement Tagging)
- Claude: Embedded in all agents

---

### REQ-ROO-RULE-004: Feedback Protocol Rule

**Priority**: High
**Type**: Functional
**Phase**: 1

**Description**: Complete and validate the feedback protocol rule for use across all modes.

**Acceptance Criteria**:
- File: `roo/rules/feedback-protocol.md`
- Content defines:
  - Universal feedback behavior (REQ-NFR-REFINE-001)
  - Accept feedback FROM downstream stages (what to accept, how to process)
  - Provide feedback TO upstream stages (when to send, how to format)
  - Feedback triggers (gap, ambiguity, conflict, error)
  - Feedback actions (pause, analyze, decide, update, version, notify, resume)
  - Maximum 3 iterations per item
- Examples provided (Design → Requirements feedback, Code → Design feedback)
- Integrated into ALL modes via `@rules/feedback-protocol.md`

**Rationale**: Feedback protocol enables iterative refinement - critical for methodology.

**Traces To**:
- REQ-STAGE-004 (Bidirectional Feedback)
- REQ-REQ-003 (Requirement Refinement)
- Claude: Embedded in all agents

---

### REQ-ROO-RULE-005: Key Principles Rule

**Priority**: Critical
**Type**: Functional
**Phase**: 1

**Description**: Complete and validate the Key Principles rule for use in Code stage mode.

**Acceptance Criteria**:
- File: `roo/rules/key-principles.md`
- Content defines all 7 principles:
  1. Test Driven Development - "No code without tests"
  2. Fail Fast & Root Cause - "Break loudly, fix completely"
  3. Modular & Maintainable - "Single responsibility, loose coupling"
  4. Reuse Before Build - "Check first, create second"
  5. Open Source First - "Suggest alternatives, human decides"
  6. No Legacy Baggage - "Clean slate, no debt"
  7. Perfectionist Excellence - "Best of breed only"
- Seven Questions checklist included
- Integrated into Code mode via `@rules/key-principles.md`

**Rationale**: Key Principles define engineering excellence - must be enforced in Code stage.

**Traces To**:
- REQ-CODE-002 (Key Principles Enforcement)
- Claude: `/docs/principles/KEY_PRINCIPLES.md`

---

### REQ-ROO-RULE-006: Workspace Safeguards Rule

**Priority**: Medium
**Type**: Functional
**Phase**: 1

**Description**: Complete and validate the workspace safeguards rule for use across all modes.

**Acceptance Criteria**:
- File: `roo/rules/workspace-safeguards.md`
- Content defines:
  - Never delete ACTIVE_TASKS.md without explicit confirmation
  - Never delete finished task files
  - Always backup before `--force` operations
  - Validate file paths before write operations
  - Preserve user work during framework updates
- Checklist for agents to follow before destructive operations
- Integrated into modes that modify workspace via `@rules/workspace-safeguards.md`

**Rationale**: Safeguards prevent accidental data loss - critical for user trust.

**Traces To**:
- REQ-TOOL-002 (Developer Workspace)
- Claude: Embedded in init and checkpoint commands

---

## 4. Installer System

### Rationale

Roo Code projects need automated setup to reduce manual configuration. Claude has a 1,100-line Python installer that scaffolds the entire workspace.

Roo currently has no installer. Need Python script adapted for Roo's structure (roo/ folder instead of .claude/ folder).

---

### REQ-ROO-INSTALL-001: Python Installer Script

**Priority**: Critical
**Type**: Functional
**Phase**: 1

**Description**: Create Python installer script that scaffolds complete Roo AISDLC project structure.

**Acceptance Criteria**:
- Script location: `roo-code-iclaude/installers/aisdlc-setup.py`
- Command interface:
  ```bash
  python aisdlc-setup.py init --variant <name> --platform roo-code
  python aisdlc-setup.py validate
  python aisdlc-setup.py update [--force] [--backup]
  ```
- `init` command creates:
  - `roo/` directory with modes/, rules/, memory-bank/ subdirectories
  - `.ai-workspace/` directory with tasks/, templates/, config/ subdirectories
  - `docs/` directory with requirements/, design/, test/, uat/, runtime/, releases/ subdirectories
  - All placeholder files from templates (INTENT.md, REQUIREMENTS.md, DESIGN.md, etc.)
  - IMPLEMENTATION.yaml manifest binding implementation to design
- `validate` command checks:
  - IMPLEMENTATION.yaml exists and points to valid design_path
  - Required design artifacts exist (requirements.yaml, DESIGN.md)
  - Required workspace artifacts exist (ACTIVE_TASKS.md, templates)
  - Mode JSONs are valid JSON
  - Rule files exist
- `update` command:
  - Default: Create missing files only
  - `--force`: Overwrite framework files (preserve user work: ACTIVE_TASKS.md, finished/, requirements/, design/)
  - `--backup`: Create backup in /tmp before changes
- Logging: Progress messages, warnings, errors, success summary
- Exit codes: 0 (success), 1 (validation failed), 2 (operation failed)

**Rationale**: Installer automates setup - critical for adoption and consistency.

**Traces To**:
- REQ-TOOL-010 (Installer Project Scaffolding)
- REQ-TOOL-011 (Installer Design-Implementation Validation)
- Claude: `/installers/aisdlc-setup.py`

---

### REQ-ROO-INSTALL-002: Project Templates

**Priority**: High
**Type**: Functional
**Phase**: 1

**Description**: Create complete set of project templates used by installer.

**Acceptance Criteria**:
- Template directory: `roo-code-iclaude/project-template/`
- Templates include:
  - `roo/modes/*.json` - All 7 mode JSONs with full content
  - `roo/rules/*.md` - All 6 rule files with full content
  - `roo/memory-bank/*.md` - All 3 memory bank files (projectbrief, techstack, activecontext)
  - `.ai-workspace/tasks/active/ACTIVE_TASKS.md` - Task tracking template
  - `.ai-workspace/templates/TASK_TEMPLATE.md` - Task entry template
  - `.ai-workspace/templates/FINISHED_TASK_TEMPLATE.md` - Completed task template
  - `.ai-workspace/config/workspace_config.yml` - Workspace settings
  - `docs/requirements/INTENT.md` - Intent template
  - `docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` - Requirements template
  - `docs/design/{variant}/AISDLC_IMPLEMENTATION_DESIGN.md` - Design template
  - `docs/design/{variant}/adrs/ADR-000-template.md` - ADR template
  - `docs/TRACEABILITY_MATRIX.md` - Traceability template
- Templates use placeholders: `{project_name}`, `{date}`, `{variant}`
- Installer substitutes placeholders during setup
- Templates match Claude versions but adapted for Roo structure

**Rationale**: Templates ensure consistent project structure across all installations.

**Traces To**:
- REQ-TOOL-010 (Installer Project Scaffolding)
- Claude: `/templates/`

---

## 5. Validation System

### Rationale

Validation tools programmatically check methodology compliance. Claude has a 700-line traceability validator. Roo needs equivalent adapted for Roo structure.

---

### REQ-ROO-VALIDATE-001: Traceability Validator Script

**Priority**: High
**Type**: Functional
**Phase**: 1

**Description**: Create Python script that validates requirement traceability across all stages.

**Acceptance Criteria**:
- Script location: `roo-code-iclaude/installers/validate_traceability.py`
- Command interface:
  ```bash
  python validate_traceability.py [--strict] [--report-format {text|json|html}]
  ```
- Validation checks:
  - **Requirements**: All REQ-* keys in REQUIREMENTS.md are unique, valid format
  - **Design**: All components map to REQ-* keys, all REQ-* keys have components
  - **Tasks**: All tasks in ACTIVE_TASKS.md reference REQ-* keys
  - **Code**: Grep source for `# Implements: REQ-*`, validate tags exist in REQUIREMENTS.md
  - **Tests**: Grep tests for `# Validates: REQ-*`, validate tags exist in REQUIREMENTS.md
  - **Traceability Matrix**: All entries reference valid REQ-* keys, no orphans
- Gap detection:
  - Requirements without design (REQ-* in REQUIREMENTS.md, not in DESIGN.md)
  - Requirements without tests (REQ-* in REQUIREMENTS.md, not in tests/)
  - Requirements without code (REQ-* in REQUIREMENTS.md, not in src/)
  - Code without requirements (# Implements tag, but REQ-* not in REQUIREMENTS.md)
- Output formats:
  - Text: Console-friendly summary with colored output
  - JSON: Machine-readable for CI/CD integration
  - HTML: Visual report with drill-down capability
- Exit codes: 0 (all valid), 1 (gaps found), 2 (validation errors)
- `--strict` mode: Fail on ANY gap (for CI/CD gates)

**Rationale**: Automated validation ensures traceability is maintained, not just documented.

**Traces To**:
- REQ-TRACE-003 (Traceability Validation)
- REQ-TRACE-001 (Full Lifecycle Traceability)
- Claude: `/installers/validate_traceability.py`

---

### REQ-ROO-VALIDATE-002: Mode Validation Script

**Priority**: Medium
**Type**: Functional
**Phase**: 1

**Description**: Create Python script that validates mode JSONs are well-formed and complete.

**Acceptance Criteria**:
- Script location: `roo-code-iclaude/installers/validate_modes.py`
- Command interface:
  ```bash
  python validate_modes.py [--mode <name>]
  ```
- Validation checks:
  - JSON syntax is valid
  - Required fields present: slug, name, roleDefinition, groups, customInstructions
  - `slug` matches filename (aisdlc-requirements.json → slug: "aisdlc-requirements")
  - `groups` contains valid tool permissions (read, edit, command, mcp, browser)
  - `customInstructions` references valid rules (@rules/*.md files exist)
  - `roleDefinition` is non-empty (minimum 100 characters)
- Output: Per-mode validation status, error details, success summary
- Exit codes: 0 (all valid), 1 (validation failed)

**Rationale**: Mode validation catches configuration errors before runtime.

**Traces To**:
- REQ-ROO-MODE-001 through REQ-ROO-MODE-007
- Claude: Embedded in aisdlc-setup.py validation

---

## 6. Workspace Structure

### Rationale

Workspace structure must be consistent and well-documented. Roo has partial templates - need completion.

---

### REQ-ROO-WORKSPACE-001: Complete .ai-workspace Structure

**Priority**: High
**Type**: Structural
**Phase**: 1

**Description**: Complete the .ai-workspace directory structure and templates.

**Acceptance Criteria**:
- Directory structure:
  ```
  .ai-workspace/
  ├── tasks/
  │   ├── active/
  │   │   └── ACTIVE_TASKS.md
  │   └── finished/
  │       └── {YYYYMMDD_HHMM}_{task_slug}.md
  ├── templates/
  │   ├── TASK_TEMPLATE.md
  │   └── FINISHED_TASK_TEMPLATE.md
  ├── config/
  │   └── workspace_config.yml
  ├── context_history/
  │   └── {YYYYMMDD}_{HHMM}_{label}.md
  └── README.md
  ```
- All templates match Claude versions
- README.md explains structure and usage
- workspace_config.yml includes all settings (auto_checkpoint, require_req_tags, coverage_minimum)

**Rationale**: Workspace is the foundation for task management and context persistence.

**Traces To**:
- REQ-TOOL-002 (Developer Workspace)
- Claude: `/templates/.ai-workspace/`

---

### REQ-ROO-WORKSPACE-002: Complete roo/ Structure

**Priority**: Critical
**Type**: Structural
**Phase**: 1

**Description**: Complete the roo/ directory structure for modes, rules, and memory bank.

**Acceptance Criteria**:
- Directory structure:
  ```
  roo/
  ├── modes/
  │   ├── aisdlc-requirements.json
  │   ├── aisdlc-design.json
  │   ├── aisdlc-tasks.json
  │   ├── aisdlc-code.json
  │   ├── aisdlc-system-test.json
  │   ├── aisdlc-uat.json (Phase 2)
  │   └── aisdlc-runtime.json (Phase 2)
  ├── rules/
  │   ├── tdd-workflow.md
  │   ├── bdd-workflow.md
  │   ├── key-principles.md
  │   ├── req-tagging.md
  │   ├── feedback-protocol.md
  │   └── workspace-safeguards.md
  ├── memory-bank/
  │   ├── projectbrief.md
  │   ├── techstack.md
  │   ├── activecontext.md
  │   └── methodref.md
  └── README.md
  ```
- All files have complete content (not stubs)
- README.md explains Roo-specific features (modes, rules, memory bank)
- methodref.md references full AI SDLC methodology

**Rationale**: roo/ structure is Roo's integration point - must be complete and documented.

**Traces To**:
- REQ-ROO-MODE-* (all mode requirements)
- REQ-ROO-RULE-* (all rule requirements)
- Roo Code documentation

---

### REQ-ROO-WORKSPACE-003: Complete docs/ Structure

**Priority**: High
**Type**: Structural
**Phase**: 1

**Description**: Complete the docs/ directory structure for requirements, design, and artifacts.

**Acceptance Criteria**:
- Directory structure matches Claude:
  ```
  docs/
  ├── requirements/
  │   ├── INTENT.md
  │   └── AISDLC_IMPLEMENTATION_REQUIREMENTS.md
  ├── design/
  │   └── {variant}_aisdlc/
  │       ├── requirements.yaml
  │       ├── AISDLC_IMPLEMENTATION_DESIGN.md
  │       ├── design.md
  │       └── adrs/
  │           └── ADR-000-template.md
  ├── test/
  │   └── coverage/
  ├── uat/
  │   └── test_cases/
  ├── runtime/
  │   └── telemetry/
  ├── releases/
  │   └── CHANGELOG.md
  └── TRACEABILITY_MATRIX.md
  ```
- All templates have complete content with examples
- Structure enables Phase 1 MVP (Requirements → System Test)
- Phase 2 directories present but optional (uat/, runtime/)

**Rationale**: docs/ structure stores all SDLC artifacts - must match methodology stages.

**Traces To**:
- REQ-TOOL-009 (Design-Implementation Structure Convention)
- Claude: Project structure convention

---

## 7. Documentation

### Rationale

User documentation is critical for adoption. Need comprehensive guides adapted for Roo.

---

### REQ-ROO-DOC-001: Installation Guide

**Priority**: High
**Type**: Documentation
**Phase**: 1

**Description**: Create installation guide for Roo AISDLC.

**Acceptance Criteria**:
- File: `roo-code-iclaude/README.md`
- Content includes:
  - Prerequisites (Roo Code, Python 3.8+, git)
  - Installation steps (clone repo, run installer)
  - Project initialization (how to use aisdlc-setup.py)
  - Mode activation (how to use @mode syntax)
  - Troubleshooting (common issues and solutions)
  - Examples (quickstart project)
- Screenshots of Roo Code with modes active
- Links to full methodology documentation

**Rationale**: Installation guide is the entry point for new users.

**Traces To**:
- REQ-TOOL-010 (Installer Project Scaffolding)

---

### REQ-ROO-DOC-002: Mode User Guide

**Priority**: High
**Type**: Documentation
**Phase**: 1

**Description**: Create user guide for all 7 modes.

**Acceptance Criteria**:
- File: `roo-code-iclaude/docs/MODE_GUIDE.md`
- Content includes:
  - Overview of mode system (what modes are, why use them)
  - Per-mode guide:
    - When to use this mode
    - How to activate (@mode aisdlc-requirements)
    - What it does (role, responsibilities, outputs)
    - Example interactions (natural language prompts)
  - Workflow guide (Requirements → Design → Tasks → Code → System Test)
  - Switching between modes (when to switch, how to handoff context)
- Examples with screenshots

**Rationale**: Mode guide explains how to use the methodology effectively.

**Traces To**:
- REQ-AI-003 (Stage-Specific Agent Personas)

---

### REQ-ROO-DOC-003: Workflow Examples

**Priority**: Medium
**Type**: Documentation
**Phase**: 1

**Description**: Create end-to-end workflow examples.

**Acceptance Criteria**:
- File: `roo-code-iclaude/docs/WORKFLOW_EXAMPLES.md`
- Content includes:
  - Simple example (single feature end-to-end)
    - Intent: "Add user login"
    - Requirements: REQ-F-AUTH-001 generated
    - Design: AuthService component
    - Tasks: Work breakdown
    - Code: TDD implementation
    - System Test: BDD scenarios
  - Complex example (multi-feature with dependencies)
  - Error handling example (downstream feedback)
  - Screenshots at each stage

**Rationale**: Examples demonstrate methodology in practice - accelerate learning.

**Traces To**:
- Complete 7-stage workflow

---

### REQ-ROO-DOC-004: Roo-Specific Features Guide

**Priority**: Medium
**Type**: Documentation
**Phase**: 1

**Description**: Create guide explaining Roo-specific features and differences from Claude.

**Acceptance Criteria**:
- File: `roo-code-iclaude/docs/ROO_FEATURES.md`
- Content includes:
  - Memory bank explained (@memory-bank persistence)
  - Rules system explained (@rules shared instructions)
  - Mode activation vs slash commands (natural language + @mode vs /command)
  - Tool group permissions (read, edit, command, mcp, browser)
  - MCP integration (if applicable)
  - Differences from Claude implementation (what's different, why, pros/cons)
- Migration guide for Claude users

**Rationale**: Roo has unique features - users need to understand them to maximize effectiveness.

**Traces To**:
- Roo Code platform capabilities

---

## Requirement Summary

### By Category

| Category | Phase 1 Count | Critical | High | Medium | Low |
|----------|---------------|----------|------|--------|-----|
| Mode Definitions | 5 | 3 | 2 | 0 | 0 |
| Command System | 9 | 2 | 3 | 3 | 1 |
| Rule System | 6 | 3 | 2 | 1 | 0 |
| Installer System | 2 | 1 | 1 | 0 | 0 |
| Validation System | 2 | 0 | 1 | 1 | 0 |
| Workspace Structure | 3 | 1 | 2 | 0 | 0 |
| Documentation | 4 | 0 | 2 | 2 | 0 |
| **Phase 1 Total** | **31** | **10** | **13** | **7** | **1** |

### Phase 1 MVP Requirements (31 total)

**Critical (10)**: Must have for basic functionality
- REQ-ROO-MODE-001: Requirements Stage Mode
- REQ-ROO-MODE-002: Design Stage Mode
- REQ-ROO-MODE-004: Code Stage Mode
- REQ-ROO-CMD-001: Task Checkpoint
- REQ-ROO-CMD-002: Workspace Init
- REQ-ROO-RULE-001: TDD Workflow
- REQ-ROO-RULE-003: REQ Tagging
- REQ-ROO-RULE-005: Key Principles
- REQ-ROO-INSTALL-001: Python Installer
- REQ-ROO-WORKSPACE-002: Roo Structure

**High (13)**: Important for usability
- REQ-ROO-MODE-003: Tasks Stage Mode
- REQ-ROO-MODE-005: System Test Stage Mode
- REQ-ROO-CMD-003: Status Report
- REQ-ROO-CMD-004: Context Refresh
- REQ-ROO-RULE-002: BDD Workflow
- REQ-ROO-RULE-004: Feedback Protocol
- REQ-ROO-INSTALL-002: Project Templates
- REQ-ROO-VALIDATE-001: Traceability Validator
- REQ-ROO-WORKSPACE-001: .ai-workspace Structure
- REQ-ROO-WORKSPACE-003: docs/ Structure
- REQ-ROO-DOC-001: Installation Guide
- REQ-ROO-DOC-002: Mode User Guide

**Medium (7)**: Nice to have for Phase 1
- REQ-ROO-CMD-005: Help System
- REQ-ROO-CMD-006: Commit Helper
- REQ-ROO-CMD-008: Context Snapshot
- REQ-ROO-RULE-006: Workspace Safeguards
- REQ-ROO-VALIDATE-002: Mode Validation
- REQ-ROO-DOC-003: Workflow Examples
- REQ-ROO-DOC-004: Roo Features Guide

**Low (1)**: Defer if time-constrained
- REQ-ROO-CMD-007: Release Management

### Phase 2 (Out of Scope)

**Deferred to v2.0**:
- REQ-ROO-MODE-006: UAT Stage Mode
- REQ-ROO-MODE-007: Runtime Feedback Stage Mode
- All UAT and Runtime Feedback features

---

## Implementation Phasing

### Phase 1A: Foundation (Week 1-2)

**Goal**: Basic scaffolding and core modes

1. **Installer System**:
   - REQ-ROO-INSTALL-001: Python installer
   - REQ-ROO-INSTALL-002: Project templates
   - REQ-ROO-WORKSPACE-001, 002, 003: All workspace structures

2. **Core Rules**:
   - REQ-ROO-RULE-003: REQ Tagging (foundation for everything)
   - REQ-ROO-RULE-004: Feedback Protocol (enables iteration)
   - REQ-ROO-RULE-006: Workspace Safeguards (prevents data loss)

3. **Foundation Modes**:
   - REQ-ROO-MODE-001: Requirements Stage Mode (entry point)
   - REQ-ROO-MODE-004: Code Stage Mode (delivery point)

4. **Basic Commands**:
   - REQ-ROO-CMD-002: Workspace Init (setup)
   - REQ-ROO-CMD-005: Help System (discovery)

**Validation**: Can initialize project, capture requirements, implement with TDD.

### Phase 1B: Complete Workflow (Week 3-4)

**Goal**: Full Requirements → System Test pipeline

1. **Remaining Modes**:
   - REQ-ROO-MODE-002: Design Stage Mode
   - REQ-ROO-MODE-003: Tasks Stage Mode
   - REQ-ROO-MODE-005: System Test Stage Mode

2. **Workflow Rules**:
   - REQ-ROO-RULE-001: TDD Workflow
   - REQ-ROO-RULE-002: BDD Workflow
   - REQ-ROO-RULE-005: Key Principles

3. **Task Management Commands**:
   - REQ-ROO-CMD-001: Task Checkpoint
   - REQ-ROO-CMD-003: Status Report
   - REQ-ROO-CMD-004: Context Refresh

**Validation**: Can execute complete workflow from intent to tested code.

### Phase 1C: Polish (Week 5-6)

**Goal**: Production-ready with validation and docs

1. **Validation System**:
   - REQ-ROO-VALIDATE-001: Traceability Validator
   - REQ-ROO-VALIDATE-002: Mode Validation

2. **Remaining Commands**:
   - REQ-ROO-CMD-006: Commit Helper
   - REQ-ROO-CMD-008: Context Snapshot
   - REQ-ROO-CMD-009: Version Display

3. **Documentation**:
   - REQ-ROO-DOC-001: Installation Guide
   - REQ-ROO-DOC-002: Mode User Guide
   - REQ-ROO-DOC-003: Workflow Examples
   - REQ-ROO-DOC-004: Roo Features Guide

4. **Optional**:
   - REQ-ROO-CMD-007: Release Management (defer if time-constrained)

**Validation**: Comprehensive test suite, production-ready, documented.

---

## Traceability to Platform-Agnostic Requirements

| Roo Requirement | Platform-Agnostic Requirement | Notes |
|-----------------|------------------------------|-------|
| REQ-ROO-MODE-001 | REQ-REQ-001, REQ-AI-003 | Requirements mode implements requirement generation |
| REQ-ROO-MODE-002 | REQ-DES-001, REQ-DES-002, REQ-DES-003 | Design mode implements component design + ADRs |
| REQ-ROO-MODE-003 | REQ-TASK-001, REQ-TASK-003 | Tasks mode implements work breakdown |
| REQ-ROO-MODE-004 | REQ-CODE-001, REQ-CODE-002, REQ-CODE-003, REQ-CODE-004 | Code mode implements TDD + Key Principles |
| REQ-ROO-MODE-005 | REQ-SYSTEST-001, REQ-SYSTEST-002, REQ-SYSTEST-003 | System Test mode implements BDD |
| REQ-ROO-MODE-006 | REQ-UAT-001, REQ-UAT-002 | UAT mode (Phase 2) |
| REQ-ROO-MODE-007 | REQ-RUNTIME-001, REQ-RUNTIME-002, REQ-RUNTIME-003 | Runtime Feedback mode (Phase 2) |
| REQ-ROO-CMD-001 | REQ-TOOL-003, REQ-TASK-001 | Checkpoint implements task management |
| REQ-ROO-CMD-002 | REQ-TOOL-010 | Init implements scaffolding |
| REQ-ROO-CMD-003 | REQ-TOOL-003, REQ-TRACE-001 | Status implements progress tracking |
| REQ-ROO-CMD-004 | REQ-TOOL-003, REQ-TOOL-002 | Refresh implements context restoration |
| REQ-ROO-CMD-005 | REQ-TOOL-003 | Help implements discovery |
| REQ-ROO-CMD-006 | REQ-CODE-003, REQ-TRACE-002 | Commit implements REQ-* tagging |
| REQ-ROO-CMD-007 | REQ-TOOL-005 | Release implements versioning |
| REQ-ROO-CMD-008 | REQ-TOOL-012 | Snapshot implements context preservation |
| REQ-ROO-CMD-009 | REQ-TOOL-003 | Version implements plugin info display |
| REQ-ROO-RULE-001 | REQ-CODE-001 | TDD workflow rule |
| REQ-ROO-RULE-002 | REQ-SYSTEST-001 | BDD workflow rule |
| REQ-ROO-RULE-003 | REQ-TRACE-002, REQ-CODE-003 | REQ tagging rule |
| REQ-ROO-RULE-004 | REQ-STAGE-004, REQ-REQ-003 | Feedback protocol rule |
| REQ-ROO-RULE-005 | REQ-CODE-002 | Key Principles rule |
| REQ-ROO-RULE-006 | REQ-TOOL-002 | Workspace safeguards rule |
| REQ-ROO-INSTALL-001 | REQ-TOOL-010, REQ-TOOL-011 | Python installer |
| REQ-ROO-INSTALL-002 | REQ-TOOL-010 | Project templates |
| REQ-ROO-VALIDATE-001 | REQ-TRACE-003 | Traceability validator |
| REQ-ROO-VALIDATE-002 | REQ-TOOL-011 | Mode validator |
| REQ-ROO-WORKSPACE-* | REQ-TOOL-002, REQ-TOOL-009 | Workspace structure |
| REQ-ROO-DOC-* | REQ-TOOL-001 | Documentation |

---

## Critical Decisions

### Decision 1: Command Delivery Mechanism

**Options**:
1. **Dedicated Command Modes** - Each command is a separate mode (e.g., @mode aisdlc-checkpoint)
2. **Embedded in Stage Modes** - Commands embedded in all modes (keyword detection)
3. **Hybrid** - Some commands as modes, some embedded

**Recommendation**: **Option 1 (Dedicated Command Modes)**

**Rationale**:
- Clean separation of concerns
- Explicit invocation (no keyword ambiguity)
- Mode-specific tool permissions (checkpoint only needs read/edit, not command)
- Easier to maintain and test
- Natural Roo usage pattern (@mode is first-class)

**Trade-offs**:
- More modes to maintain (16 total: 7 stages + 9 commands)
- User must know mode names (mitigated by help system)

### Decision 2: Hook Alternative

**Problem**: Roo Code doesn't support lifecycle hooks (Stop, PreToolUse)

**Options**:
1. **Omit Hooks** - Rely on user discipline (ask them to checkpoint)
2. **Agent Reminders** - Modes proactively suggest checkpointing
3. **Auto-Checkpoint Rule** - Modes auto-checkpoint after N operations
4. **Request Roo Feature** - Ask Roo team to add hook support

**Recommendation**: **Option 2 (Agent Reminders) + Option 3 (Auto-Checkpoint Rule)**

**Rationale**:
- Roo modes can proactively suggest: "You've completed 3 tasks, would you like me to checkpoint?"
- Modes can embed auto-checkpoint logic: "Checkpointing after task completion..."
- Maintains user control while reducing cognitive load
- No platform feature dependency

**Trade-offs**:
- Less robust than hooks (user can ignore reminders)
- Slightly more complex mode instructions

**Implementation**: Add to all modes' customInstructions:
```
## Checkpoint Protocol
After completing significant work (task completion, multiple commits, long session):
1. Suggest: "Would you like me to checkpoint your tasks now?"
2. If user agrees, execute checkpoint workflow
3. Auto-checkpoint if 5+ operations without checkpoint
```

### Decision 3: Validation in CI/CD

**Options**:
1. **Manual Validation** - User runs validate_traceability.py manually
2. **Git Hooks** - Pre-commit/pre-push hooks run validation
3. **CI/CD Integration** - GitHub Actions/GitLab CI runs validation
4. **All Three** - Provide all options

**Recommendation**: **Option 4 (All Three)**

**Rationale**:
- Different teams have different needs
- Git hooks provide fast local feedback
- CI/CD provides gate for main branch
- Manual provides on-demand checking
- Installer can optionally set up git hooks

**Implementation**:
- Installer asks: "Install git hooks for traceability validation? [y/n]"
- Provide example GitHub Action workflow in docs/
- Document manual usage in README

---

## Success Metrics

**Phase 1 MVP is complete when**:
1. ✅ Installer creates complete Roo project structure
2. ✅ All 5 Phase 1 modes are fully functional
3. ✅ All 9 commands are available (as modes or embedded)
4. ✅ All 6 rules are complete and tested
5. ✅ Traceability validator runs successfully
6. ✅ Can execute complete workflow: Intent → Requirements → Design → Tasks → Code → System Test
7. ✅ REQ-* keys propagate through all artifacts (requirements, design, tasks, code, tests)
8. ✅ Documentation enables self-service adoption
9. ✅ Example project demonstrates methodology
10. ✅ Validation suite passes on example project

**Acceptance Test**: Fresh project initialized, authentication feature built end-to-end with full traceability.

---

## Next Steps

1. **Review & Approve**: Stakeholders review this requirements document
2. **Design**: Create detailed design for each component (modes, commands, installer, validator)
3. **Implement Phase 1A**: Foundation (installer, core modes, basic commands)
4. **Validate Phase 1A**: Test scaffolding and basic workflow
5. **Implement Phase 1B**: Complete workflow (remaining modes, rules)
6. **Validate Phase 1B**: Test end-to-end workflow
7. **Implement Phase 1C**: Polish (validation, docs, examples)
8. **Validate Phase 1C**: Comprehensive test suite
9. **Release v1.0**: Phase 1 MVP

---

**Document Status**: Draft - Pending Review
**Author**: AISDLC Requirements Agent
**Last Updated**: 2026-01-20
**Version**: 1.0
**Next Review**: Design stage (create ROO_PARITY_DESIGN.md)
