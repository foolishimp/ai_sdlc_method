# AI SDLC Method Implementation Requirements

**Document Type**: Requirements Specification
**Project**: ai_sdlc_method (self-implementation)
**Version**: 1.0
**Date**: 2025-11-23
**Status**: Bootstrap

---

## Purpose

This document defines the requirements for building the AI SDLC Method tooling itself. These are **implementation requirements** for the system that delivers the methodology defined in [AI_SDLC_REQUIREMENTS.md](AI_SDLC_REQUIREMENTS.md).

**Meta Note**: We are **dogfooding** - using the AI SDLC methodology to build the AI SDLC methodology tooling.

---

## 1. Plugin System

### REQ-F-PLUGIN-001: Plugin System with Marketplace Support

**Priority**: High
**Type**: Functional

**Description**: The system shall provide a plugin architecture that allows methodology, standards, and skills to be packaged and distributed via marketplace.

**Acceptance Criteria**:
- [ ] Plugins can be installed from GitHub marketplace
- [ ] Plugins can be installed from local filesystem
- [ ] Plugin metadata in JSON format (`.claude-plugin/plugin.json`)
- [ ] Plugin discovery via `/plugin` commands
- [ ] Marketplace registry in `marketplace.json`

**Rationale**: Modular, composable context delivery to AI assistants.

**Dependencies**: None (foundation)

---

### REQ-F-PLUGIN-002: Federated Plugin Loading

**Priority**: High
**Type**: Functional

**Description**: The system shall support hierarchical plugin composition where plugins load in order (corporate → division → team → project) with later plugins overriding earlier ones.

**Acceptance Criteria**:
- [ ] Global plugins load from `~/.claude/plugins/`
- [ ] Project plugins load from `./.claude-plugins/`
- [ ] Project plugins override global plugins
- [ ] Configuration deep-merges (primitives replace, objects merge, arrays concatenate)
- [ ] Override priority documented

**Rationale**: Enables corporate standards + division customization + team preferences + project specifics.

**Dependencies**: REQ-F-PLUGIN-001

**Related**: REQ-NFR-FEDERATE-001 (hierarchical composition)

---

### REQ-F-PLUGIN-003: Plugin Bundles

**Priority**: Medium
**Type**: Functional

**Description**: The system shall support plugin bundles that group multiple plugins for common use cases.

**Acceptance Criteria**:
- [ ] Bundle declares dependencies on other plugins
- [ ] Installing bundle installs all dependencies
- [ ] Bundles available: startup, datascience, qa, enterprise
- [ ] Bundle metadata in marketplace.json

**Rationale**: Reduce installation complexity for common scenarios.

**Dependencies**: REQ-F-PLUGIN-001, REQ-F-PLUGIN-004

---

### REQ-F-PLUGIN-004: Plugin Versioning and Dependency Management

**Priority**: High
**Type**: Functional

**Description**: The system shall use semantic versioning (SemVer) for plugins and support dependency declarations with version ranges.

**Acceptance Criteria**:
- [ ] Plugin versions in format: major.minor.patch
- [ ] Dependencies declared in plugin.json
- [ ] Version ranges supported (^1.0.0, >=2.0.0 <3.0.0)
- [ ] Breaking changes → major version bump
- [ ] New features → minor version bump
- [ ] Bug fixes → patch version bump

**Rationale**: Prevents version conflicts, enables safe upgrades.

**Dependencies**: REQ-F-PLUGIN-001

---

## 2. Command System

### REQ-F-CMD-001: Slash Commands for Workflow

**Priority**: High
**Type**: Functional

**Description**: The system shall provide slash commands that integrate with Claude Code to support development workflows.

**Acceptance Criteria**:
- [ ] Commands in `.claude/commands/*.md` format
- [ ] Minimum commands: /start-session, /todo, /finish-task, /commit-task
- [ ] Commands integrate with .ai-workspace/
- [ ] Command installer (setup_commands.py)

**Rationale**: Streamline common development actions.

**Dependencies**: REQ-F-WORKSPACE-001

---

### REQ-F-CMD-002: Persona Management

**Priority**: Low
**Type**: Functional
**Status**: ✅ **Implemented by 7-Stage SDLC Agents** (not commands)

**Description**: The system shall provide role-based personas for different development stages and roles.

**Acceptance Criteria**:
- [x] Requirements agent (.claude/agents/requirements-agent.md)
- [x] Design agent (.claude/agents/design-agent.md)
- [x] Tasks agent (.claude/agents/tasks-agent.md)
- [x] Code agent (.claude/agents/code-agent.md)
- [x] System Test agent (.claude/agents/system-test-agent.md)
- [x] UAT agent (.claude/agents/uat-agent.md)
- [x] Runtime Feedback agent (.claude/agents/runtime-feedback-agent.md)

**Rationale**: Support role-based development workflows through 7-stage SDLC agent system. Agents provide stage-specific focus and perspective.

**Implementation**: 7 agent files in `.claude/agents/` (not slash commands). Vestigial persona commands removed in v0.1.4+.

**Dependencies**: None (agents are part of core methodology)

---

## 3. Developer Workspace

### REQ-F-WORKSPACE-001: Developer Workspace Structure

**Priority**: High
**Type**: Functional

**Description**: The system shall provide a .ai-workspace/ directory structure for task management, session tracking, and templates.

**Acceptance Criteria**:
- [ ] Directory structure: tasks/, session/, templates/, config/
- [ ] Task subdirectories: todo/, active/, finished/, archive/
- [ ] Workspace installer (setup_workspace.py)
- [ ] Git-ignored session/ directory
- [ ] Version-controlled tasks/ and templates/

**Rationale**: Persistent task and session management.

**Dependencies**: None (foundation)

---

### REQ-F-WORKSPACE-002: Task Management Templates

**Priority**: High
**Type**: Functional

**Description**: The system shall provide templates for task management following TDD workflow.

**Acceptance Criteria**:
- [ ] TASK_TEMPLATE.md with acceptance criteria
- [ ] FINISHED_TASK_TEMPLATE.md with problem/solution/lessons
- [ ] ACTIVE_TASKS.md for task tracking

**Rationale**: Structured task documentation.

**Dependencies**: REQ-F-WORKSPACE-001

---

### REQ-F-WORKSPACE-003: Session Tracking Templates

**Priority**: Medium
**Type**: Functional

**Description**: The system shall provide templates for session tracking.

**Acceptance Criteria**:
- [ ] SESSION_TEMPLATE.md with goals/notes/decisions
- [ ] PAIR_PROGRAMMING_GUIDE.md for AI collaboration
- [ ] current_session.md (git-ignored, active session)

**Rationale**: Context preservation across sessions.

**Dependencies**: REQ-F-WORKSPACE-001

---

## 4. Testing Requirements

### REQ-F-TESTING-001: Test Coverage Validation

**Priority**: High
**Type**: Functional

**Description**: The system shall validate that all code has corresponding tests with minimum coverage threshold.

**Acceptance Criteria**:
- [ ] Coverage measurement via pytest-cov
- [ ] Minimum coverage: 80%
- [ ] Coverage reports include requirement traceability
- [ ] Coverage validation in CI/CD

**Rationale**: Ensure code quality via TDD.

**Dependencies**: None

**Related**: Implements Sacred Seven Principle #1 (Test Driven Development)

---

### REQ-F-TESTING-002: Test Generation

**Priority**: Medium
**Type**: Functional

**Description**: The system shall provide skills for automatic test generation when coverage gaps detected.

**Acceptance Criteria**:
- [ ] Detect missing tests (sensor)
- [ ] Generate test templates (actuator)
- [ ] Tests include requirement tags (# Validates: REQ-*)
- [ ] Integration with testing-skills plugin

**Rationale**: Homeostatic test coverage maintenance.

**Dependencies**: REQ-F-TESTING-001

---

## 6. Non-Functional Requirements

### REQ-NFR-TRACE-001: Full Lifecycle Traceability

**Priority**: Critical
**Type**: Non-Functional (Traceability)

**Description**: The system shall maintain traceability from requirements through design, code, tests, and runtime.

**Acceptance Criteria**:
- [ ] All requirement keys follow format: REQ-{TYPE}-{AREA}-{NUMBER}
- [ ] Design documents reference requirements (→ REQ-*)
- [ ] Code includes traceability tags (# Implements: REQ-*)
- [ ] Tests include traceability tags (# Validates: REQ-*)
- [ ] Traceability validation tool (validate_traceability.py)
- [ ] Traceability matrix generated automatically

**Rationale**: Enable requirement tracking for governance and compliance.

**Dependencies**: None (foundation)

---

### REQ-NFR-TRACE-002: Requirement Key Propagation

**Priority**: High
**Type**: Non-Functional (Traceability)

**Description**: The system shall ensure requirement keys propagate through all SDLC stages.

**Acceptance Criteria**:
- [ ] Requirements → unique immutable keys (REQ-*)
- [ ] Design → maps REQ-* to components
- [ ] Tasks → maps REQ-* to Jira tickets
- [ ] Code → tagged with REQ-* in comments
- [ ] Tests → tagged with REQ-* in comments
- [ ] Runtime → logs/metrics tagged with REQ-*

**Rationale**: End-to-end traceability for impact analysis.

**Dependencies**: REQ-NFR-TRACE-001

---

### REQ-NFR-CONTEXT-001: Persistent Context Across Sessions

**Priority**: High
**Type**: Non-Functional (Usability)

**Description**: The system shall preserve context (tasks, decisions, progress) across development sessions.

**Acceptance Criteria**:
- [ ] Session state in .ai-workspace/session/
- [ ] Active tasks persist in ACTIVE_TASKS.md
- [ ] Finished tasks archived in finished/
- [ ] Context loadable via /load-context

**Rationale**: Reduce context-switching overhead.

**Dependencies**: REQ-F-WORKSPACE-001

---

### REQ-NFR-FEDERATE-001: Hierarchical Configuration Composition

**Priority**: High
**Type**: Non-Functional (Architecture)

**Description**: The system shall support hierarchical configuration where configurations merge from corporate → division → team → project levels.

**Acceptance Criteria**:
- [ ] Configurations load in priority order
- [ ] Later configs override earlier configs
- [ ] Deep merge for objects (recursive)
- [ ] Array concatenation (deduplicated)
- [ ] Primitive replacement

**Rationale**: Balance standardization and customization.

**Dependencies**: REQ-F-PLUGIN-002

---

### REQ-NFR-COVERAGE-001: Test Coverage Minimum

**Priority**: High
**Type**: Non-Functional (Quality)

**Description**: The system shall maintain minimum test coverage of 80% for all production code.

**Acceptance Criteria**:
- [ ] Coverage measured via pytest-cov
- [ ] Coverage reported in CI/CD
- [ ] Coverage gates prevent merging <80%
- [ ] Exclude patterns: migrations/, generated/

**Rationale**: Ensure code quality.

**Dependencies**: REQ-F-TESTING-001

---

## 7. Requirement Summary

**Total Implementation Requirements**: 20
- Functional (F): 13
- Non-Functional (NFR): 7

**By Category**:
- Plugin System: 4
- Command System: 3
- Workspace: 3
- TODO System: 3
- Testing: 2
- Traceability: 2
- Other NFR: 3

**By Priority**:
- Critical: 1 (REQ-NFR-TRACE-001)
- High: 12
- Medium: 5
- Low: 2

**Status**:
- ✅ Implemented but untagged: 16 (design exists, code exists, no traceability tags)
- ⚠️ Partially implemented: 3 (REQ-F-PLUGIN-004, REQ-F-CMD-002, REQ-F-TESTING-002)
- ❌ Not implemented: 0

---

## Traceability to Design

- REQ-F-PLUGIN-* → [PLUGIN_ARCHITECTURE.md](../design/PLUGIN_ARCHITECTURE.md)
- REQ-F-CMD-* → [COMMAND_SYSTEM.md](../design/COMMAND_SYSTEM.md) (to be created)
- REQ-F-WORKSPACE-* → [TEMPLATE_SYSTEM.md](../design/TEMPLATE_SYSTEM.md)
- REQ-F-TESTING-* → testing-skills plugin
- REQ-NFR-TRACE-* → validate_traceability.py
- REQ-NFR-CONTEXT-* → .ai-workspace/ structure
- REQ-NFR-FEDERATE-* → Plugin loading mechanism

---

## Example Requirements

Example requirements demonstrating the methodology have been moved to:
- [examples/AI_SDLC_REQUIREMENTS.md](examples/AI_SDLC_REQUIREMENTS.md) - Complete 7-stage methodology examples
- [examples/AI_SDLC_OVERVIEW.md](examples/AI_SDLC_OVERVIEW.md) - Overview examples
- [examples/AI_SDLC_CONCEPTS.md](examples/AI_SDLC_CONCEPTS.md) - Conceptual examples
- [examples/FOLDER_BASED_REQUIREMENTS.md](examples/FOLDER_BASED_REQUIREMENTS.md) - Discovery examples

These demonstrate HOW to use the methodology, not how to BUILD ai_sdlc_method itself.

---

## Next Steps

1. **Add traceability tags to code** - Tag all implementations with `# Implements: REQ-*`
2. **Add traceability tags to tests** - Tag all tests with `# Validates: REQ-*`
3. **Validate traceability** - Run `python installers/validate_traceability.py --check-all`
4. **Generate matrix** - Run `python installers/validate_traceability.py --matrix > docs/TRACEABILITY_MATRIX.md`
5. **Complete missing design docs** - COMMAND_SYSTEM.md, TEMPLATE_SYSTEM.md

---

**Document Status**: Bootstrap - Requirements extracted from existing design and code
**Next Review**: After traceability tags added to code
