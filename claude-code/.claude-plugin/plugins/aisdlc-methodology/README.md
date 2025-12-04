# AI SDLC Methodology Plugin - Complete 7-Stage Framework

**Version**: 3.0.0
**Author**: foolishimp
**Reference Guide**: [AI SDLC Methodology](../../docs/ai_sdlc_method.md)

## Overview

This plugin provides a complete **7-stage AI SDLC methodology** with fully specified AI agent configurations for each stage. It extends the foundational Key Principles principles with end-to-end lifecycle management from intent to runtime feedback.

**This is the master plugin** that contains all organizational elements for the AI SDLC framework:
- **Commands** - Slash commands for workflow (`/aisdlc-*`)
- **Agents** - Stage-specific personas for each SDLC stage
- **Templates** - Workspace scaffolding (`.ai-workspace/`)
- **Configuration** - Stage specifications and principles

### Plugin Structure

```
aisdlc-methodology/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── commands/                  # Slash commands
│   ├── aisdlc-checkpoint-tasks.md
│   ├── aisdlc-commit-task.md
│   ├── aisdlc-finish-task.md
│   ├── aisdlc-help.md
│   ├── aisdlc-init.md
│   ├── aisdlc-refresh-context.md
│   ├── aisdlc-release.md
│   ├── aisdlc-status.md
│   └── aisdlc-version.md
├── agents/                    # Stage personas
│   ├── aisdlc-requirements-agent.md
│   ├── aisdlc-design-agent.md
│   ├── aisdlc-tasks-agent.md
│   ├── aisdlc-code-agent.md
│   ├── aisdlc-system-test-agent.md
│   ├── aisdlc-uat-agent.md
│   └── aisdlc-runtime-feedback-agent.md
├── templates/                 # Workspace scaffolding
│   └── .ai-workspace/
│       ├── tasks/
│       ├── templates/
│       └── config/
├── config/                    # Stage specifications
│   ├── stages_config.yml
│   └── config.yml
└── docs/                      # Documentation
    ├── principles/
    ├── processes/
    └── guides/
```

### What's New in 3.0

- ✨ **7 Complete Stage Configurations**: Requirements, Design, Tasks, Code, System Test, UAT, Runtime Feedback
- 🤖 **AI Agent Specifications**: Each stage has detailed agent responsibilities and constraints
- 🔗 **Full Traceability**: Requirement key propagation through all stages
- 🔄 **Feedback Loops**: Bi-directional traceability from Runtime → Requirements → Intent
- 📊 **Concurrent Execution**: Support for parallel sub-vector SDLCs
- 🎯 **Context-Driven**: Standards, templates, and constraints guide each stage

## Architecture

```
AI SDLC Pipeline
┌─────────────┐
│   Intent    │  Raw business needs, problems, goals
│  Manager    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐  ◄──────────────┐
│ 1. AISDLC           │                  │
│    Requirements     │  Feedback Loop   │
│    Agent            │  (All stages     │
│    (Section 4.0)    │   feed back)     │
└──────┬──────────────┘                  │
       │                                  │
       ▼                                  │
┌─────────────────────┐                  │
│ 2. AISDLC Design    │                  │
│    Agent            │                  │
│    (Section 5.0)    │                  │
└──────┬──────────────┘                  │
       │                                  │
       ▼                                  │
┌─────────────────────┐                  │
│ 3. AISDLC Tasks     │  ◄─ Jira         │
│    Orchestrator     │     Integration  │
│    (Section 6.0)    │                  │
└──────┬──────────────┘                  │
       │                                  │
       ▼                                  │
┌─────────────────────┐                  │
│ 4. AISDLC Code      │  TDD Cycle       │
│    Agent            │  RED→GREEN       │
│    (Section 7.0)    │  →REFACTOR       │
│    [Key Principles]   │                  │
└──────┬──────────────┘                  │
       │                                  │
       ▼                                  │
┌─────────────────────┐                  │
│ 5. AISDLC System    │  BDD Testing     │
│    Test Agent       │  (Given/When/    │
│    (Section 8.0)    │   Then)          │
└──────┬──────────────┘                  │
       │                                  │
       ▼                                  │
┌─────────────────────┐                  │
│ 6. AISDLC UAT       │  Business        │
│    Agent            │  Validation      │
│    (Section 9.0)    │                  │
└──────┬──────────────┘                  │
       │                                  │
       ▼                                  │
┌─────────────────────┐                  │
│ 7. AISDLC Runtime   │  Production      │
│    Feedback Agent   │  Telemetry   ────┘
│    (Section 10.0)   │
└─────────────────────┘
```

## The 7 Stages

### 1. Requirements Stage (Section 4.0)

**Agent**: AISDLC Requirements Agent
**Purpose**: Transform intent into structured requirements with unique, immutable keys

**Key Responsibilities**:
- Parse raw intent from Intent Manager
- Generate requirement artifacts (user stories, NFRs, data requirements)
- Assign unique requirement keys (`REQ-F-*`, `REQ-NFR-*`, `REQ-DATA-*`)
- Process feedback from all downstream stages
- Maintain bi-directional traceability

**Quality Gates**:
- All requirements have unique keys
- All requirements have acceptance criteria
- Product Owner / Business Analyst / Data Steward review

**Outputs**:
- `<REQ-ID>`: Functional requirements
- `REQ-NFR-PERF-001`: Non-functional requirements
- `REQ-DATA-CQ-001`: Data quality requirements
- `REQ-BR-CALC-001`: Business rules

---

### 2. Design Stage (Section 5.0)

**Agent**: AISDLC Design Agent / Solution Designer
**Purpose**: Transform requirements into implementable technical and data solution

**Key Responsibilities**:
- Analyze requirements and extract specifications
- Apply architectural patterns from context
- Design components, APIs, and data models
- Generate traceability matrix (100% requirement coverage)
- Document trade-offs in Architecture Decision Records (ADRs)

**Quality Gates**:
- 100% requirement coverage in design
- All components mapped to requirement keys
- Architecture/Data/Security reviews complete

**Outputs**:
- Component diagrams
- Data models (conceptual, logical, physical)
- API specifications
- Data flow diagrams
- Design-to-Requirement Traceability Matrix

---

### 3. Tasks / Work Breakdown Stage (Section 6.0)

**Agent**: AISDLC Tasks Stage Orchestrator
**Purpose**: Convert design into actionable work units with Jira integration and agent orchestration

**Dual Purpose**:
1. **Work Planning**: Decompose design into estimable work units
2. **Agent Orchestration**: Assign work units to developer agents and monitor execution

**Key Responsibilities**:
- Generate epics, user stories, technical tasks, data tasks
- Estimate work units (story points/hours)
- Identify dependencies and critical path
- Create/update Jira tickets with requirement key tagging
- Monitor TDD cycle execution by Code agents
- Track test coverage gates (≥80%, critical paths 100%)

**Quality Gates**:
- All tasks linked to requirement keys
- All tasks estimated
- Capacity validated
- Dependencies identified

**Outputs**:
- Jira tickets (epics, stories, subtasks)
- Dependency graph
- Capacity utilization report
- Requirement coverage matrix

---

### 4. Code Stage (Section 7.0) - TDD-Driven

**Agent**: AISDLC Code Agent / Developer Agent
**Purpose**: Implement solution using Test-Driven Development

**Methodology**: **RED → GREEN → REFACTOR → COMMIT**

**Key Responsibilities**:
- Receive work units from Tasks Stage
- Execute TDD cycle for every change
- Write tests first (Principle #1: No code without tests)
- Tag all code with requirement keys
- Maintain ≥80% test coverage (critical paths 100%)

**Key Principles Integration**:
- Principle #1: Test Driven Development (TDD mandatory)
- Principle #2: Fail Fast & Root Cause (tests fail loudly)
- Principle #3: Modular & Maintainable (single responsibility)

**Quality Gates**:
- All code has tests
- Test coverage ≥80% (critical paths 100%)
- All tests passing
- Code tagged with requirement keys
- Security scan passes

**Outputs**:
- Production code with requirement key tags
- Test code (unit, integration)
- Git commits with requirement traceability

---

### 5. System Test Stage (Section 8.0) - BDD-Driven

**Agent**: AISDLC System Test Agent / QA Agent
**Purpose**: Verify integrated system behavior using BDD

**Methodology**: **Given/When/Then** scenarios

**Key Responsibilities**:
- Generate BDD scenarios from requirements
- Implement step definitions (Behave/Cucumber/SpecFlow)
- Perform coverage analysis (≥95% requirement coverage)
- Validate data quality and performance
- Provide feedback to Requirements for gaps

**Quality Gates**:
- All requirements have ≥1 BDD scenario
- Requirement coverage ≥95%
- All scenarios pass
- No critical defects
- QA Lead approval

**Outputs**:
- BDD feature files (Gherkin format)
- Step definitions (automated tests)
- Coverage matrix (scenario-to-requirement)
- Test reports

---

### 6. UAT Stage (Section 9.0) - BDD for Business

**Agent**: AISDLC UAT Agent
**Purpose**: Business validation through pure business language BDD

**Three Parallel Activities**:
1. **Manual UAT Test Cases** (Business SMEs)
2. **Automated UAT Tests** (QA Engineers)
3. **Automated Data Tests** (QA Engineers)

**Key Responsibilities**:
- Support manual test case creation in business language
- Convert UAT scripts to automated BDD tests
- Generate data validation tests
- Track requirement-to-test traceability
- Facilitate business sign-off

**Quality Gates**:
- All scenarios executed
- Business sign-off obtained
- Data validation complete
- No critical defects

**Sign-Off Authorities**:
- Business SME
- Business Data Steward
- UAT Lead
- Compliance Officer (if applicable)

**Outputs**:
- Manual UAT test cases (Given/When/Then)
- Automated UAT tests (BDD)
- Automated data tests (Great Expectations, dbt)
- Sign-off document with requirement status

---

### 7. Runtime Feedback Stage (Section 10.0)

**Agent**: AISDLC Runtime Feedback Agent
**Purpose**: Close feedback loop between production and requirements

**Key Responsibilities**:
- Parse release manifests with requirement keys
- Aggregate telemetry from observability platforms
- Link alerts to requirement keys
- Perform root cause and trend analysis
- Generate new intents from runtime observations

**Quality Gates**:
- All deployed code tagged with requirement keys
- Telemetry systems capture requirement keys
- Alerts routed to Intent Manager
- Traceability complete

**Outputs**:
- Release manifests with requirement traceability
- Runtime telemetry (tagged with REQ keys)
- Alerts linked to requirements
- Feedback reports (new intents)
- Traceability reports (impact analysis)

---

## Key Principles

### Requirement Key Traceability

Every artifact at every stage is tagged with requirement keys:

```
Intent
  ↓
<REQ-ID> (User Login)
  ↓
Design: AuthenticationService → <REQ-ID>
  ↓
Jira: PROJ-123 → <REQ-ID>
  ↓
Code: auth_service.py # Implements: <REQ-ID>
  ↓
Tests: test_auth.py # Validates: <REQ-ID>
  ↓
BDD: "Given user has credentials..." → <REQ-ID>
  ↓
UAT: Manual test case → <REQ-ID>
  ↓
Runtime: ERROR: <REQ-ID> - Auth failure
  ↓
Feedback: New intent to improve auth UX
```

### Feedback Loops

**Forward Traceability**: Intent → Requirements → Design → Tasks → Code → Tests → UAT → Runtime

**Backward Traceability**: Production Issues → Requirement → Code → Design → Intent

All stages feed discoveries back to Requirements stage, ensuring Requirements remain the single source of truth.

### Concurrent Execution

Multiple sub-vector SDLCs can run concurrently:
- Architecture SDLC runs before Code SDLC
- UAT Test SDLC runs in parallel with Code SDLC
- Data Pipeline SDLC runs alongside Application SDLC

**Principle**: When a common asset like Requirements exists, all dependent tasks can trigger and run concurrently.

## Configuration Files

### `config/stages_config.yml`
Complete 7-stage agent configuration with:
- Agent responsibilities
- Inputs/Outputs
- Quality gates
- Context constraints
- Key principles

### `config/config.yml`
Key Principles principles and TDD workflow (foundation for Code Stage)

### Reference: `../../docs/ai_sdlc_method.md`
Complete AI SDLC methodology documentation (Sections 1.0-13.0)

## Usage

### Loading the Plugin

```yaml
# In your project's ai_sdlc_method configuration
methodology:
  base: "file://plugins/aisdlc-methodology/config/stages_config.yml"
  key.principles: "file://plugins/aisdlc-methodology/config/config.yml"
```

### Using Stage Agents

Each stage agent can be configured with:
- Stage-specific context (standards, templates, constraints)
- Quality gates and governance requirements
- Persona collaboration rules
- Traceability requirements

### Example: AISDLC Requirements Agent Configuration

```yaml
requirements_agent:
  inputs:
    - intent_from: "Intent Manager"
    - feedback_from: ["design", "tasks", "code", "test", "uat", "runtime"]

  outputs:
    - user_stories: "REQ-F-*"
    - nfrs: "REQ-NFR-*"
    - data_requirements: "REQ-DATA-*"

  quality_gates:
    - unique_keys: true
    - acceptance_criteria: required
    - product_owner_review: required
```

## Integration with Key Principles

The Code Stage (Section 7.0) fully integrates the Key Principles principles:

1. **Test Driven Development** → TDD cycle mandatory (RED → GREEN → REFACTOR)
2. **Fail Fast & Root Cause** → Tests fail loudly, no workarounds
3. **Modular & Maintainable** → Single responsibility, loose coupling
4. **Reuse Before Build** → Check existing code first
5. **Open Source First** → Suggest alternatives, human decides
6. **No Legacy Baggage** → Clean slate, no debt
7. **Perfectionist Excellence** → Quality over quantity

**Ultimate Mantra**: **"Excellence or nothing"** 🔥

## Benefits

✅ **Complete Lifecycle Coverage**: 7 stages from Intent to Runtime Feedback
✅ **End-to-End Traceability**: Requirement keys flow through entire pipeline
✅ **AI Agent Ready**: Detailed specifications for each stage agent
✅ **Feedback-Driven**: Continuous improvement through closed loops
✅ **Concurrent Execution**: Support for parallel sub-vector SDLCs
✅ **Context-Driven**: Standards and templates guide all stages
✅ **Data as First-Class**: Data requirements have parity with functional requirements
✅ **Key Principles Foundation**: Code stage built on proven principles

## Version History

### 3.0.0 (2025-11-26)
- **Unified Plugin Architecture**: Consolidated all Claude Code features into this plugin
- Added `commands/` directory with 7 slash commands
- Added `agents/` directory with 7 stage persona agents
- Added `templates/` directory with workspace scaffolding
- Updated plugin.json with commands and agents paths
- Follows ADR-006: Plugin Configuration and Discovery

### 2.0.0 (2025-01-14)
- Added complete 7-stage agent configurations
- Integrated full AI SDLC methodology from reference guide
- Added Jira integration and agent orchestration to Tasks stage
- Added BDD methodology to System Test and UAT stages
- Added Runtime Feedback stage with observability integration
- Updated plugin.json with stage metadata

### 1.0.0 (2025-10-17)
- Initial release with Key Principles principles
- TDD workflow for Code stage
- Pair programming and session management guides

## References

- **AI SDLC Method**: `../../docs/ai_sdlc_method.md`
- **Key Principles**: `docs/principles/KEY_PRINCIPLES.md`
- **TDD Workflow**: `docs/processes/TDD_WORKFLOW.md`
- **Pair Programming**: `docs/guides/PAIR_PROGRAMMING_WITH_AI.md`

## License

MIT License - See LICENSE file

## Author

foolishimp - https://github.com/foolishimp/ai_sdlc_method
