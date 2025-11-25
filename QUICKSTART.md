# ai_sdlc_method Quick Start Guide

Get started with the **7-Stage AI SDLC Methodology** in 5-10 minutes.

**Choose your path**:
- ⚡ **Quick Start** (below) - Install plugin and try it out (5-10 min)
- 🏗️ **[New Project Setup](docs/guides/NEW_PROJECT_SETUP.md)** - Complete project setup guide (30 min)
- 🎯 **[Complete Journey](docs/guides/JOURNEY.md)** - Full 7-stage walkthrough with examples (2-3 hours)

## Table of Contents
- [What is ai_sdlc_method?](#what-is-ai_sdlc_method)
- [Quick Install (5 minutes)](#quick-install-5-minutes)
- [Quick Start Example](#quick-start-example)
- [Common Use Cases](#common-use-cases)
- [Next Steps](#next-steps)

---

## What is ai_sdlc_method?

ai_sdlc_method is an **Intent-Driven AI SDLC Methodology** providing:

### 7-Stage Software Development Lifecycle

```
Intent → Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
           ↑                                                                    ↓
           └────────────────────── Feedback Loop ──────────────────────────────┘
```

**Complete Lifecycle**:
1. **Requirements** - Transform intent into structured requirements (REQ-F-*, REQ-NFR-*, REQ-DATA-*)
2. **Design** - Create technical solution architecture (components, APIs, data models)
3. **Tasks** - Break down into work units with Jira orchestration
4. **Code** - TDD implementation (RED → GREEN → REFACTOR) + Key Principles
5. **System Test** - BDD integration testing (Given/When/Then scenarios)
6. **UAT** - Business validation and sign-off
7. **Runtime Feedback** - Production telemetry closes the loop back to requirements

### Key Features

✅ **Requirement Traceability** - Auto-generated matrix tracking REQ-* from intent to runtime
✅ **AI Agent Configurations** - Detailed specs for AI agents at each SDLC stage
✅ **Bidirectional Feedback** - Production issues flow back to requirements
✅ **Key Principles** - Foundation for Code stage (TDD, Fail Fast, Modular, etc.)
✅ **Claude Code Plugins** - Installable methodology and standards
✅ **Federated Architecture** - Compose contexts across corporate → division → team → project

---

## Quick Install (5 minutes)

### Step 1: Install the Plugin

```bash
# In Claude Code (CLI or VS Code)
/plugin marketplace add foolishimp/ai_sdlc_method
/plugin install @aisdlc/aisdlc-methodology
```

**Expected output**:
```
✓ @aisdlc/aisdlc-methodology v2.0.0 installed

Claude now has access to:
- Complete 7-stage AI SDLC methodology
- AI agent configurations for each stage
- Key Principles (TDD, Fail Fast, Modular, etc.)
- TDD workflow (RED → GREEN → REFACTOR)
- BDD testing guides
- Requirement traceability system
```

### Step 2: Try It Out

**Ask Claude:**
```
"Help me implement user authentication following the AI SDLC methodology"
```

**Claude will guide you through**:
1. **Requirements** - Generate REQ-F-AUTH-001, REQ-NFR-PERF-001, etc.
2. **Design** - Create AuthenticationService, API specs, data models
3. **Tasks** - Break into work units (Jira tickets with REQ tags)
4. **Code** - TDD implementation (RED → GREEN → REFACTOR)
5. **System Test** - BDD scenarios (Given/When/Then)
6. **UAT** - Business validation test cases
7. **Runtime Feedback** - Telemetry setup with REQ key tagging

✅ **That's it!** You're using the 7-stage methodology.

### Want More Detail?

👉 **[Complete Journey](docs/guides/JOURNEY.md)** - Full 7-stage walkthrough with code examples (2-3 hours) ⭐
👉 **[New Project Setup](docs/guides/NEW_PROJECT_SETUP.md)** - Detailed setup guide for your project (30 min)
👉 **[Example Projects](https://github.com/foolishimp/ai_sdlc_examples)** - Complete example projects (separate repo)

---

## Quick Start Example

Once the plugin is installed, Claude understands the 7-stage methodology:

```bash
# Clone repository
git clone https://github.com/foolishimp/ai_sdlc_method.git
cd ai_sdlc_method

# Install dependencies
pip install pyyaml
```

### Example: Load and Use Methodology

```python
from pathlib import Path
import yaml

# Load the 7-stage methodology configuration
stages_config_path = Path("claude-code/plugins/aisdlc-methodology/config/stages_config.yml")
with open(stages_config_path) as f:
    methodology = yaml.safe_load(f)

# Access stage specifications
requirements_stage = methodology['ai_sdlc']['stages']['requirements']
code_stage = methodology['ai_sdlc']['stages']['code']

# Get agent configuration for Requirements stage
requirements_agent = requirements_stage['agent']
print(f"Role: {requirements_agent['role']}")  # "Intent Store & Traceability Hub"

# Get traceability matrix specification
traceability = requirements_stage['outputs']['traceability_matrix']
print(f"Tool: {traceability['tool']}")  # "validate_traceability.py --matrix"
```

### Generate Traceability Matrix

```bash
# Auto-generate requirements traceability matrix
python installers/validate_traceability.py --matrix > docs/TRACEABILITY_MATRIX.md

# Auto-generate component inventory
python installers/validate_traceability.py --inventory > INVENTORY.md

# Validate traceability (check for gaps)
python installers/validate_traceability.py --check-all
```

---

## Common Use Cases

### Use Case 1: Full Lifecycle Development

**Scenario:** Develop a feature from intent to production with complete traceability.

**With Claude Code Plugin:**
```bash
# Install methodology
/plugin install @aisdlc/aisdlc-methodology

# Ask Claude to follow 7-stage process
"Implement customer authentication feature using AI SDLC methodology"

Claude guides you through:
1. Requirements: Generate REQ-F-AUTH-001, REQ-NFR-PERF-001, etc.
2. Design: Create AuthenticationService component, API specs
3. Tasks: Break into JIRA tickets (PORTAL-123, PORTAL-124)
4. Code: TDD implementation with requirement tags
5. System Test: BDD scenarios (Given/When/Then)
6. UAT: Business validation test cases
7. Runtime Feedback: Setup telemetry with REQ key tagging

Result:
- Complete traceability from intent to production
- Auto-generated traceability matrix (docs/TRACEABILITY_MATRIX.md)
- 70%+ implementation coverage, 25%+ test coverage
```

### Use Case 2: Code Stage Only (TDD Focus)

**Scenario:** You already have requirements and design, just need implementation.

**Ask Claude:**
```
"Implement these requirements using TDD and the Key Principles"

Claude will:
- Follow TDD workflow strictly (RED → GREEN → REFACTOR)
- Apply Key Principles (Test First, Fail Fast, Modular, etc.)
- Ensure test coverage meets targets
- Tag code with requirement keys (# Implements: REQ-*)
```

### Use Case 3: Traceability Audit

**Scenario:** Understand which requirements are implemented and tested.

```bash
# Generate traceability matrix
python installers/validate_traceability.py --matrix > docs/TRACEABILITY_MATRIX.md

# View summary
cat docs/TRACEABILITY_MATRIX.md | head -30

Output:
- Total Requirements: 20
- Implementation Coverage: 70.0% (14/20)
- Test Coverage: 25.0% (5/20)
- Design Coverage: 165.0%

# Identify gaps
python installers/validate_traceability.py --check-all
```

### Use Case 4: Runtime Issue → New Intent

**Scenario:** Production alert triggers feedback loop to requirements.

```
Alert: "ERROR: REQ-F-AUTH-001 - Auth timeout in production"

Claude (Runtime Feedback Agent):
1. Traces REQ-F-AUTH-001 back through stages
2. Identifies root cause (performance requirement violated)
3. Generates new intent: INT-042 "Fix auth timeout"
4. Links to original requirement REQ-F-AUTH-001

New cycle begins at Requirements stage
```

---

## 7-Stage Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    INTENT MANAGER                           │
│  "Users need self-service portal with authentication"       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  1. REQUIREMENTS STAGE (Traceability Hub)                   │
│     • Transform intent → structured requirements            │
│     • Generate traceability matrix (auto)                   │
│     • Output: REQ-F-AUTH-001, REQ-NFR-PERF-001, etc.       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. DESIGN STAGE                                            │
│     • Requirements → technical solution                     │
│     • Output: AuthenticationService, API specs, data models │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. TASKS STAGE                                             │
│     • Design → work units                                   │
│     • Output: Jira tickets (PORTAL-123) tagged with REQ-*  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. CODE STAGE                                              │
│     • TDD: RED → GREEN → REFACTOR                          │
│     • Key Principles (7 principles)                         │
│     • Output: auth_service.py # Implements: REQ-F-AUTH-001 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  5. SYSTEM TEST STAGE                                       │
│     • BDD: Given/When/Then scenarios                        │
│     • Output: auth.feature # Validates: REQ-F-AUTH-001     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  6. UAT STAGE                                               │
│     • Business validation                                   │
│     • Output: UAT-001 → REQ-F-AUTH-001 (Business sign-off) │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  7. RUNTIME FEEDBACK STAGE                                  │
│     • Telemetry: Tagged with REQ-F-AUTH-001                │
│     • Alerts → New intents (feedback loop)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         └──────────► Back to Intent Manager
```

---

## Documentation

### Core Methodology
- **[docs/README.md](docs/README.md)** - Documentation index with role-based learning paths ⭐ **Start here**
- [docs/requirements/AI_SDLC_OVERVIEW.md](docs/requirements/AI_SDLC_OVERVIEW.md) - High-level overview (~30 min read)
- [docs/requirements/AI_SDLC_REQUIREMENTS.md](docs/requirements/AI_SDLC_REQUIREMENTS.md) - Complete requirements with 7-stage methodology
- [claude-code/plugins/aisdlc-methodology/config/stages_config.yml](claude-code/plugins/aisdlc-methodology/config/stages_config.yml) - Complete agent specifications (1,273 lines)

### Implementation Requirements
- [docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md](docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) - 20 requirements for building ai_sdlc_method itself
- [docs/TRACEABILITY_MATRIX.md](docs/TRACEABILITY_MATRIX.md) - Auto-generated traceability matrix
- [docs/REQUIREMENTS_AUDIT.md](docs/REQUIREMENTS_AUDIT.md) - Requirements audit and analysis

### Plugin Documentation
- [claude-code/plugins/README.md](claude-code/plugins/README.md) - Plugin creation and usage guide
- [claude-code/plugins/aisdlc-methodology/README.md](claude-code/plugins/aisdlc-methodology/README.md) - Methodology plugin docs
- [claude-code/plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md](claude-code/plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md) - The 7 Key Principles

### Examples
- **[ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples)** - Complete example projects (separate repo) ⭐

---

## Component Inventory

See [docs/info/INVENTORY.md](docs/info/INVENTORY.md) for complete list of all components.

**Quick Stats** (v0.1.0):
- **Implementation Requirements:** 20 (70% implemented, 25% tested)
- **Templates:** 38 files (~27,400 lines)
- **Plugins:** 9 plugins + 4 bundles
- **Commands:** 16 slash commands
- **Agents:** 7 stage-specific agents
- **Total:** 129+ files (~48,900 lines)

**Auto-Generated Artifacts:**
- `docs/TRACEABILITY_MATRIX.md` - Requirement coverage matrix
- `INVENTORY.md` - Component inventory (can be auto-generated)

---

## Installation Methods

### Method 1: Claude Code Marketplace (Recommended)

```bash
# Add marketplace
/plugin marketplace add foolishimp/ai_sdlc_method

# Install plugins
/plugin install @aisdlc/aisdlc-methodology

# Check status
/plugin list
```

**Pros:** Easy to use, auto-updates
**Cons:** Plugins only (no templates/commands)

### Method 2: Python Installer (Complete)

```bash
# Clone repository
git clone https://github.com/foolishimp/ai_sdlc_method.git
cd ai_sdlc_method

# Install to your project
python installers/setup_all.py \
  --target /path/to/your/project \
  --with-plugins \
  --bundle startup
```

**Pros:** Complete installation (templates, commands, agents, plugins)
**Cons:** Manual updates

### Method 3: Hybrid (Best of Both)

Use Python installers for templates/commands, marketplace for plugins:

```bash
# Install workspace and commands
python installers/setup_workspace.py --target /path/to/your/project
python installers/setup_commands.py --target /path/to/your/project

# Install plugins via marketplace
/plugin install @aisdlc/aisdlc-methodology
```

**Pros:** Flexibility + convenience
**Cons:** Two-step process

---

## Updating

### Check Current Version

```bash
# View version tags
git tag -l "v*"

# Current version
cat INVENTORY.md | grep "Version:"
```

### Update Plugins

```bash
# Claude Code marketplace
/plugin update @aisdlc/aisdlc-methodology
```

### Update Templates & Commands

```bash
# Navigate to ai_sdlc_method repository
cd /path/to/ai_sdlc_method
git pull

# Refresh your project
cd /path/to/your/project
python /path/to/ai_sdlc_method/installers/setup_workspace.py --force
python /path/to/ai_sdlc_method/installers/setup_commands.py --force
```

---

## Next Steps

### For New Users

1. ✅ **You just did the quick start!** (above)
2. 📖 **[Follow the Complete Journey](docs/guides/JOURNEY.md)** - See all 7 stages in detail (2-3 hours) ⭐
3. 🏗️ **[Set Up Your Project](docs/guides/NEW_PROJECT_SETUP.md)** - Detailed setup for your real project (30 min)
4. 📚 **[Learn the Methodology](docs/README.md)** - Role-based learning paths
5. 💡 **[Review Example Projects](https://github.com/foolishimp/ai_sdlc_examples)** - Complete walkthrough

### For Developers

1. **Review implementation requirements**: [docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md](docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md)
2. **Check traceability**: [docs/TRACEABILITY_MATRIX.md](docs/TRACEABILITY_MATRIX.md)
3. **Read Key Principles**: [claude-code/plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md](claude-code/plugins/aisdlc-methodology/docs/principles/KEY_PRINCIPLES.md)
4. **Follow TDD workflow**: [claude-code/plugins/aisdlc-methodology/docs/processes/TDD_WORKFLOW.md](claude-code/plugins/aisdlc-methodology/docs/processes/TDD_WORKFLOW.md)

### For Role-Specific Learning

See [docs/README.md](docs/README.md) for learning paths tailored to:
- Business Analysts / Product Owners
- Architects / Technical Leads
- Developers
- QA Engineers
- DevOps / SRE
- Project Managers / Scrum Masters

---

## Support & Resources

- **Happy Path Journey:** [docs/JOURNEY.md](docs/JOURNEY.md) - Setup to UAT guided tour ⭐
- **Component Inventory:** [docs/info/INVENTORY.md](docs/info/INVENTORY.md) - Complete deployment guide
- **Traceability Matrix:** [docs/TRACEABILITY_MATRIX.md](docs/TRACEABILITY_MATRIX.md) - Auto-generated coverage
- **New Project Setup:** [docs/guides/NEW_PROJECT_SETUP.md](docs/guides/NEW_PROJECT_SETUP.md) - Step-by-step setup
- **Plugin Guide:** [docs/guides/PLUGIN_GUIDE.md](docs/guides/PLUGIN_GUIDE.md) - Plugin creation and usage
- **Issues:** https://github.com/foolishimp/ai_sdlc_method/issues
- **Examples:** [ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples) - Working examples (separate repo)

---

## Version History

- **v0.1.0** (2025-11-24) - Initial Requirements Traceability Implementation
  - Requirements Agent as Traceability Hub
  - Auto-generated traceability matrix
  - 20 implementation requirements (70% implemented, 25% tested)
  - Clean separation: implementation vs example requirements

---

**"Excellence or nothing"** 🔥

**Ready to start!** Install the plugin or review the examples. 🚀
