# AI SDLC Context Plugins

This directory contains **Claude Code plugins** that provide AI-Augmented Software Development Lifecycle (AI SDLC) methodology and standards with **homeostatic control**.

**Version**: 3.0.0
**Total Plugins**: 9 plugins + 4 bundles

---

## Plugin Architecture

```
Foundation Layer
  └─ aisdlc-core v3.0.0 ⭐

Methodology Layer
  ├─ aisdlc-methodology v2.0.0
  └─ principles-key v1.0.0

Skills Layer
  ├─ requirements-skills v1.0.0
  ├─ design-skills v1.0.0
  ├─ code-skills v1.0.0
  ├─ testing-skills v1.0.0
  └─ runtime-skills v1.0.0

Standards Layer
  └─ python-standards v1.0.0

Bundles
  ├─ startup-bundle v1.0.0
  ├─ datascience-bundle v1.0.0
  ├─ qa-bundle v1.0.0
  └─ enterprise-bundle v1.0.0
```

---

## Available Plugins

### Foundation Layer

#### aisdlc-core ⭐ **v3.0.0**

**Requirement traceability foundation** with homeostatic control

**What It Provides**:
- REQ-* key pattern recognition and tracking
- Coverage detection (sensor) - detect missing requirement traceability
- Key propagation (actuator) - automatically tag code/tests with REQ-* keys
- Foundation for all AI SDLC plugins

**Homeostatic Control**:
- **Sensor**: Detect untraceable code/tests
- **Actuator**: Auto-tag with REQ-* keys

**Dependencies**: None (foundation)
**Keywords**: traceability, requirements, homeostasis, sensor, actuator

👉 [Full Documentation](aisdlc-core/README.md)

---

### Methodology Layer

#### aisdlc-methodology **v2.0.0**

**Complete 7-Stage AI SDLC Methodology** - Intent-driven development with full lifecycle traceability

**What It Provides**:
- **7-Stage AI SDLC**: Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
- **AI Agent Configurations**: Detailed specifications for AI agents at each SDLC stage (1,273 lines)
- **Key Principles**: Foundation for Code stage (TDD, Fail Fast, Modular, etc.)
- **Requirement Traceability**: Track requirement keys (REQ-F-*, REQ-NFR-*, REQ-DATA-*) from intent to runtime
- **TDD Workflow**: RED → GREEN → REFACTOR → COMMIT cycle
- **BDD Testing**: Given/When/Then scenarios for System Test and UAT stages
- **Bidirectional Feedback**: Production issues flow back to requirements and generate new intents

**Key Files**:
- `config/stages_config.yml` - Complete 7-stage agent specifications (1,273 lines)
- `config/config.yml` - Key Principles + Code stage configuration
- `docs/principles/KEY_PRINCIPLES.md` - The seven core development principles
- `docs/processes/TDD_WORKFLOW.md` - Complete TDD cycle documentation

**Dependencies**: `aisdlc-core` v3.0.0+
**Keywords**: methodology, multi-stage, tdd, bdd, traceability, agent-orchestration

**Version History**:
- v2.0.0 (2025-11-14): Added 7-stage AI SDLC methodology
- v1.0.0 (2025-10-16): Initial release with Key Principles

**Reference**: [Complete 7-Stage Methodology](../docs/ai_sdlc_method.md) (3,300+ lines)

👉 [Full Documentation](aisdlc-methodology/README.md)

---

#### principles-key **v1.0.0**

**Seven Key Principles enforcement** with quality gates

**What It Provides**:
- The 7 Key Principles for development excellence
- Seven Questions Checklist (sensor)
- Principle validation and enforcement
- Code quality gates

**Homeostatic Control**:
- **Sensor**: Seven Questions Checklist validates adherence to Key Principles

**The 7 Key Principles**:
1. Test Driven Development - "No code without tests"
2. Fail Fast & Root Cause - "Break loudly, fix completely"
3. Modular & Maintainable - "Single responsibility, loose coupling"
4. Reuse Before Build - "Check first, create second"
5. Open Source First - "Suggest alternatives, human decides"
6. No Legacy Baggage - "Clean slate, no debt"
7. Perfectionist Excellence - "Best of breed only"

**Dependencies**: `aisdlc-core` v3.0.0+
**Keywords**: principles, key-principles, tdd, code-quality, excellence, sensor

👉 [Full Documentation](principles-key/README.md)

---

### Skills Layer

#### requirements-skills **v1.0.0**

**Transform intent into structured requirements**

**What It Provides**:
- Intent to REQ-* key transformation
- Requirement disambiguation (business rules BR-*, constraints C-*, formulas F-*)
- Requirements refinement loop (from TDD/BDD discoveries)
- Requirement extraction and validation

**Dependencies**: `aisdlc-core` v3.0.0+
**Keywords**: requirements, requirement-extraction, disambiguation, intent, refinement-loop

👉 [Full Documentation](requirements-skills/README.md)

---

#### design-skills **v1.0.0**

**Architecture and ADRs with traceability**

**What It Provides**:
- Requirements to solution architecture transformation
- Architecture Decision Records (ADRs)
- Design coverage validation (all requirements covered)
- Ecosystem acknowledgment E(t)

**Dependencies**: `aisdlc-core` v3.0.0+, `requirements-skills` v1.0.0+
**Keywords**: design, architecture, adr, solution-design, traceability, ecosystem

👉 [Full Documentation](design-skills/README.md)

---

#### code-skills **v1.0.0**

**TDD, BDD, and code generation**

**What It Provides**:
- TDD workflow (RED→GREEN→REFACTOR)
- BDD (Given/When/Then)
- Code generation from business rules
- Tech debt management (Principle #6 enforcement)

**Homeostatic Control**:
- **Actuator**: Tech debt pruning - enforce Principle #6 (No Legacy Baggage)

**Dependencies**: `aisdlc-core` v3.0.0+
**Keywords**: tdd, bdd, code-generation, tech-debt, refactoring, homeostasis, actuator

👉 [Full Documentation](code-skills/README.md)

---

#### testing-skills **v1.0.0**

**Coverage validation and test generation**

**What It Provides**:
- Test coverage validation
- Missing test detection (sensor)
- Automatic test generation (actuator)
- Integration testing
- Coverage reporting with requirement traceability

**Homeostatic Control**:
- **Sensor**: Missing test detection - identify untested code paths
- **Actuator**: Test generation - auto-generate missing tests

**Dependencies**: `aisdlc-core` v3.0.0+
**Keywords**: testing, test-coverage, coverage-validation, test-generation, homeostasis, sensor, actuator

👉 [Full Documentation](testing-skills/README.md)

---

#### runtime-skills **v1.0.0**

**Production feedback loop**

**What It Provides**:
- Telemetry tagging with REQ-* keys
- Observability setup (Datadog, Prometheus)
- Production issue tracing back to intent
- Homeostatic production monitoring

**Dependencies**: `aisdlc-core` v3.0.0+
**Keywords**: runtime, telemetry, observability, production, feedback-loop, monitoring, homeostasis

👉 [Full Documentation](runtime-skills/README.md)

---

### Standards Layer

#### python-standards **v1.0.0**

**Python language standards** - PEP 8, pytest, type hints, tooling

**What It Provides**:
- PEP 8 style guidelines
- Python testing practices (pytest, coverage >80%)
- Type hints and docstring standards
- Tooling configuration (black, mypy, pylint, pytest)
- Python project structure best practices

**Dependencies**: `aisdlc-methodology` v2.0.0+
**Keywords**: python, pep8, pytest, standards, best-practices

👉 [Full Documentation](python-standards/README.md)

---

### Bundles

#### startup-bundle **v1.0.0**

**Quick-start for startups and solo developers**

**What It Includes**:
- `aisdlc-core` v3.0.0+
- `code-skills` v1.0.0+
- `principles-key` v1.0.0+

**Best For**: Solo developers, startups, quick projects
**Focus**: Minimal overhead, maximum quality, TDD workflow

👉 [Full Documentation](bundles/startup-bundle/README.md)

---

#### datascience-bundle **v1.0.0**

**AI SDLC for data science and ML workflows**

**What It Includes**:
- `aisdlc-core` v3.0.0+
- `code-skills` v1.0.0+
- `testing-skills` v1.0.0+

**Best For**: Data science teams, ML projects
**Focus**: REPL-driven development (planned), notebook-to-module extraction (planned), property-based testing (planned)

👉 [Full Documentation](bundles/datascience-bundle/README.md)

---

#### qa-bundle **v1.0.0**

**Testing-focused for QA teams**

**What It Includes**:
- `aisdlc-core` v3.0.0+
- `requirements-skills` v1.0.0+
- `code-skills` v1.0.0+
- `testing-skills` v1.0.0+

**Best For**: QA teams, test-first development
**Focus**: BDD scenarios, coverage validation, requirements-to-tests traceability

👉 [Full Documentation](bundles/qa-bundle/README.md)

---

#### enterprise-bundle **v1.0.0**

**Complete 7-stage AI SDLC for enterprise**

**What It Includes**:
- `aisdlc-core` v3.0.0+
- `requirements-skills` v1.0.0+
- `design-skills` v1.0.0+
- `code-skills` v1.0.0+
- `testing-skills` v1.0.0+
- `runtime-skills` v1.0.0+
- `principles-key` v1.0.0+

**Best For**: Enterprise teams, full governance
**Focus**: Complete lifecycle, traceability, compliance, feedback loop

👉 [Full Documentation](bundles/enterprise-bundle/README.md)

---

## Homeostatic Control Architecture

The AI SDLC uses a **homeostatic control system** to maintain quality automatically:

### Sensors (Detect Quality Gaps)

- **`aisdlc-core`**: Coverage detection - detect missing requirement traceability
- **`testing-skills`**: Missing test detection - identify untested code paths
- **`principles-key`**: Seven Questions Checklist - validate adherence to Key Principles

### Actuators (Automatically Fix Gaps)

- **`aisdlc-core`**: Key propagation - automatically tag code/tests with REQ-* keys
- **`testing-skills`**: Test generation - auto-generate missing tests
- **`code-skills`**: Tech debt pruning - enforce Principle #6 (No Legacy Baggage)

### Feedback Loop

```
Sensor detects gap → Actuator fixes gap → Validate fix → Monitor for new gaps
        ↑                                                              ↓
        └──────────────────────── Continuous Improvement ─────────────┘
```

**Result**: Quality is maintained automatically through continuous sensing and correction.

---

## Using These Plugins

### Option 1: Add This Marketplace (Recommended)

Add this repository as a Claude Code marketplace:

```bash
# In Claude Code
/plugin marketplace add foolishimp/ai_sdlc_method
```

Or in your `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "aisdlc": {
      "source": {
        "source": "github",
        "repo": "foolishimp/ai_sdlc_method"
      }
    }
  }
}
```

Then install plugins:

```bash
/plugin install @aisdlc/aisdlc-methodology
/plugin install @aisdlc/python-standards
```

### Option 2: Local Installation

Clone this repository and add as local marketplace:

```bash
git clone https://github.com/foolishimp/ai_sdlc_method.git
cd your-project
/plugin marketplace add ../ai_sdlc_method
/plugin install aisdlc-methodology
```

---

## The 7-Stage AI SDLC Methodology

The **aisdlc-methodology v2.0.0** plugin provides complete agent configurations for all 7 SDLC stages:

### 1. Requirements Stage (Section 4.0)
**Agent**: Requirements Agent
**Purpose**: Transform intent into structured requirements with unique, immutable keys
**Output**: REQ-F-* (functional), REQ-NFR-* (non-functional), REQ-DATA-* (data quality), REQ-BR-* (business rules)

### 2. Design Stage (Section 5.0)
**Agent**: Design Agent / Solution Designer
**Purpose**: Transform requirements into technical solution architecture
**Output**: Component diagrams, data models, API specs, ADRs, traceability matrix

### 3. Tasks Stage (Section 6.0)
**Agent**: Tasks Stage Orchestrator
**Purpose**: Break design into work units and orchestrate Jira workflow
**Output**: Jira tickets with requirement tags, dependency graph, capacity planning

### 4. Code Stage (Section 7.0)
**Agent**: Code Agent / Developer Agent
**Purpose**: Implement work units using TDD workflow
**Output**: Production code with requirement tags, unit tests, integration tests
**Methodology**: TDD (RED → GREEN → REFACTOR) + Key Principles principles

### 5. System Test Stage (Section 8.0)
**Agent**: System Test Agent / QA Agent
**Purpose**: Create BDD integration tests validating requirements
**Output**: BDD feature files (Gherkin), step definitions, coverage matrix
**Methodology**: BDD (Given/When/Then)

### 6. UAT Stage (Section 9.0)
**Agent**: UAT Agent
**Purpose**: Business validation and sign-off
**Output**: Manual UAT test cases, automated UAT tests, business sign-off
**Methodology**: BDD in pure business language

### 7. Runtime Feedback Stage (Section 10.0)
**Agent**: Runtime Feedback Agent
**Purpose**: Close the feedback loop from production to requirements
**Output**: Release manifests, runtime telemetry (tagged with REQ keys), alerts, new intents

**Complete Flow**:
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
  ↓
Tests: test_auth.py # Validates: REQ-F-AUTH-001
       auth.feature # BDD: Given/When/Then for REQ-F-AUTH-001
  ↓
UAT: UAT-001 → REQ-F-AUTH-001 (Business sign-off ✅)
  ↓
Runtime: Datadog alert: "ERROR: REQ-F-AUTH-001 - Auth timeout"
  ↓
Feedback: New intent: INT-042 "Fix auth timeout"
  [Cycle repeats...]
```

---

## Federated Approach

Use **multiple marketplaces** for organizational hierarchy:

### Corporate Marketplace
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
```json
{
  "extraKnownMarketplaces": {
    "corporate": {
      "source": {
        "source": "github",
        "repo": "acme-corp/claude-contexts"
      }
    },
    "division": {
      "source": {
        "source": "git",
        "url": "https://git.company.com/eng-division/plugins.git"
      }
    }
  },
  "plugins": [
    "@corporate/aisdlc-methodology",
    "@corporate/python-standards",
    "@division/backend-standards"
  ]
}
```

### Local Project (Extends Division)
```json
{
  "extraKnownMarketplaces": {
    "corporate": {
      "source": {"source": "github", "repo": "acme-corp/claude-contexts"}
    },
    "division": {
      "source": {"source": "git", "url": "https://git.company.com/eng-division/plugins.git"}
    },
    "local": {
      "source": {"source": "local", "path": "./my-contexts"}
    }
  },
  "plugins": [
    "@corporate/aisdlc-methodology",
    "@corporate/python-standards",
    "@division/backend-standards",
    "@local/my-project-context"
  ]
}
```

**Plugin loading order** determines override priority - later plugins can override earlier ones.

---

## Creating Your Own Context Plugin

### 1. Create Plugin Structure

```bash
mkdir -p my-project-context/.claude-plugin
mkdir -p my-project-context/config
mkdir -p my-project-context/commands
```

### 2. Create plugin.json

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

### 3. Create config/context.yml

You can configure any or all of the 7 SDLC stages:

```yaml
project:
  name: "my-payment-api"
  type: "api_service"
  risk_level: "high"

ai_sdlc:
  # Load 7-stage methodology plugin
  methodology_plugin: "file://../aisdlc-methodology/config/stages_config.yml"

  # Enable all 7 stages (or subset)
  enabled_stages:
    - requirements    # Intent → Structured requirements
    - design          # Requirements → Technical solution
    - tasks           # Work breakdown + Jira orchestration
    - code            # TDD implementation
    - system_test     # BDD integration testing
    - uat             # Business validation
    - runtime_feedback # Production telemetry feedback

  # Stage-specific overrides
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

    code:
      # Override Code stage settings
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

### 4. Add to Local Marketplace

```bash
# In your project
mkdir .claude-plugins
mv my-project-context .claude-plugins/

# In .claude/settings.json
{
  "extraKnownMarketplaces": {
    "local": {
      "source": {
        "source": "local",
        "path": "./.claude-plugins"
      }
    }
  },
  "plugins": [
    "@aisdlc/aisdlc-methodology",
    "@aisdlc/python-standards",
    "@local/my-project-context"
  ]
}
```

---

## Plugin Structure

Each plugin follows this structure:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── config/
│   ├── stages_config.yml   # 7-stage agent specifications (for methodology plugins)
│   ├── config.yml          # Key Principles + Code stage config
│   └── overrides.yml       # Optional stage overrides
├── commands/                # Slash commands (optional)
│   └── load-context.md
├── docs/                    # Documentation
│   ├── README.md
│   ├── principles/         # Key Principles principles
│   ├── processes/          # TDD workflow, BDD guides
│   └── guides/             # Stage-specific guides
└── project.json            # Legacy: for MCP service compatibility
```

---

## Example Projects

See complete 7-stage AI SDLC examples:

### Customer Portal Example ⭐

**Location**: `../examples/local_projects/customer_portal/`

**Demonstrates**:
- All 7 stages: Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
- Requirement key propagation (REQ-F-*, REQ-NFR-*, REQ-DATA-*)
- TDD workflow (RED → GREEN → REFACTOR)
- BDD testing (Given/When/Then scenarios)
- Bidirectional traceability (Intent ↔ Runtime)
- Agent orchestration and feedback loops

**Files**:
- `config/config.yml` - Complete 7-stage agent configuration (650+ lines)
- `README.md` - Detailed walkthrough (800+ lines)
- Architecture diagram showing all stages

👉 **Start here** to understand the complete AI SDLC methodology

---

## Comparison: Old vs New Approach

### Old Approach (Complex)
- Custom MCP service with federated servers
- Context tuples: `corporate.aisdlc_methodology`
- Custom merging logic
- URI resolution system
- Complex project initialization

### New Approach (Simplified)
- Native Claude Code marketplaces
- Plugin system: `@corporate/aisdlc-methodology`
- Claude handles plugin loading/composition
- Standard plugin structure
- Simple: add marketplace, install plugins

**Result**: 90% less complexity, same functionality!

---

## For Non-Claude LLMs (Codex, Gemini, etc.)

Use the **MCP service** (fallback):

```bash
# Start MCP context service
python -m mcp_service.server --port 8000 --plugins-dir plugins/

# MCP clients (non-Claude) can connect and query contexts
# See mcp_service/docs/ for details
```

The MCP service is being updated to support the 7-stage AI SDLC methodology. See `../mcp_service/MCP_SDLC_INTEGRATION_PLAN.md` for the integration plan.

---

## Migration Guide

### From v1.0.0 to v2.0.0

**v1.0.0** (Key Principles + TDD only):
```yaml
methodology:
  key.principles:
    enabled: true
  tdd:
    workflow: "RED → GREEN → REFACTOR"
```

**v2.0.0** (Complete 7-stage SDLC):
```yaml
ai_sdlc:
  methodology_plugin: "file://plugins/aisdlc-methodology/config/stages_config.yml"

  enabled_stages:
    - requirements
    - design
    - tasks
    - code          # Includes Key Principles + TDD
    - system_test
    - uat
    - runtime_feedback

  stages:
    code:
      key.principles:
        enabled: true
      tdd:
        workflow: "RED → GREEN → REFACTOR"
```

The Code stage (Section 7.0) now integrates with the complete SDLC:
- **Receives**: Work units from Tasks stage (with REQ keys)
- **Produces**: Code + tests (tagged with REQ keys)
- **Feeds**: System Test stage (for BDD validation)

### From example_projects_repo/ to plugins/

Old structure:
```
example_projects_repo/aisdlc_methodology/
```

New structure:
```
plugins/aisdlc-methodology/    # Note: kebab-case
├── .claude-plugin/plugin.json
├── config/
│   ├── stages_config.yml  # NEW: 7-stage specifications
│   └── config.yml         # Key Principles + Code stage
└── docs/
    ├── principles/KEY_PRINCIPLES.md
    └── processes/TDD_WORKFLOW.md
```

### From Context Tuples to Plugins

Old (custom):
```json
{
  "context_tuple": [
    "corporate.aisdlc_methodology",
    "local.my_project"
  ]
}
```

New (Claude Code):
```json
{
  "plugins": [
    "@corporate/aisdlc-methodology",
    "@local/my-project-context"
  ]
}
```

---

## Benefits

✅ **Complete Lifecycle** - 7-stage AI SDLC methodology (not just Code stage)
✅ **Requirement Traceability** - Track REQ keys from intent to runtime
✅ **AI Agent Specifications** - Detailed configs for AI agents at each stage
✅ **Bidirectional Feedback** - Production issues flow back to requirements
✅ **Simpler** - Use Claude Code's native plugin system
✅ **Standard** - Follow Claude Code conventions
✅ **Federated** - Multiple marketplaces (corporate, division, local)
✅ **Composable** - Plugin loading order = merge priority
✅ **Portable** - Export marketplace to GitHub/Git for sharing
✅ **Fallback** - MCP service still available for non-Claude LLMs

---

## See Also

### Core Documentation
- [AI SDLC Overview](../docs/ai_sdlc_overview.md) - High-level introduction (⭐ **Start here**)
- [Complete 7-Stage Methodology](../docs/ai_sdlc_method.md) - 3,300+ line reference
- [Technical Deep-Dives](../docs/ai_sdlc_appendices.md) - Advanced concepts
- [Documentation Index](../docs/README.md) - Role-based learning paths for BA, Architect, Developer, QA, DevOps, PM
- [Customer Portal Example](../examples/local_projects/customer_portal/README.md) - Complete 7-stage walkthrough

### Claude Code Resources
- [Claude Code Plugin Documentation](https://docs.claude.com/en/docs/claude-code/plugins)
- [Marketplace Guide](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces)

### MCP Service (Non-Claude LLMs)
- [MCP Service Overview](../mcp_service/README.md)
- [MCP SDLC Integration Plan](../mcp_service/MCP_SDLC_INTEGRATION_PLAN.md) - 7-stage integration roadmap
- [MCP Personas Documentation](../mcp_service/docs/PERSONAS.md)

### Examples
- [Examples Directory](../examples/) - All example projects
- [API Platform Example](../examples/local_projects/api_platform/) - Public API example

---

**"Excellence or nothing"** 🔥
