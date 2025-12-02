# ai_sdlc_method

**Intent-Driven AI SDLC Methodology** with homeostatic control, requirement traceability, and 7-stage agent orchestration.

**Mantra**: **"Excellence or nothing"** 🔥

**Version**: 0.5.0

Please credit the work done here if you find it useful!
Would love to hear your feedback, improvements, and contributions.

---

## What Is This?

A complete **AI-Augmented Software Development Lifecycle (AI SDLC)** framework providing:

- **🎯 7-Stage Methodology**: Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
- **🔗 Requirement Traceability**: Track requirement keys (REQ-F-*, REQ-NFR-*, REQ-DATA-*) from intent to runtime
- **🤖 AI Agent Configurations**: Detailed specifications for AI agents at each SDLC stage
- **⚖️ Homeostatic Control**: Sensors detect quality gaps, actuators automatically fix them
- **📦 Claude Code Plugins**: Installable methodology and standards as plugins (9 plugins + 4 bundles)
- **🏢 Federated Architecture**: Compose contexts across corporate → division → team → project
- **🔄 Bidirectional Feedback**: Production issues flow back to requirements and generate new intents

### The 7-Stage AI SDLC

```
Intent → Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
   ↑                                                                         ↓
   └─────────────────────────── Feedback Loop ───────────────────────────────┘
```

Each stage has:
- **AI Agent specification** with clear responsibilities
- **Quality gates** for stage completion
- **Traceability** to requirement keys
- **Personas** (human roles and AI agents)

👉 **Start Here**: [The AI SDLC Journey](docs/guides/JOURNEY.md) - Complete happy path from setup to UAT (3 hour guided tour) ⭐
👉 **Quick Introduction**: [AI SDLC Overview](docs/requirements/AI_SDLC_OVERVIEW.md) (~30 min read)
👉 **Complete Methodology**: [AI SDLC Requirements](docs/requirements/AI_SDLC_REQUIREMENTS.md) (Sections 1-13)
👉 **Example Projects**: [ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples) (separate repo)

---

## Quick Start (One Command)

**From your project directory:**

```bash
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -
```

**That's it!** Restart Claude Code and you're ready.

### Installation Options

```bash
# Basic setup (3 core plugins)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -

# Full setup with task workspace and lifecycle hooks
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --workspace --hooks

# All 9 plugins (enterprise)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --all

# Preview changes without writing
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --dry-run
```

**What you get**:
- Complete 7-stage AI SDLC workflow
- Key Principles development principles (TDD, Fail Fast, Modular, etc.)
- TDD workflow (RED → GREEN → REFACTOR)
- BDD testing guidelines
- Requirement traceability framework (REQ-F-*, REQ-NFR-*, REQ-DATA-*)
- Lifecycle hooks for methodology automation (with `--hooks`)
- Task management workspace (with `--workspace`)

### Verify Installation

After restarting Claude Code, run `/plugin` to see installed plugins.

### Option 2: Explore the Methodology First

```bash
# Clone the repository
git clone https://github.com/foolishimp/ai_sdlc_method.git
cd ai_sdlc_method

# Read the methodology overview
open docs/ai_sdlc_overview.md

# Or dive into the complete method
open docs/ai_sdlc_method.md

# Explore example projects (separate repo)
# git clone https://github.com/foolishimp/ai_sdlc_examples.git

# Review the methodology plugin
open claude-code/plugins/aisdlc-methodology/README.md
```

---

## The 7 Stages Explained

### 1. Requirements Stage (Section 4.0)
**Agent**: AISDLC Requirements Agent
**Purpose**: Transform intent into structured requirements with unique, immutable keys

**Outputs**: REQ-F-* (functional), REQ-NFR-* (non-functional), REQ-DATA-* (data quality), REQ-BR-* (business rules)

### 2. Design Stage (Section 5.0)
**Agent**: AISDLC Design Agent / Solution Designer
**Purpose**: Transform requirements into implementable technical and data solution

**Outputs**: Component diagrams, data models, API specifications, architecture decision records (ADRs)

### 3. Tasks Stage (Section 6.0)
**Agent**: AISDLC Tasks Stage Orchestrator
**Purpose**: Work breakdown with Jira integration and agent orchestration

**Outputs**: Jira epics/stories with requirement tags, dependency graph, capacity planning

### 4. Code Stage (Section 7.0)
**Agent**: AISDLC Code Agent / Developer Agent
**Purpose**: TDD-driven implementation (RED → GREEN → REFACTOR)

**Methodology**: Key Principles principles + TDD cycle
**Outputs**: Production code with requirement tags, unit tests, integration tests

### 5. System Test Stage (Section 8.0)
**Agent**: AISDLC System Test Agent / QA Agent
**Purpose**: BDD integration testing (Given/When/Then)

**Outputs**: BDD feature files (Gherkin), step definitions, coverage matrix (≥95% requirement coverage)

### 6. UAT Stage (Section 9.0)
**Agent**: AISDLC UAT Agent
**Purpose**: Business validation with BDD in pure business language

**Outputs**: Manual UAT test cases, automated UAT tests, business sign-off

### 7. Runtime Feedback Stage (Section 10.0)
**Agent**: AISDLC Runtime Feedback Agent
**Purpose**: Production telemetry and feedback loop closure

**Outputs**: Release manifests with requirement traceability, runtime alerts linked to requirement keys, new intents from production issues

👉 **Detailed Specifications**: [AI SDLC Method](docs/ai_sdlc_method.md)

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

**Every artifact tagged with requirement keys** for complete traceability!

---

## Key Principles Principles (Code Stage Foundation)

The Code Stage (Section 7.0) is built on these principles:

1. **Test Driven Development** - "No code without tests"
   - TDD cycle: RED → GREEN → REFACTOR → COMMIT
   - Minimum 80% coverage (critical paths 100%)

2. **Fail Fast & Root Cause** - "Break loudly, fix completely"
   - No workarounds or band-aids
   - Tests fail loudly, fix root causes

3. **Modular & Maintainable** - "Single responsibility, loose coupling"
   - Each module does one thing well
   - Clean, understandable code

4. **Reuse Before Build** - "Check first, create second"
   - Search existing code first
   - Avoid duplication

5. **Open Source First** - "Suggest alternatives, human decides"
   - AI suggests options
   - Humans make final decisions

6. **No Legacy Baggage** - "Clean slate, no debt"
   - No technical debt
   - Clean implementation

7. **Perfectionist Excellence** - "Best of breed only"
   - Quality over quantity
   - Excellence or nothing

👉 **Full Principles**: [Key Principles](claude-code/plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md)

---

## Available Plugins

### Foundation Layer

#### aisdlc-core v3.0.0 ⭐

**Requirement traceability foundation** with homeostatic control

**Provides**:
- REQ-* key pattern recognition and tracking
- Coverage detection (sensor)
- Key propagation (actuator)
- Foundation for all AI SDLC plugins

**Dependencies**: None (foundation)
**Keywords**: traceability, requirements, homeostasis, sensor, actuator

👉 [Full Documentation](claude-code/plugins/aisdlc-core/README.md)

---

### Methodology Layer

#### aisdlc-methodology v2.0.0

**Core AI SDLC methodology** - Complete 7-stage workflow

**Provides**:
- ✅ Complete 7-stage AI SDLC agent configurations (1,273 lines)
- ✅ Key Principles development principles
- ✅ TDD workflow (RED → GREEN → REFACTOR)
- ✅ BDD testing guidelines (Given/When/Then)
- ✅ Requirement traceability framework
- ✅ Quality gates for each stage
- ✅ Persona specifications (human roles + AI agents)

**Dependencies**: `aisdlc-core`
**Keywords**: methodology, multi-stage, tdd, bdd, traceability, agent-orchestration

👉 [Full Documentation](claude-code/plugins/aisdlc-methodology/README.md)

#### principles-key v1.0.0

**Seven Key Principles enforcement** with quality gates

**Provides**:
- The 7 Key Principles for development excellence
- Seven Questions Checklist (sensor)
- Principle validation and enforcement
- Code quality gates

**Dependencies**: `aisdlc-core`
**Keywords**: principles, key-principles, tdd, code-quality, excellence, sensor

👉 [Full Documentation](claude-code/plugins/principles-key/README.md)

---

### Skills Layer

#### requirements-skills v1.0.0

**Transform intent into structured requirements**

**Provides**:
- Intent to REQ-* key transformation
- Requirement disambiguation (business rules, constraints, formulas)
- Requirements refinement loop
- Requirement extraction and validation

**Dependencies**: `aisdlc-core`
**Keywords**: requirements, requirement-extraction, disambiguation, intent, refinement-loop

👉 [Full Documentation](claude-code/plugins/requirements-skills/README.md)

#### design-skills v1.0.0

**Architecture and ADRs with traceability**

**Provides**:
- Requirements to solution architecture transformation
- Architecture Decision Records (ADRs)
- Design coverage validation
- Ecosystem acknowledgment E(t)

**Dependencies**: `aisdlc-core`, `requirements-skills`
**Keywords**: design, architecture, adr, solution-design, traceability, ecosystem

👉 [Full Documentation](claude-code/plugins/design-skills/README.md)

#### code-skills v1.0.0

**TDD, BDD, and code generation**

**Provides**:
- TDD workflow (RED→GREEN→REFACTOR)
- BDD (Given/When/Then)
- Code generation from business rules
- Tech debt management (Principle #6 enforcement - actuator)

**Dependencies**: `aisdlc-core`
**Keywords**: tdd, bdd, code-generation, tech-debt, refactoring, homeostasis, actuator

👉 [Full Documentation](claude-code/plugins/code-skills/README.md)

#### testing-skills v1.0.0

**Coverage validation and test generation**

**Provides**:
- Test coverage validation
- Missing test detection (sensor)
- Automatic test generation (actuator)
- Integration testing
- Coverage reporting with requirement traceability

**Dependencies**: `aisdlc-core`
**Keywords**: testing, test-coverage, coverage-validation, test-generation, homeostasis, sensor, actuator

👉 [Full Documentation](claude-code/plugins/testing-skills/README.md)

#### runtime-skills v1.0.0

**Production feedback loop**

**Provides**:
- Telemetry tagging with REQ-* keys
- Observability setup (Datadog, Prometheus)
- Production issue tracing back to intent
- Homeostatic production monitoring

**Dependencies**: `aisdlc-core`
**Keywords**: runtime, telemetry, observability, production, feedback-loop, monitoring, homeostasis

👉 [Full Documentation](claude-code/plugins/runtime-skills/README.md)

---

### Standards Layer

#### python-standards v1.0.0

**Python language standards** - PEP 8, pytest, type hints, tooling

**Provides**:
- PEP 8 style guidelines
- Python testing practices (pytest, coverage >80%)
- Type hints and docstring standards
- Tooling configuration (black, mypy, pylint, pytest)
- Python project structure best practices

**Dependencies**: `aisdlc-methodology`
**Keywords**: python, pep8, pytest, standards, best-practices

👉 [Full Documentation](claude-code/plugins/python-standards/README.md)

---

### Bundles

#### startup-bundle v1.0.0

**Quick-start for startups and solo developers**

**Includes**: `aisdlc-core`, `code-skills`, `principles-key`
**Best For**: Solo developers, startups, quick projects
**Focus**: Minimal overhead, maximum quality, TDD workflow

👉 [Full Documentation](claude-code/plugins/bundles/startup-bundle/README.md)

#### datascience-bundle v1.0.0

**AI SDLC for data science and ML workflows**

**Includes**: `aisdlc-core`, `code-skills`, `testing-skills`
**Best For**: Data science teams, ML projects
**Focus**: REPL-driven development (planned), notebook-to-module extraction (planned)

👉 [Full Documentation](claude-code/plugins/bundles/datascience-bundle/README.md)

#### qa-bundle v1.0.0

**Testing-focused for QA teams**

**Includes**: `aisdlc-core`, `requirements-skills`, `code-skills`, `testing-skills`
**Best For**: QA teams, test-first development
**Focus**: BDD scenarios, coverage validation, requirements-to-tests traceability

👉 [Full Documentation](claude-code/plugins/bundles/qa-bundle/README.md)

#### enterprise-bundle v1.0.0

**Complete 7-stage AI SDLC for enterprise**

**Includes**: All plugins (aisdlc-core, requirements-skills, design-skills, code-skills, testing-skills, runtime-skills, principles-key)
**Best For**: Enterprise teams, full governance
**Focus**: Complete lifecycle, traceability, compliance, feedback loop

👉 [Full Documentation](claude-code/plugins/bundles/enterprise-bundle/README.md)

---

## Federated Architecture

The power of this approach is **multiple marketplaces** for organizational hierarchy:

```json
{
  "extraKnownMarketplaces": {
    "corporate": {
      "source": {"source": "github", "repo": "acme-corp/claude-contexts"}
    },
    "division": {
      "source": {"source": "git", "url": "https://git.company.com/eng/plugins.git"}
    },
    "local": {
      "source": {"source": "local", "path": "./my-contexts"}
    }
  },
  "plugins": [
    "@corporate/aisdlc-methodology",      // Corporate baseline (7 stages)
    "@corporate/python-standards",         // Corporate Python standards
    "@division/backend-standards",         // Division overrides
    "@local/my-team-customizations",       // Team customizations
    "@local/my-project-context"            // Project-specific
  ]
}
```

**Plugin loading order** = merge priority. Later plugins override earlier ones.

---

## Example Projects

Example projects demonstrating the 7-stage AI SDLC are maintained in a separate repository:

👉 **[ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples)** - Complete example projects

**Includes**:
- **customer_portal** - Complete 7-stage example with full requirement traceability
- **api_platform** - Public API with backwards compatibility requirements
- **payment_gateway** - High-risk financial project example
- **admin_dashboard** - Low-risk internal tool example

---

## Creating Your Own Project with AI SDLC

See [claude-code/plugins/README.md](claude-code/plugins/README.md) for complete guide.

### Quick Example

```bash
# Create project structure
mkdir -p my-project/.claude-plugin
cd my-project

# Create plugin.json
cat > .claude-plugin/plugin.json <<EOF
{
  "name": "my-project-context",
  "version": "1.0.0",
  "displayName": "My Project",
  "dependencies": {
    "aisdlc-methodology": "^2.0.0",
    "python-standards": "^1.0.0"
  }
}
EOF

# Create project config with 7-stage SDLC
mkdir config
cat > config/context.yml <<EOF
project:
  name: "my-payment-api"
  risk_level: "high"

# Reference 7-stage methodology plugin
ai_sdlc:
  methodology_plugin: "file://../../claude-code/plugins/aisdlc-methodology/config/stages_config.yml"

  # Enable stages you need
  enabled_stages:
    - requirements
    - design
    - tasks
    - code
    - system_test
    - uat
    - runtime_feedback

  # Project-specific quality standards
  stages:
    code:
      testing:
        coverage_minimum: 95  # Override baseline 80%

    system_test:
      requirement_coverage_minimum: 98  # Override baseline 95%

security:
  pci_compliance: required
EOF

# Add to local marketplace
/plugin marketplace add ./my-project
/plugin install my-project-context
```

---

## Use Cases

### Corporate Standard Contexts

Your company hosts a marketplace with baseline contexts:

```
corporate-marketplace/
├── aisdlc-methodology/        # 7-stage AI SDLC
├── python-standards/
├── javascript-standards/
├── security-baseline/
└── compliance-requirements/
```

All developers add this marketplace and get company standards + 7-stage methodology.

### Division Customizations

Engineering division extends corporate with specific practices:

```
division-marketplace/
├── backend-api-standards/      # Extends python-standards
├── frontend-standards/          # Extends javascript-standards
├── microservices-patterns/
└── division-sdlc-overrides/    # Stage-specific customizations
```

### Team/Project Contexts

Individual teams create local contexts:

```
.claude-claude-code/plugins/
├── team-conventions/
└── project-specific/
    └── config/
        └── context.yml         # Project-specific 7-stage config
```

### Result: Layered Composition

```
Corporate (baseline + 7-stage SDLC)
  └─> Division (extensions + stage customizations)
      └─> Team (customizations)
          └─> Project (specifics)
```

Each layer can override the previous, creating a flexible hierarchy.

---

## Project Structure

```
ai_sdlc_method/
├── docs/                            # Core documentation
│   ├── ai_sdlc_overview.md          # High-level overview (~30 min read)
│   ├── ai_sdlc_method.md            # ⭐ Complete 7-stage methodology (3,300+ lines)
│   ├── ai_sdlc_appendices.md        # Technical deep-dives
│   ├── guides/                      # Role-specific guides
│   └── README.md                    # Documentation index
│
├── claude-code/plugins/                         # Claude Code plugins and skills
│   ├── aisdlc-methodology/          # 7-stage AI SDLC v2.0.0
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json          # Plugin metadata (7 stages)
│   │   ├── config/
│   │   │   ├── stages_config.yml    # Complete 7-stage agent specs (1,273 lines)
│   │   │   └── config.yml           # Key Principles + TDD workflow
│   │   ├── docs/                    # Methodology documentation
│   │   └── README.md                # Plugin overview
│   │
│   ├── code-skills/                 # Code generation skills plugin
│   ├── python-standards/            # Python standards plugin
│   └── README.md                    # Plugin creation guide
│
├── installers/                      # Python installation scripts
│   └── README.md                    # Installation scripts documentation
│
├── .claude-plugin/                  # Root plugin metadata
│   └── plugin.json                  # Repository as plugin
│
├── marketplace.json                 # Claude Code marketplace registry
├── CLAUDE.md                        # Claude Code guidance
├── QUICKSTART.md                    # Quick start guide
└── README.md                        # This file
```

---

## Documentation

### Core Methodology
- **[AI SDLC Overview](docs/ai_sdlc_overview.md)** - High-level introduction (~30 min read)
- **[AI SDLC Method](docs/ai_sdlc_method.md)** ⭐ - Complete 7-stage methodology (3,300+ lines)
- **[AI SDLC Appendices](docs/ai_sdlc_appendices.md)** - Technical deep-dives
- **[Example Projects](https://github.com/foolishimp/ai_sdlc_examples)** - Full walkthrough examples (separate repo)
- **[Methodology Plugin](claude-code/plugins/aisdlc-methodology/README.md)** - Plugin overview

### Principles & Processes
- **[Key Principles Principles](claude-code/plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md)** - Core principles
- **[TDD Workflow](claude-code/plugins/aisdlc-methodology/docs/processes/TDD_WORKFLOW.md)** - Development process
- **[Pair Programming](claude-code/plugins/aisdlc-methodology/docs/guides/PAIR_PROGRAMMING_WITH_AI.md)** - Human-AI collaboration

### Guides
- **[New Project Setup](docs/guides/NEW_PROJECT_SETUP.md)** - Step-by-step setup guide
- **[Plugin Guide](docs/guides/PLUGIN_GUIDE.md)** - How to create and use plugins
- **[Plugins Overview](claude-code/plugins/README.md)** - Plugin architecture and catalog
- **[Example Projects](https://github.com/foolishimp/ai_sdlc_examples)** - Example projects (separate repo)

### Reference
- **[Component Inventory](docs/info/INVENTORY.md)** - All deployable components and versions
- **[Skills Inventory](docs/info/SKILLS_INVENTORY.md)** - Complete skills catalog (41 skills)
- **[Agents vs Skills](docs/info/AGENTS_VS_SKILLS.md)** - Architecture explanation
- **[Project Intent](docs/requirements/INTENT.md)** - Project vision and roadmap

---

## Benefits of This Approach

### Methodology Benefits
✅ **Complete Lifecycle Coverage** - 7 stages from Intent to Runtime Feedback
✅ **End-to-End Traceability** - Requirement keys flow through entire pipeline
✅ **AI Agent Ready** - Detailed specifications for each stage agent
✅ **Feedback-Driven** - Continuous improvement through closed loops
✅ **Concurrent Execution** - Support for parallel sub-vector SDLCs
✅ **Context-Driven** - Standards and templates guide all stages
✅ **Quality Gates** - Clear pass/fail criteria at each stage

### Technical Benefits
✅ **90% simpler** - Uses Claude Code's native plugin system
✅ **Standard** - Follows Claude Code conventions
✅ **Federated** - Multiple marketplaces (corporate, division, local)
✅ **Composable** - Plugin loading order = merge priority
✅ **Portable** - Share via GitHub/Git marketplaces
✅ **Extensible** - Create your own plugins easily

---

## Updating Your Installation

### Reset Installation (Recommended)

The reset installer cleanly updates to a specific version, removing stale files while preserving your work:

```bash
cd /path/to/your/project

# One-liner via curl (no clone needed)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 -

# Specific version
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --version v0.2.0

# Preview first
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --dry-run
```

**Preserves**: `.ai-workspace/tasks/active/`, `.ai-workspace/tasks/finished/` (your work)
**Replaces**: `.claude/commands/`, `.claude/agents/`, `.ai-workspace/templates/`, `.ai-workspace/config/` (framework code)

See [installers/README.md](installers/README.md) for complete documentation.

---

## Migration from Old Version

If you were using the previous `example_projects_repo/` structure:

**Old**:
```
example_projects_repo/aisdlc_methodology/  (v1.0 - Code stage only)
contexts.json
```

**New**:
```
claude-code/plugins/aisdlc-methodology/  (v2.0 - Complete 7-stage SDLC)
marketplace.json
```

See [MIGRATION.md](MIGRATION.md) for complete guide.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## License

MIT

---

## Acknowledgments

- **Inspired by** [ai_init](https://github.com/foolishimp/ai_init) - Original Key Principles methodology
- **Expanded with** Complete 7-stage AI SDLC framework
- **Built with** Claude Code and the Key Principles principles
- **Simplified** by leveraging Claude Code's native marketplace system

---

## Version History

### v3.0.0 (2025-11-24) - Homeostatic Control Architecture ⭐
- ✨ Added homeostatic control system (sensors + actuators)
- ✨ Promoted `aisdlc-core` to v3.0.0 as foundation plugin
- ✨ Added 5 skills plugins (requirements, design, code, testing, runtime)
- ✨ Added `principles-key` plugin (Seven Principles enforcement)
- ✨ Added 4 bundles (startup, datascience, qa, enterprise)
- ✨ Sensors: Coverage detection, missing test detection, Seven Questions Checklist
- ✨ Actuators: Key propagation, test generation, tech debt pruning
- ✨ Complete marketplace registry with 9 plugins + 4 bundles
- ✨ Enhanced plugin architecture with clear layer separation
- 🔄 Refactored to modular, composable plugin system

### v2.0.0 (2025-11-14) - 7-Stage AI SDLC
- ✨ Added complete 7-stage AI SDLC methodology
- ✨ Added requirement traceability framework (REQ-* keys)
- ✨ Added AI agent specifications for each stage
- ✨ Added BDD testing guidelines (System Test & UAT stages)
- ✨ Added Runtime Feedback stage with observability integration
- ✨ Added complete example project (customer_portal)
- ✨ Added comprehensive methodology guide (3,300+ lines)

### v1.0.0 (2025-10-17) - Initial Release
- Initial release with Key Principles principles
- TDD workflow for Code stage
- Claude Code plugin marketplace

---

**"Excellence or nothing"** 🔥
