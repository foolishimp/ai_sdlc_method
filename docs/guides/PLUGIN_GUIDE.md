# ai_sdlc_method Claude Code Plugin Guide

**Complete guide to using the 7-Stage AI SDLC Methodology as a Claude Code plugin**

## Overview

ai_sdlc_method provides the **complete 7-Stage AI SDLC methodology** as installable Claude Code plugins, enabling intent-driven development with full lifecycle traceability.

### What You Get

✅ **7-Stage AI SDLC Methodology** - Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
✅ **AI Agent Configurations** - Detailed specifications for AI agents at each SDLC stage (1,273 lines)
✅ **Requirement Traceability** - Track REQ keys from intent to runtime
✅ **Key Principles Principles** - Foundation for Code stage (TDD, Fail Fast, Modular, etc.)
✅ **TDD Workflow** - RED → GREEN → REFACTOR → COMMIT cycle
✅ **BDD Testing** - Given/When/Then scenarios for System Test and UAT stages
✅ **Bidirectional Feedback** - Production issues flow back to requirements

---

## Installation

### Current Installation Method

The AI SDLC methodology is embedded in this project repository. When you use Claude Code in a project with the ai_sdlc_method plugin:

```bash
# The plugin is located at:
# /path/to/project/.claude-plugin/plugins/aisdlc-methodology/

# To install in your own project using Python installers:
cd /path/to/your-project
python /path/to/ai_sdlc_method/claude-code/installers/aisdlc-setup.py
```

### Verify Installation

Check that the plugin is available:

```bash
# Check plugin structure
ls .claude-plugin/plugins/aisdlc-methodology/

# Should show:
# - agents/        (7 stage agents)
# - commands/      (8 slash commands)
# - skills/        (42 skills in 7 categories)
# - config/        (stages_config.yml, config.yml)
# - templates/     (workspace scaffolding)
```

### Alternative: Marketplace Installation (Future)

Once published to GitHub marketplace:

```bash
# Add marketplace (future)
/plugin marketplace add foolishimp/ai_sdlc_method

# Install methodology plugin (future)
/plugin install @foolishimp/aisdlc-methodology
```

---

## Quick Start

### Basic Usage

Once installed, Claude has access to the complete 7-stage methodology:

```
You: "Help me implement authentication using the AI SDLC methodology"

Claude will guide you through:
1. Requirements Stage - Generate REQ-F-AUTH-001, REQ-NFR-PERF-001, etc.
2. Design Stage - Create AuthenticationService, API specs, data models
3. Tasks Stage - Break into Jira tickets (PORTAL-123) with REQ tags
4. Code Stage - TDD implementation (RED → GREEN → REFACTOR)
5. System Test Stage - BDD scenarios (Given/When/Then)
6. UAT Stage - Business validation test cases
7. Runtime Feedback Stage - Telemetry with REQ key tagging
```

### Selective Stage Usage

You can enable only the stages you need:

**Enable all 7 stages:**
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
```

**Enable Code stage only (TDD focus):**
```yaml
ai_sdlc:
  enabled_stages:
    - code

  stages:
    code:
      key.principles:
        enabled: true
      tdd:
        workflow: "RED → GREEN → REFACTOR"
      testing:
        coverage_minimum: 80
```

---

## Plugin Architecture

### aisdlc-methodology Plugin Structure

```
.claude-plugin/plugins/aisdlc-methodology/
├── .claude-plugin/
│   └── plugin.json                 # Plugin metadata (v4.4.0)
├── agents/                         # 7 stage-specific personas
│   ├── aisdlc-requirements-agent.md
│   ├── aisdlc-design-agent.md
│   ├── aisdlc-tasks-agent.md
│   ├── aisdlc-code-agent.md
│   ├── aisdlc-system-test-agent.md
│   ├── aisdlc-uat-agent.md
│   └── aisdlc-runtime-feedback-agent.md
├── commands/                       # 8 slash commands
│   ├── aisdlc-checkpoint-tasks.md
│   ├── aisdlc-commit-task.md
│   ├── aisdlc-finish-task.md
│   ├── aisdlc-help.md
│   ├── aisdlc-refresh-context.md
│   ├── aisdlc-release.md
│   ├── aisdlc-status.md
│   └── aisdlc-update.md
├── skills/                         # 42 skills in 7 categories
│   ├── code/                       # Code generation skills
│   ├── core/                       # Core methodology skills
│   ├── design/                     # Design and architecture skills
│   ├── principles/                 # Key Principles skills
│   ├── requirements/               # Requirements management skills
│   ├── runtime/                    # Runtime monitoring skills
│   └── testing/                    # Testing and validation skills
├── config/
│   ├── stages_config.yml           # 7-stage specifications (790 lines)
│   └── config.yml                  # Key Principles configuration
├── templates/                      # Workspace scaffolding
│   └── .ai-workspace/
│       ├── tasks/
│       ├── templates/
│       └── config/
├── hooks/                          # 4 lifecycle hooks
│   └── hooks.json
├── docs/                           # Documentation
│   ├── README.md
│   ├── principles/
│   └── processes/
└── README.md                       # Plugin overview
```

### Key Configuration Files

#### 1. stages_config.yml (790 lines)

Complete 7-stage agent specifications:

```yaml
ai_sdlc_stages:
  version: "1.0"
  description: "Complete AI SDLC stage configurations with AI agent specifications"

  requirements_stage:
    agent:
      name: "AISDLC Requirements Agent"
      role: "Intent Store & Traceability Hub"
      purpose: "Transform intent into formally documented, uniquely-keyed requirements"
      responsibilities: [...]
      inputs: [...]
      outputs: [...]
      quality_gates: [...]

  design_stage:
    agent:
      name: "AISDLC Design Agent"
      role: "Solution Designer"
      # ... complete specification

  tasks_stage:
    agent:
      name: "AISDLC Tasks Stage Orchestrator"
      # ... complete specification

  code_stage:
    agent:
      name: "AISDLC Code Agent"
      # ... complete specification + Key Principles + TDD

  system_test_stage:
    agent:
      name: "AISDLC System Test Agent"
      # ... complete specification + BDD

  uat_stage:
    agent:
      name: "AISDLC UAT Agent"
      # ... complete specification

  runtime_feedback_stage:
    agent:
      name: "AISDLC Runtime Feedback Agent"
      # ... complete specification
```

#### 2. config.yml

Key Principles principles and Code stage configuration:

```yaml
methodology:
  key.principles:
    principles:
      - name: "Test Driven Development"
        mandate: "No code without tests"
      - name: "Fail Fast & Root Cause"
        mandate: "Break loudly, fix completely"
      # ... all 7 principles

  tdd:
    workflow: "RED → GREEN → REFACTOR"
    steps:
      - name: "RED"
        description: "Write failing test first"
      - name: "GREEN"
        description: "Write minimal code to pass"
      - name: "REFACTOR"
        description: "Improve code quality"
```

---

## Creating Your Own Project Plugin

### Step 1: Create Plugin Structure

```bash
mkdir -p .claude-plugin/plugins/my-project-context/.claude-plugin
mkdir -p .claude-plugin/plugins/my-project-context/config
```

### Step 2: Create plugin.json

```json
{
  "name": "my-project-context",
  "version": "1.0.0",
  "displayName": "My Project Context",
  "description": "Project-specific configuration and standards",
  "dependencies": {
    "aisdlc-methodology": "^2.0.0",
    "python-standards": "^1.0.0"
  }
}
```

### Step 3: Create config.yml

Configure stages for your project:

```yaml
project:
  name: "my-payment-api"
  type: "api_service"
  risk_level: "high"

ai_sdlc:
  # Reference to methodology plugin (loaded automatically)
  # Plugin location: .claude-plugin/plugins/aisdlc-methodology/

  # Enable stages you need
  enabled_stages:
    - requirements
    - design
    - tasks
    - code
    - system_test
    - uat
    - runtime_feedback

  # Override stage configurations
  stages:
    requirements:
      personas:
        product_owner: john@acme.com
        business_analyst: sarah@acme.com

      requirement_types:
        - type: functional
          prefix: REQ-F
          template: "file://docs/templates/user_story_template.md"
        - type: non_functional
          prefix: REQ-NFR
          template: "file://docs/templates/nfr_template.md"
        - type: data_quality
          prefix: REQ-DATA
          template: "file://docs/templates/data_quality_template.md"

    code:
      testing:
        coverage_minimum: 95  # Higher than baseline 80%
        frameworks: [pytest, unittest]

      key.principles:
        enabled: true
        tdd_workflow: strict  # Enforce RED → GREEN → REFACTOR

    system_test:
      bdd_framework: behave  # or cucumber, pytest-bdd
      coverage_requirement: 95  # ≥95% requirement coverage

    runtime_feedback:
      telemetry_platform: datadog
      alert_channels:
        - slack: "#alerts-payment-api"
        - pagerduty: "payment-service-oncall"

# Project-specific overrides
security:
  penetration_testing: required
  pci_compliance: true
```

### Step 4: Use Your Plugin

Your project plugin extends the base aisdlc-methodology plugin. Place it in:

```bash
.claude-plugin/plugins/my-project-context/

# Claude Code will automatically discover plugins in .claude-plugin/plugins/
```

The plugin loading order:
1. Base plugins (aisdlc-methodology)
2. Project-specific plugins (your overrides)

Later plugins can override earlier ones.

---

## Federated Plugin Architecture

Use multiple marketplaces for organizational hierarchy:

### Corporate Marketplace

**Repository**: `acme-corp/claude-contexts`

```json
{
  "extraKnownMarketplaces": {
    "corporate": {
      "source": {
        "source": "github",
        "repo": "acme-corp/claude-contexts"
      }
    }
  },
  "plugins": [
    "@corporate/aisdlc-methodology",
    "@corporate/python-standards"
  ]
}
```

### Division Marketplace (Extends Corporate)

**Repository**: `git.company.com/eng-division/plugins.git`

```json
{
  "plugins": [
    "@corporate/aisdlc-methodology",
    "@corporate/python-standards",
    "@division/backend-standards",
    "@division/payment-services-standards"
  ]
}
```

### Project Plugin (Extends Division)

**Local**: `./.claude-plugin/plugins/`

```bash
# Project-specific plugin
.claude-plugin/plugins/payment-gateway-context/

# Inherits from:
# - Corporate standards (aisdlc-methodology, python-standards)
# - Division standards (backend-standards)
```

**Plugin loading order determines priority** - later plugins override earlier ones.

Note: Currently plugins are installed via Python installers. Future versions will support marketplace-based installation.

---

## Example Workflows

### Workflow 1: Full 7-Stage Development

```
You: "Implement user registration feature using AI SDLC methodology"

Claude (Requirements Agent):
- REQ-F-REG-001: User can register with email/password
- REQ-F-REG-002: User receives confirmation email
- REQ-NFR-PERF-001: Registration completes in < 2 seconds
- REQ-DATA-001: Email must be valid format

Claude (Design Agent):
- Component: RegistrationService
- API: POST /api/v1/auth/register
- Data Model: User table with email, password_hash, confirmed_at
- Dependencies: EmailService, ValidationService

Claude (Tasks Agent):
- PORTAL-101: Implement RegistrationService (REQ-F-REG-001)
- PORTAL-102: Integrate EmailService (REQ-F-REG-002)
- PORTAL-103: Add validation (REQ-DATA-001)

Claude (Code Agent - TDD):
- RED: test_user_registration_creates_user() → FAIL
- GREEN: Implement register() method → PASS
- REFACTOR: Clean up code, add # Implements: REQ-F-REG-001
- COMMIT: "Add user registration (REQ-F-REG-001)"

Claude (System Test Agent - BDD):
Feature: User Registration
  Scenario: Successful registration
    Given I am on the registration page
    When I enter valid email "user@example.com"
    And I enter valid password "SecurePass123!"
    And I click "Register"
    Then I should see "Registration successful"
    And I should receive confirmation email
    # Validates: REQ-F-REG-001, REQ-F-REG-002

Claude (UAT Agent):
- UAT-001: Business analyst confirms registration flow works
- UAT-002: Product owner signs off on email content
- Status: REQ-F-REG-001 ✅ APPROVED

Claude (Runtime Feedback Agent):
- Release manifest: v1.2.0 includes REQ-F-REG-001, REQ-F-REG-002
- Telemetry: Track "registration_success" tagged with REQ-F-REG-001
- Alert: If registration_failures > 5%, create new intent
```

### Workflow 2: Code Stage Only

```yaml
# Enable only Code stage
ai_sdlc:
  enabled_stages:
    - code

  stages:
    code:
      key.principles:
        enabled: true
```

```
You: "Implement the login method"

Claude (Code Agent):
Following TDD workflow (RED → GREEN → REFACTOR):

1. RED - Write failing test:
def test_user_login_with_valid_credentials():
    user = create_test_user()
    result = login(user.email, "password123")
    assert result.success == True

2. GREEN - Implement minimal solution:
def login(email, password):
    user = User.get_by_email(email)
    if user and user.check_password(password):
        return LoginResult(success=True, user=user)
    return LoginResult(success=False)

3. REFACTOR - Improve code quality:
# Implements: REQ-F-AUTH-002
def login(email: str, password: str) -> LoginResult:
    """Authenticate user with email and password."""
    user = User.get_by_email(email)

    if not user:
        logger.warning(f"Login attempt for non-existent user: {email}")
        return LoginResult(success=False, error="Invalid credentials")

    if not user.check_password(password):
        logger.warning(f"Failed login attempt for user: {email}")
        return LoginResult(success=False, error="Invalid credentials")

    logger.info(f"Successful login for user: {email}")
    return LoginResult(success=True, user=user)
```

### Workflow 3: Runtime Issue → Requirements

```
Production Alert:
  "ERROR: REQ-F-AUTH-001 - Authentication timeout (>5s)"
  Datadog: auth_service.login() p99 latency = 7.2s

You: "Analyze this authentication timeout issue"

Claude (Runtime Feedback Agent):
1. Traces REQ-F-AUTH-001 back through stages:
   - Runtime: p99 = 7.2s (violates REQ-NFR-PERF-001: < 500ms)
   - Code: auth_service.py implemented REQ-F-AUTH-001
   - Design: AuthenticationService depends on UserDB
   - Requirements: REQ-NFR-PERF-001 specifies < 500ms

2. Root cause analysis:
   - Performance requirement violated
   - UserDB query is bottleneck

3. Generates new intent:
   - INT-042: "Optimize authentication performance"
   - Links to: REQ-F-AUTH-001, REQ-NFR-PERF-001
   - Priority: HIGH (production impact)

New cycle begins at Requirements stage to address INT-042
```

---

## Benefits

### For Teams

✅ **Consistent Methodology** - Everyone follows the same 7-stage process
✅ **Complete Traceability** - Track requirements from intent to runtime
✅ **Quality Enforcement** - TDD, BDD, coverage requirements built-in
✅ **Federated Standards** - Corporate → Division → Team → Project layers
✅ **Easy Sharing** - Install with `/plugin install` command

### For Developers

✅ **Clear Guidance** - AI agents specify exactly what to do at each stage
✅ **TDD Workflow** - RED → GREEN → REFACTOR cycle enforced
✅ **Key Principles Principles** - Foundation for excellent code
✅ **Automated Tagging** - Requirement keys automatically tracked
✅ **Bidirectional Feedback** - Production issues link back to requirements

### For Organizations

✅ **Audit Trail** - Git-backed plugin history
✅ **Compliance** - Standards enforced at plugin level
✅ **Scalability** - Federated architecture supports large organizations
✅ **Versioning** - Plugin versions track methodology evolution

---

## Documentation

### Core Methodology
- [../requirements/AI_SDLC_OVERVIEW.md](../requirements/AI_SDLC_OVERVIEW.md) - High-level overview
- [../requirements/AI_SDLC_REQUIREMENTS.md](../requirements/AI_SDLC_REQUIREMENTS.md) - Complete methodology specification
- [../requirements/AI_SDLC_CONCEPTS.md](../requirements/AI_SDLC_CONCEPTS.md) - Key concepts and theory
- [../requirements/AI_SDLC_APPENDICES.md](../requirements/AI_SDLC_APPENDICES.md) - Category theory deep-dives
- [../README.md](../README.md) - Documentation index

### Plugin Documentation
- [../../claude-code/.claude-plugin/plugins/aisdlc-methodology/README.md](../../claude-code/.claude-plugin/plugins/aisdlc-methodology/README.md) - Plugin overview
- [../../claude-code/.claude-plugin/plugins/README.md](../../claude-code/.claude-plugin/plugins/README.md) - Plugin system (if exists)

### Implementation Design
- [../design/claude_aisdlc/](../design/claude_aisdlc/) - Claude Code implementation design
- [../design/claude_aisdlc/adrs/](../design/claude_aisdlc/adrs/) - Architecture decision records

### Quick Start
- [../../QUICKSTART.md](../../QUICKSTART.md) - Quick start guide
- [../../README.md](../../README.md) - Project overview

---

## Troubleshooting

### Plugin Not Loading

```bash
# Check plugin structure
ls .claude-plugin/plugins/aisdlc-methodology/

# Verify agents, commands, and skills are present
ls .claude-plugin/plugins/aisdlc-methodology/agents/
ls .claude-plugin/plugins/aisdlc-methodology/commands/
ls .claude-plugin/plugins/aisdlc-methodology/skills/

# Reinstall if needed using Python installer
python /path/to/ai_sdlc_method/claude-code/installers/aisdlc-setup.py
```

### Configuration Not Working

Check that the plugin structure is complete:
```bash
# Verify config files exist
cat .claude-plugin/plugins/aisdlc-methodology/config/stages_config.yml
cat .claude-plugin/plugins/aisdlc-methodology/config/config.yml

# Check plugin metadata
cat .claude-plugin/plugins/aisdlc-methodology/.claude-plugin/plugin.json
```

### Commands Not Available

```bash
# Verify commands are installed
ls .claude-plugin/plugins/aisdlc-methodology/commands/

# Should show 8 commands:
# - aisdlc-checkpoint-tasks.md
# - aisdlc-commit-task.md
# - aisdlc-finish-task.md
# - aisdlc-help.md
# - aisdlc-refresh-context.md
# - aisdlc-release.md
# - aisdlc-status.md
# - aisdlc-update.md
```

---

## Support

- **GitHub**: https://github.com/foolishimp/ai_sdlc_method
- **Issues**: https://github.com/foolishimp/ai_sdlc_method/issues
- **Documentation**: [docs/README.md](docs/README.md)

---

**"Excellence or nothing"** 🔥

**Install now:** `/plugin install @aisdlc/aisdlc-methodology` 🚀
