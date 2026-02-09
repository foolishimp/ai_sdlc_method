# CLAUDE.md - ai_sdlc_method Project Guide

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**ai_sdlc_method** provides a complete **Intent-Driven AI SDLC Methodology** with full lifecycle traceability from intent to runtime.

### Purpose

Enable AI-augmented software development where:
1. **7-Stage Lifecycle** - Complete SDLC from Requirements to Runtime Feedback
2. **Requirement Traceability** - Track REQ keys (REQ-F-*, REQ-NFR-*, REQ-DATA-*) through all stages
3. **AI Agent Configurations** - Detailed specifications for AI agents at each SDLC stage
4. **Bidirectional Feedback** - Production issues flow back to requirements and generate new intents
5. **Claude Code Plugins** - Installable methodology and standards as plugins
6. **Federated Architecture** - Compose contexts across corporate → division → team → project

### Key Features

- [COMPLETE] **Complete 7-Stage Methodology** - Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
- [COMPLETE] **Key Principles** - Foundation for Code stage (TDD, Fail Fast, Modular, etc.)
- [COMPLETE] **TDD Workflow** - RED → GREEN → REFACTOR → COMMIT cycle
- [COMPLETE] **BDD Testing** - Given/When/Then scenarios for System Test and UAT stages
- [COMPLETE] **AI Agent Specifications** - 1,273-line configuration file with detailed agent specs
- [COMPLETE] **Requirement Key Tagging** - Automatic propagation of REQ keys from intent to runtime

---

## Project Structure

```
ai_sdlc_method/
├── docs/                        # Core documentation
│   ├── requirements/            # Methodology and implementation requirements
│   │   ├── AI_SDLC_REQUIREMENTS.md   # Complete methodology (Sections 1-13, ~2,950 lines)
│   │   ├── AI_SDLC_OVERVIEW.md       # High-level introduction
│   │   ├── AI_SDLC_CONCEPTS.md       # Exhaustive concept inventory
│   │   ├── AI_SDLC_APPENDICES.md     # Technical deep-dives (category theory, ecosystem)
│   │   ├── AISDLC_IMPLEMENTATION_REQUIREMENTS.md  # Platform-agnostic implementation reqs
│   │   └── INTENT.md                 # Project intent document
│   ├── TRACEABILITY_MATRIX.md   # Requirements traceability across phases
│   ├── guides/                  # Role-specific application guides
│   │   └── PLUGIN_GUIDE.md      # Plugin creation and usage guide
│   ├── README.md                # Documentation index with role-based learning paths
│   └── deprecated/              # Archive of previous versions
│
├── claude-code/.claude-plugin/plugins/  # Claude Code plugins and skills
│   ├── aisdlc-methodology/      # 7-stage methodology plugin (v2.0.0)
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json      # Plugin metadata
│   │   ├── config/
│   │   │   ├── stages_config.yml  # 7-stage agent specifications (1,273 lines)
│   │   │   └── config.yml         # Key Principles + Code stage config
│   │   ├── docs/
│   │   │   ├── principles/KEY_PRINCIPLES.md
│   │   │   └── processes/TDD_WORKFLOW.md
│   │   └── README.md            # Plugin overview
│   ├── python-standards/        # Python language standards plugin
│   └── code-skills/             # Code generation skills plugin
│
├── installers/                  # Python installation scripts
│   └── README.md                # Installation scripts documentation
│
├── .claude-plugin/              # Root plugin metadata
├── marketplace.json             # Claude Code marketplace registry
├── README.md                    # Project overview
├── QUICKSTART.md                # Quick start guide
└── CLAUDE.md                    # This file
```

---

## Context Auto-Loading

**IMPORTANT**: This project uses an **implicit session model** where context loads automatically when Claude Code starts.

### What Auto-Loads

When you open this project in Claude Code, the following context is automatically available:

1. **This file (CLAUDE.md)** - Project guide, methodology overview, development guidelines
2. **Method Reference** - `.ai-workspace/templates/AISDLC_METHOD_REFERENCE.md` (workspace structure, workflow patterns)
3. **Active Tasks + Work Context** - `.ai-workspace/tasks/active/ACTIVE_TASKS.md` (single file with everything)

**One File. That's It.**

### No Explicit Session Start Needed

**You do NOT need to run `/aisdlc-start-session`** - that command has been removed.

- **Session = Context** - Your "session" is simply your current working context
- **Context persists** - Automatically saved via `/aisdlc-checkpoint-tasks`
- **No ceremony** - Just open Claude and start working
- **One file** - ACTIVE_TASKS.md has both tasks and work context

### How It Works

```
Open Claude → CLAUDE.md mentions ACTIVE_TASKS.md → Work → /aisdlc-checkpoint-tasks → Close
                          ↑                                         ↓
                          └──────── Context persists in one file ──┘
```

### The One File: ACTIVE_TASKS.md

This single file contains:
- **Active Tasks** - All your current work items with status
- **Summary** - Task counts and recently completed
- **Recovery Commands** - Quick commands to regain context

Simple. Just tasks. Context comes from conversation history.

### Checkpointing Your Work

Use **`/aisdlc-checkpoint-tasks`** to save your work:
- Updates task status (completed, in-progress, blocked)
- Creates finished task documentation for completed work
- Updates ACTIVE_TASKS.md with current state
- Moves completed tasks to "Recently Completed" section

### Quick Recovery

If you need to quickly understand where you are:
```bash
cat .ai-workspace/tasks/active/ACTIVE_TASKS.md  # Everything is here
git status                                       # Current git state
```

---

## The 7-Stage AI SDLC Methodology

### Complete Lifecycle

```
Intent → Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
           ↑                                                                    ↓
           └────────────────────── Feedback Loop ──────────────────────────────┘
```

### Stage Details

#### 1. Requirements Stage (Section 4.0)
**Agent**: AISDLC Requirements Agent
**Purpose**: Transform intent into structured requirements with unique, immutable keys
**Input**: Raw intent from Intent Manager
**Output**:
- REQ-F-* (functional requirements)
- REQ-NFR-* (non-functional requirements)
- REQ-DATA-* (data quality requirements)
- REQ-BR-* (business rules)

#### 2. Design Stage (Section 5.0)
**Agent**: AISDLC Design Agent / Solution Designer
**Purpose**: Transform requirements into technical solution architecture
**Input**: Structured requirements from Requirements stage
**Output**: Component diagrams, data models, API specs, ADRs, traceability matrix

#### 3. Tasks Stage (Section 6.0)
**Agent**: AISDLC Tasks Stage Orchestrator
**Purpose**: Break design into work units and orchestrate Jira workflow
**Input**: Design artifacts
**Output**: Jira tickets with requirement tags, dependency graph, capacity planning

#### 4. Code Stage (Section 7.0)
**Agent**: AISDLC Code Agent / Developer Agent
**Purpose**: Implement work units using TDD workflow
**Input**: Work units from Tasks stage
**Output**: Production code with requirement tags, unit tests, integration tests
**Methodology**: TDD (RED → GREEN → REFACTOR) + Key Principles

#### 5. System Test Stage (Section 8.0)
**Agent**: AISDLC System Test Agent / QA Agent
**Purpose**: Create BDD integration tests validating requirements
**Input**: Deployed code
**Output**: BDD feature files (Gherkin), step definitions, coverage matrix
**Methodology**: BDD (Given/When/Then)

#### 6. UAT Stage (Section 9.0)
**Agent**: AISDLC UAT Agent
**Purpose**: Business validation and sign-off
**Input**: System test passed
**Output**: Manual UAT test cases, automated UAT tests, business sign-off
**Methodology**: BDD in pure business language

#### 7. Runtime Feedback Stage (Section 10.0)
**Agent**: AISDLC Runtime Feedback Agent
**Purpose**: Close the feedback loop from production to requirements
**Input**: Production deployment
**Output**: Release manifests, runtime telemetry (tagged with REQ keys), alerts, new intents

---

## Requirement Traceability Example

```
Intent: INT-001 "Customer self-service portal"
  ↓
Requirements: REQ-F-AUTH-001 "User login with email/password"
  ↓
Design: AuthenticationService → REQ-F-AUTH-001
  ↓
Tasks: PORTAL-123 (Jira ticket) → REQ-F-AUTH-001
  ↓
Code: auth_service.py
      # Implements: REQ-F-AUTH-001
      def login(email, password):
          ...
  ↓
Tests: test_auth.py # Validates: REQ-F-AUTH-001
       auth.feature # BDD: Given/When/Then for REQ-F-AUTH-001
  ↓
UAT: UAT-001 → REQ-F-AUTH-001 (Business sign-off [COMPLETE])
  ↓
Runtime: Datadog alert: "ERROR: REQ-F-AUTH-001 - Auth timeout"
  ↓
Feedback: New intent: INT-042 "Fix auth timeout"
  [Cycle repeats...]
```

---

## Common Operations

### Using the Methodology

```bash
# Install Claude Code plugin
/plugin marketplace add foolishimp/ai_sdlc_method
/plugin install @aisdlc/aisdlc-methodology

# Claude now has access to complete 7-stage methodology
```

### Ask Claude to Follow 7-Stage Process

```
You: "Implement authentication feature using AI SDLC methodology"

Claude will guide you through:
1. Requirements: Generate REQ-F-AUTH-001, REQ-NFR-PERF-001, etc.
2. Design: Create AuthenticationService component, API specs
3. Tasks: Break into Jira tickets (PORTAL-123) with REQ tags
4. Code: TDD implementation (RED → GREEN → REFACTOR)
5. System Test: BDD scenarios (Given/When/Then)
6. UAT: Business validation test cases
7. Runtime Feedback: Setup telemetry with REQ key tagging
```

### Accessing the Methodology

```python
from pathlib import Path
import yaml

# Load 7-stage methodology configuration
stages_config = Path("claude-code/plugins/aisdlc-methodology/config/stages_config.yml")
with open(stages_config) as f:
    methodology = yaml.safe_load(f)

# Access stage specifications
requirements_stage = methodology['ai_sdlc']['stages']['requirements']
code_stage = methodology['ai_sdlc']['stages']['code']

# Get agent configuration
requirements_agent = requirements_stage['agent']
print(f"Role: {requirements_agent['role']}")
print(f"Purpose: {requirements_agent['purpose']}")

# Get Key Principles
key_principles = code_stage['key_principles']
print(f"TDD Workflow: {key_principles['tdd']['workflow']}")
```

---

## Development Methodology

**IMPORTANT**: This project follows the **Key Principles**, which are integrated as the foundation for the Code stage (Section 7.0) in the complete 7-stage AI SDLC methodology.

### The Key Principles

1. **Test Driven Development** - "No code without tests"
2. **Fail Fast & Root Cause** - "Break loudly, fix completely"
3. **Modular & Maintainable** - "Single responsibility, loose coupling"
4. **Reuse Before Build** - "Check first, create second"
5. **Open Source First** - "Suggest alternatives, human decides"
6. **No Legacy Baggage** - "Clean slate, no debt"
7. **Perfectionist Excellence** - "Best of breed only"

**Read Full Principles**: [KEY_PRINCIPLES.md](claude-code/.claude-plugin/plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md)

### TDD Workflow (Code Stage)

**Always follow**: RED → GREEN → REFACTOR → COMMIT

1. **RED**: Write failing test first
2. **GREEN**: Write minimal code to pass
3. **REFACTOR**: Improve code quality
4. **COMMIT**: Save with clear message (tagged with REQ key)
5. **REPEAT**: Next test

**No code without tests. Ever.**

**Read Full Workflow**: [TDD_WORKFLOW.md](claude-code/.claude-plugin/plugins/aisdlc-methodology/docs/processes/TDD_WORKFLOW.md)

### Before You Code (7 Questions)

Ask these seven questions:

1. Have I written tests first? (Principle #1)
2. Will this fail loudly if wrong? (Principle #2)
3. Is this module focused? (Principle #3)
4. Did I check if this exists? (Principle #4)
5. Have I researched alternatives? (Principle #5)
6. Am I avoiding tech debt? (Principle #6)
7. Is this excellent? (Principle #7)

**If not "yes" to all seven, don't code yet.**

---

## Key Documentation

### Must-Read Documents

1. **[docs/requirements/AI_SDLC_REQUIREMENTS.md](docs/requirements/AI_SDLC_REQUIREMENTS.md)** - Complete 7-stage methodology (~2,950 lines)
   - Section 1.0: Introduction
   - Section 2.0: End-to-End Intent Lifecycle
   - Section 3.0: Builder Pipeline Overview
   - Section 4.0: Requirements Stage
   - Section 5.0: Design Stage
   - Section 6.0: Tasks Stage
   - Section 7.0: Code Stage (Key Principles + TDD)
   - Section 8.0: System Test Stage (BDD)
   - Section 9.0: UAT Stage
   - Section 10.0: Runtime Feedback Stage
   - Section 11.0: End-to-End Requirement Traceability
   - Section 12.0: AI SDLC Sub-Vectors
   - Section 13.0: Conclusion

2. **[claude-code/plugins/aisdlc-methodology/config/stages_config.yml](claude-code/plugins/aisdlc-methodology/config/stages_config.yml)** - 7-stage agent specifications (1,273 lines)

3. **[ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples)** - Complete 7-stage example projects (separate repo)

### Role-Based Learning Paths

See [docs/README.md](docs/README.md) for learning paths tailored to:
- Business Analysts / Product Owners → Focus on Requirements & UAT stages
- Architects / Technical Leads → Focus on Design stage
- Developers → Focus on Code stage (TDD + Key Principles)
- QA Engineers → Focus on System Test & UAT stages (BDD)
- DevOps / SRE → Focus on Runtime Feedback stage
- Project Managers / Scrum Masters → Focus on Tasks stage

---

## Development Guidelines

### Implementing a New Feature (7-Stage Process)

1. **Requirements Stage**: Generate REQ-* keys
   ```yaml
   - REQ-F-AUTH-001: "User login with email/password"
   - REQ-NFR-PERF-001: "Login response < 500ms"
   - REQ-DATA-001: "Email must be valid format"
   ```

2. **Design Stage**: Create technical solution
   ```yaml
   Component: AuthenticationService
   API: POST /api/v1/auth/login
   Data Model: User table (email, password_hash)
   Dependencies: ValidationService, TokenService
   ```

3. **Tasks Stage**: Break into work units
   ```yaml
   - PORTAL-123: Implement AuthenticationService (REQ-F-AUTH-001)
   - PORTAL-124: Add validation (REQ-DATA-001)
   - PORTAL-125: Optimize performance (REQ-NFR-PERF-001)
   ```

4. **Code Stage**: TDD implementation
   ```python
   # RED: Write failing test
   def test_user_login_with_valid_credentials():
       user = create_test_user()
       result = login(user.email, "password123")
       assert result.success == True

   # GREEN: Implement minimal solution
   # Implements: REQ-F-AUTH-001
   def login(email: str, password: str) -> LoginResult:
       user = User.get_by_email(email)
       if user and user.check_password(password):
           return LoginResult(success=True, user=user)
       return LoginResult(success=False)

   # REFACTOR: Improve code quality
   # (Add logging, error handling, type hints, etc.)

   # COMMIT: Save with REQ tag
   git commit -m "Add user login (REQ-F-AUTH-001)"
   ```

5. **System Test Stage**: BDD scenarios
   ```gherkin
   Feature: User Authentication
     # Validates: REQ-F-AUTH-001

     Scenario: Successful login
       Given I am on the login page
       When I enter valid email "user@example.com"
       And I enter valid password "password123"
       And I click "Login"
       Then I should see "Welcome back"
   ```

6. **UAT Stage**: Business validation
   ```yaml
   UAT-001:
     title: "Validate user login flow"
     requirement: REQ-F-AUTH-001
     tester: Business Analyst
     status: APPROVED
   ```

7. **Runtime Feedback Stage**: Telemetry
   ```python
   # Tag metrics with requirement keys
   logger.info("User login", extra={
       "requirement": "REQ-F-AUTH-001",
       "latency_ms": 120,
       "success": True
   })

   # If production issue occurs
   Alert: "ERROR: REQ-F-AUTH-001 - Auth timeout"
   → Traces back to requirements
   → Generates new intent: INT-042 "Fix auth timeout"
   ```

### Code Standards

- **Tests first** (always RED → GREEN → REFACTOR)
- **Tag code with REQ keys** (# Implements: REQ-F-AUTH-001)
- Use type hints
- Follow PEP 8 (for Python projects)
- Add docstrings to all public methods
- Keep functions focused and small
- No technical debt

---

## Plugin System

### Creating a Project Plugin

See [docs/guides/PLUGIN_GUIDE.md](docs/guides/PLUGIN_GUIDE.md) for complete guide.

**Quick example:**

```yaml
# .claude-claude-code/plugins/my-project/config.yml
ai_sdlc:
  methodology_plugin: "file://claude-code/plugins/aisdlc-methodology/config/stages_config.yml"

  enabled_stages:
    - requirements
    - design
    - tasks
    - code
    - system_test
    - uat
    - runtime_feedback

  stages:
    code:
      testing:
        coverage_minimum: 90
      key_principles:
        enabled: true
```

### Federated Architecture

```
Corporate Marketplace
  ├─ aisdlc-methodology (v2.0.0)
  └─ python-standards (v1.0.0)
       ↓
Division Marketplace
  ├─ backend-standards
  └─ payment-services-standards
       ↓
Project Plugin
  └─ payment-gateway-context
```

Plugin loading order determines priority - later plugins override earlier ones.

---

## Related Projects

This project evolved from and replaces:
- **ai_init** (https://github.com/foolishimp/ai_init) - Original Key Principles methodology (now integrated as Code stage)

---

## Questions?

- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
- **Plugin Guide**: See [docs/guides/PLUGIN_GUIDE.md](docs/guides/PLUGIN_GUIDE.md)
- **Complete Methodology**: See [docs/requirements/AI_SDLC_REQUIREMENTS.md](docs/requirements/AI_SDLC_REQUIREMENTS.md)
- **Examples**: See [ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples)
- **Documentation Index**: See [docs/README.md](docs/README.md)
- **Ask Claude Code**: I'm here to help!

---
