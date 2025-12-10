# ai_sdlc_method

**Intent-Driven AI SDLC Methodology** with homeostatic control, requirement traceability, and 7-stage agent orchestration.

**Mantra**: **"Excellence or nothing"** 🔥

Please credit the work done here if you find it useful!
Would love to hear your feedback, improvements, and contributions.

---

## What Is This?

A complete **AI-Augmented Software Development Lifecycle (AI SDLC)** framework providing:

- **🎯 7-Stage Methodology**: Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
- **🔗 Requirement Traceability**: Track requirement keys (REQ-F-*, REQ-NFR-*, REQ-DATA-*) from intent to runtime
- **🤖 AI Agent Configurations**: Detailed specifications for AI agents at each SDLC stage
- **⚖️ Homeostatic Control**: Sensors detect quality gaps, actuators automatically fix them
- **📦 Claude Code Plugin**: Single consolidated `aisdlc-methodology` plugin with 42 skills, 7 agents, 8 commands
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

### What Gets Installed

```
your-project/
├── .claude/settings.json          # Plugin from GitHub marketplace
└── .ai-workspace/                  # Task tracking (created by default)
    ├── tasks/active/ACTIVE_TASKS.md
    ├── tasks/finished/
    ├── templates/                  # TASK_TEMPLATE.md, FINISHED_TASK_TEMPLATE.md
    └── config/workspace_config.yml
```

### Installation Options

```bash
# Full setup (plugin + workspace) - DEFAULT
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -

# Plugin only (no workspace)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --no-workspace

# Preview changes without writing
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --dry-run
```

**Safe to re-run**: Existing files (tasks, finished work) are preserved.

**What you get**:
- Complete 7-stage AI SDLC workflow
- Key Principles development principles (TDD, Fail Fast, Modular, etc.)
- TDD workflow (RED → GREEN → REFACTOR)
- BDD testing guidelines
- Requirement traceability framework (REQ-F-*, REQ-NFR-*, REQ-DATA-*)
- Task management workspace with templates

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

## The Plugin: aisdlc-methodology

A single consolidated plugin containing everything:

### What's Included

| Category | Count | Description |
|----------|-------|-------------|
| **Skills** | 42 | Requirements, design, code, testing, runtime, principles |
| **Agents** | 7 | One per SDLC stage |
| **Commands** | 8 | `/aisdlc-*` slash commands |
| **Hooks** | 4 | Welcome, reminders, formatting |

### Skills by Category

- **Core Skills**: Requirement traceability, key propagation, coverage detection
- **Requirements Skills**: Intent transformation, disambiguation, refinement
- **Design Skills**: Architecture, ADRs, solution design
- **Code Skills**: TDD workflow (RED→GREEN→REFACTOR), BDD, tech debt management
- **Testing Skills**: Coverage validation, test generation, integration testing
- **Runtime Skills**: Telemetry, observability, feedback loop
- **Principles Skills**: 7 Key Principles enforcement, quality gates

### Commands

| Command | Purpose |
|---------|---------|
| `/aisdlc-help` | Full methodology guide |
| `/aisdlc-status` | Task queue status |
| `/aisdlc-checkpoint-tasks` | Save progress, create finished task docs |
| `/aisdlc-finish-task <id>` | Complete a specific task |
| `/aisdlc-commit-task <id>` | Generate commit message with REQ tags |
| `/aisdlc-release` | Create new project release |
| `/aisdlc-refresh-context` | Reload methodology context |

👉 [Full Plugin Documentation](.claude-plugin/plugins/aisdlc-methodology/README.md)

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
├── .claude-plugin/                  # Marketplace root (GitHub discovery)
│   ├── marketplace.json             # Plugin registry
│   └── plugins/
│       └── aisdlc-methodology/      # The consolidated plugin
│           ├── .claude-plugin/plugin.json
│           ├── skills/              # 42 skills (7 categories)
│           ├── agents/              # 7 SDLC stage agents
│           ├── commands/            # 8 slash commands
│           ├── hooks/               # 4 lifecycle hooks
│           ├── config/              # stages_config.yml, config.yml
│           └── docs/                # Principles, TDD workflow
│
├── claude-code/installers/          # Installation scripts
│   ├── aisdlc-setup.py              # One-liner installer
│   └── tests/                       # 23 unit tests
│
├── testmkt/plugins/hello-world/     # Test plugin for validation
│
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

Simply re-run the installer. It's safe and preserves your work:

```bash
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -
```

**Preserved**:
- `.ai-workspace/tasks/active/ACTIVE_TASKS.md` (your tasks)
- `.ai-workspace/tasks/finished/*` (completed work)
- Any customized templates

**Created if missing**:
- `.claude/settings.json`
- `.ai-workspace/templates/*`
- `.ai-workspace/config/*`

The plugin itself always loads fresh from GitHub, so you automatically get the latest version.

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

### v0.4.8 (2025-12-02) - Installer Tests & Documentation ⭐
- ✨ Full workspace created by default (includes templates)
- ✨ 23 unit tests for installer
- ✨ Updated QUICKSTART.md and README.md
- ✨ Safe re-run (preserves existing work)
- 🔧 Fixed installer URL paths

### v0.4.7 (2025-12-02) - Full Workspace Setup
- ✨ Embedded all templates in installer (TASK_TEMPLATE, FINISHED_TASK_TEMPLATE, etc.)
- ✨ Workspace created by default (use `--no-workspace` to skip)
- ✨ Proper dogfooding (project loads its own plugin from GitHub)

### v0.4.6 (2025-12-02) - GitHub Marketplace Fix
- 🐛 Fixed plugin source path resolution (relative to repo root)
- ✨ Added test plugin for marketplace validation
- ✨ Both hello-world and aisdlc-methodology load from GitHub

### v0.4.0-0.4.5 (2025-11-27) - Plugin Consolidation
- 🔄 Consolidated 9 plugins + 4 bundles into single `aisdlc-methodology`
- 🔄 Simplified installer to single-plugin model
- ✨ Added lifecycle hooks (welcome, reminders, formatting)
- ✨ 42 skills, 7 agents, 8 commands in one plugin

### v0.1.0-v0.3.0 (2025-11) - Foundation
- Initial 7-stage AI SDLC methodology
- Multi-plugin architecture (later consolidated)
- Key Principles + TDD workflow

---

**"Excellence or nothing"** 🔥
