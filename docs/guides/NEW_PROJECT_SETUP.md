# Setting Up a New Project with AI SDLC Method

**Complete setup guide for creating a new project with the 7-Stage AI SDLC Methodology.**

**Time**: 30-45 minutes
**Audience**: Developers setting up their first project

**Other guides**:
- ⚡ **[Quick Start](../../QUICKSTART.md)** - Get started in 5 minutes
- 🎯 **[Complete Journey](JOURNEY.md)** - Full 7-stage walkthrough with examples (2-3 hours)

---

## Prerequisites

- ✅ Claude Code installed (CLI or VS Code extension)
- ✅ Git installed
- ✅ Optional: AI SDLC Method repository cloned (for Python tools)

---

## Step-by-Step Setup

### Step 1: Install AI SDLC Plugin

The AI SDLC methodology plugin can be installed using the Python installer:

```bash
# Navigate to your project
cd /path/to/your-project

# Run the installer from the ai_sdlc_method repository
python /path/to/ai_sdlc_method/claude-code/installers/aisdlc-setup.py

# This creates:
# .claude-plugin/plugins/aisdlc-methodology/
#   ├── agents/        (7 stage personas)
#   ├── commands/      (8 slash commands)
#   ├── skills/        (42 skills)
#   ├── config/        (stage configurations)
#   ├── templates/     (workspace scaffolding)
#   └── hooks/         (lifecycle hooks)
```

**Verify installation**:
```bash
ls .claude-plugin/plugins/aisdlc-methodology/
# Should show: agents/, commands/, skills/, config/, templates/, hooks/
```

✅ The plugin is now installed in your project!

---

### Step 2: Create Your New Project Directory

```bash
# Create and navigate to your new project
mkdir -p /path/to/my-new-project
cd /path/to/my-new-project

# Initialize git (recommended)
git init
```

---

### Step 3: Optional - Install Workspace Templates

The installer can also set up workspace templates for task tracking:

```bash
# The installer creates workspace structure
# .ai-workspace/
#   ├── tasks/
#   │   ├── active/ACTIVE_TASKS.md
#   │   ├── finished/
#   │   └── archive/
#   ├── templates/
#   │   └── AISDLC_METHOD_REFERENCE.md
#   └── config/
#       └── workspace_config.yml
```

**Note**: The aisdlc-methodology plugin includes templates. You can use the installer's `--templates` flag if you want to install them separately.

---

### Step 4: Create Your Project Intent

Create an intent file describing what you want to build:

```bash
# Create INTENT.md
cat > INTENT.md <<'EOF'
# Intent: [Your Project Name]

**Intent ID**: INT-001
**Date**: 2025-01-21
**Product Owner**: your-name@company.com
**Priority**: High

---

## User Story

As a [type of user], I want to [do something] so that I can [achieve goal].

---

## Business Context

[Describe the business need, problem to solve, and why this matters]

**Business Value**:
- Benefit 1
- Benefit 2
- Benefit 3

**Success Metrics**:
- Metric 1: Target value
- Metric 2: Target value

---

## High-Level Requirements

1. **Feature 1**
   - Sub-requirement A
   - Sub-requirement B

2. **Feature 2**
   - Sub-requirement A
   - Sub-requirement B

---

## Out of Scope (This Intent)

- Thing 1
- Thing 2

---

## Constraints

- Constraint 1
- Constraint 2

---

## Dependencies

- Dependency 1
- Dependency 2

---

## Next Steps

This intent will flow through the 7-stage AI SDLC methodology.

---

**Status**: Ready for Requirements Stage
EOF
```

---

### Step 5: Create Project Configuration

Create a configuration file for your project:

```bash
# Create config directory
mkdir -p config

# Create project configuration
cat > config/config.yml <<'EOF'
project:
  name: My New Project
  team: Development Team
  tech_lead: your-name@company.com
  classification: internal

  description: |
    [Brief description of your project]

# ============================================================================
# AI SDLC METHODOLOGY - 7-STAGE CONFIGURATION
# ============================================================================

ai_sdlc:
  # Plugin is loaded from .claude-plugin/plugins/aisdlc-methodology/

  # Enable stages you want to use
  enabled_stages:
    - requirements    # Generate REQ-* keys
    - design          # Technical solution
    - tasks           # Work breakdown
    - code            # TDD implementation
    - system_test     # BDD integration testing
    - uat             # Business validation
    - runtime_feedback # Production monitoring

  # Stage-specific configuration
  stages:
    requirements:
      personas:
        product_owner: your-po@company.com
        business_analyst: your-ba@company.com

      requirement_types:
        - type: functional
          prefix: REQ-F
        - type: non_functional
          prefix: REQ-NFR
        - type: data_quality
          prefix: REQ-DATA

    code:
      testing:
        coverage_minimum: 80
        tdd_required: true

      key_principles:
        enabled: true
        enforce_tdd: true

    system_test:
      bdd:
        enabled: true
        framework: behave  # or: cucumber, pytest-bdd

      coverage_minimum: 90
EOF
```

---

### Step 6: Initial Git Commit

```bash
# Review what was created
ls -la

# Stage all files
git add .

# Initial commit
git commit -m "Initial project setup with AI SDLC Method

- Developer Workspace installed (.ai-workspace/)
- Claude commands installed (.claude/commands/)
- Project intent defined (INTENT.md)
- AI SDLC configuration (config/config.yml)
- Ready for 7-stage development process

🤖 Generated with [Claude Code](https://claude.ai/code)
"
```

---

### Step 7: Start Using the Methodology

You can now use Claude with the AI SDLC methodology. The plugin provides slash commands:

```bash
# Check methodology status
/aisdlc-status

# View available commands
/aisdlc-help

# Checkpoint your work
/aisdlc-checkpoint-tasks
```

Ask Claude to help with any SDLC stage:
```
"Generate requirements from INTENT.md using the Requirements Agent"
"Design the authentication service following the Design Agent specifications"
```

---

## Your Project Structure

After setup, your project should look like this:

```
my-new-project/
├── .claude-plugin/              # Claude Code plugins
│   └── plugins/
│       └── aisdlc-methodology/  # AI SDLC methodology plugin
│           ├── agents/          # 7 stage personas
│           ├── commands/        # 8 slash commands
│           ├── skills/          # 42 skills
│           ├── config/          # Stage configurations
│           ├── templates/       # Workspace scaffolding
│           └── hooks/           # Lifecycle hooks
│
├── .ai-workspace/               # Optional: Developer workspace
│   ├── tasks/
│   │   ├── active/ACTIVE_TASKS.md
│   │   └── finished/
│   ├── templates/
│   │   └── AISDLC_METHOD_REFERENCE.md
│   └── config/
│       └── workspace_config.yml
│
├── config/
│   └── config.yml               # AI SDLC configuration
│
├── INTENT.md                    # Your project intent (INT-001)
├── .gitignore                   # Git configuration
└── README.md                    # (Create this next)
```

---

## Running the 7-Stage AI SDLC Process

### Stage 1: Requirements

```
Ask Claude:

"Using the AI SDLC Requirements Stage configuration from config/config.yml,
generate structured requirements from INTENT.md.

Create:
1. REQ-F-* (functional requirements)
2. REQ-NFR-* (non-functional requirements)
3. REQ-DATA-* (data quality requirements)
4. Acceptance criteria for each
5. Traceability matrix"
```

**Expected Output**: `docs/requirements/REQUIREMENTS.md`

### Stage 2: Design

```
Ask Claude:

"Create technical solution for the requirements:
1. Component diagrams (Mermaid)
2. Data models
3. API specifications
4. Architecture decision records (ADRs)

Map each component to requirement keys."
```

**Expected Output**: Design docs in `docs/design/`

### Stage 3: Tasks

```
Ask Claude:

"Break the design into work items:
1. Create epic
2. Generate user stories
3. Create technical tasks
4. Add estimates and dependencies
5. Tag all items with requirement keys"
```

**Expected Output**: Work breakdown structure

### Stage 4: Code (TDD)

Follow TDD cycle:

```bash
# RED: Write failing test
npm test  # or: pytest

# GREEN: Implement minimal solution
npm test  # PASSES

# REFACTOR: Improve code quality
npm test  # STILL PASSES

# COMMIT: Save with REQ tags
/finish-task <id>
/commit-task <id>
```

### Stage 5: System Test (BDD)

```
Ask Claude:

"Create BDD integration tests:
1. Write feature files (Given/When/Then)
2. Implement step definitions
3. Validate all requirements
4. Achieve 90%+ coverage"
```

### Stage 6: UAT

```
Ask Claude:

"Create UAT test cases for business validation:
1. Manual test procedures
2. Automated UAT tests
3. Sign-off checklist"
```

### Stage 7: Runtime Feedback

```
Ask Claude:

"Set up production monitoring:
1. Tag all metrics with REQ keys
2. Configure alerts
3. Set up dashboards
4. Define feedback loop to new intents"
```

---

## Available Slash Commands

The aisdlc-methodology plugin provides 8 commands:

```bash
/aisdlc-status               # Show methodology status
/aisdlc-help                 # View available commands and agents
/aisdlc-checkpoint-tasks     # Save current task state
/aisdlc-commit-task          # Generate commit message for task
/aisdlc-finish-task          # Complete task with documentation
/aisdlc-refresh-context      # Reload methodology configuration
/aisdlc-release              # Generate release manifest
/aisdlc-update               # Update methodology to latest version
```

---

## Common Workflows

### Daily Development

```bash
# Morning routine
cd /path/to/my-new-project

# Check methodology status
/aisdlc-status

# Work on features
# (Use Claude to help with TDD, design, requirements, etc.)

# Checkpoint your work
/aisdlc-checkpoint-tasks

# Complete a task
/aisdlc-finish-task
/aisdlc-commit-task
```

### Adding Features

```bash
# 1. Create new intent
cat > INTENT_002.md <<EOF
# Intent: New Feature Name
...
EOF

# 2. Ask Claude to guide you through the 7 stages
# "Generate requirements from INTENT_002.md"
# "Create design for the new feature"
# "Implement using TDD workflow"
# ... etc
```

### Bug Fixes

```bash
# 1. Document the bug as an intent
cat > INTENT_BUG_001.md <<EOF
# Intent: Fix authentication timeout bug
...
EOF

# 2. Follow TDD for bug fix
# - Write test that reproduces bug (RED)
# - Fix bug (GREEN)
# - Refactor (REFACTOR)
# - Commit with REQ tags
```

---

## Tips & Best Practices

### 1. **Start Small**
Don't enable all 7 stages immediately. Start with:
- Requirements → Code → System Test

Then add others as you get comfortable.

### 2. **Use Feature Flags**
Every task should have a feature flag:
```yaml
feature-task-5-payment-processing: false  # Default off
```

### 3. **Keep Intents Focused**
One intent = one user story or small feature
Better to have INT-001, INT-002, INT-003 than one huge INT-001

### 4. **Tag Everything with REQ Keys**
In code:
```javascript
// Implements: REQ-F-AUTH-001
function login(email, password) { ... }
```

In tests:
```javascript
// Validates: REQ-F-AUTH-001
test('user can login with valid credentials', ...)
```

In commits:
```
Implement user login (REQ-F-AUTH-001)
```

### 5. **Use Check-ins**
During `/start-session`, set check-in frequency (15-30 min).
Update `.ai-workspace/session/current_session.md` regularly.

---

## Troubleshooting

### Issue: Commands not working

```bash
# Check if commands installed
ls .claude-plugin/plugins/aisdlc-methodology/commands/

# Should show 8 commands (aisdlc-*.md)

# Reinstall if needed
python /path/to/ai_sdlc_method/claude-code/installers/aisdlc-setup.py
```

### Issue: Plugin not loading

```bash
# Check plugin structure
ls .claude-plugin/plugins/aisdlc-methodology/

# Should show: agents/, commands/, skills/, config/, templates/, hooks/

# Reinstall if needed
python /path/to/ai_sdlc_method/claude-code/installers/aisdlc-setup.py
```

### Issue: Configuration not found

```bash
# Check config file exists
cat config/config.yml

# Verify plugin config files
ls .claude-plugin/plugins/aisdlc-methodology/config/stages_config.yml
ls .claude-plugin/plugins/aisdlc-methodology/config/config.yml
```

---

## Quick Reference Card

### For Each New Project
```bash
# 1. Create project
mkdir my-new-project && cd my-new-project
git init

# 2. Install AI SDLC plugin
python /path/to/ai_sdlc_method/claude-code/installers/aisdlc-setup.py

# 3. Create intent and config
touch INTENT.md
mkdir config && touch config/config.yml

# 4. Start using the methodology
/aisdlc-status
/aisdlc-help
```

---

## Next Steps

1. **Read the guide**: `cat .ai-workspace/README.md`
2. **Review examples**: [ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples)
3. **Start your first session**: `/start-session`
4. **Generate requirements**: Ask Claude to process your INTENT.md

---

## Updating Existing Projects

**Scenario:** You already have AI SDLC Method installed and want to update to the latest version.

### Strategy 1: Reinstall Plugin (Recommended)

**Use Case:** Clean update, ensures you have the latest plugin structure

```bash
cd /path/to/your/project

# Backup current state first
git commit -am "Checkpoint before AI SDLC update"

# Run the installer (it will update existing installation)
python /path/to/ai_sdlc_method/claude-code/installers/aisdlc-setup.py

# Review changes
git diff

# Commit if satisfied
git add .
git commit -m "Update AI SDLC methodology plugin to latest version"
```

**What gets UPDATED**:
- `.claude-plugin/plugins/aisdlc-methodology/` - Complete plugin structure
  - agents/ (7 stage personas)
  - commands/ (8 slash commands)
  - skills/ (42 skills)
  - config/ (stage configurations)
  - templates/ (workspace scaffolding)
  - hooks/ (lifecycle hooks)

**What gets PRESERVED** (your work):
- `.ai-workspace/tasks/` - Your current and finished tasks
- `config/` - Your project configuration
- All your source code and project files

### Strategy 2: Use the Update Command

The plugin provides an update command:

```bash
# Check for updates
/aisdlc-update

# This will guide you through updating the methodology
```

### Strategy 3: Manual Pull from Repository

If you have the ai_sdlc_method repository cloned:

```bash
# Update the repository
cd /path/to/ai_sdlc_method
git pull

# Reinstall in your project
cd /path/to/your/project
python /path/to/ai_sdlc_method/claude-code/installers/aisdlc-setup.py
```

---

## Component Inventory

Track which components you have installed:

### Check Installed Versions

```bash
# Check workspace version
cat .ai-workspace/README.md | head -5

# Check installed commands
ls .claude/commands/aisdlc-* | wc -l
# Should show: 6 commands (aisdlc-*)

# Check installed agents
ls .claude/agents/ | wc -l
# Should show: 7 agents (one per SDLC stage)

# Check global plugins
ls ~/.config/claude/claude-code/plugins/
# Should show: aisdlc-core, aisdlc-methodology, principles-key (+ more)

# Check project plugins (if installed locally)
ls .claude/claude-code/plugins/
```

### What Should Be Installed

**Minimal (Workspace + Commands):**
- `.ai-workspace/` (11 files)
- `.claude/commands/` (16 commands)
- `.claude/agents/` (7 agents)
- `CLAUDE.md`

**With Plugins (Startup Bundle):**
- Everything from Minimal
- Global plugins:
  - `aisdlc-core`
  - `aisdlc-methodology`
  - `principles-key`

**With Plugins (Enterprise Bundle):**
- Everything from Startup
- Additional plugins:
  - `testing-skills`
  - `code-skills`
  - `design-skills`
  - `requirements-skills`
  - `runtime-skills`
  - `python-standards`

### Verify Installation

```bash
# Run installation verification
python /Users/jim/src/apps/ai_sdlc_method/installers/validate_traceability.py

# Check if all slash commands work
/aisdlc-status
```

---

## Keeping AI SDLC Method Up to Date

### Use the Update Command

The simplest way to check for and apply updates:

```bash
# In your project directory
/aisdlc-update
```

This command will check if there are newer versions available and guide you through the update process.

### Manual Update

If you have the ai_sdlc_method repository cloned locally:

```bash
# 1. Update the repository
cd /path/to/ai_sdlc_method
git pull

# 2. Review changes
git log --oneline -10

# 3. Reinstall in your project
cd /path/to/your/project
python /path/to/ai_sdlc_method/claude-code/installers/aisdlc-setup.py

# 4. Review and commit
git diff
git add .claude-plugin/
git commit -m "Update AI SDLC methodology plugin"
```

---

## Next Steps: See the Methodology in Action

Now that your project is set up, see the complete 7-stage methodology with a real example:

👉 **[Complete Journey Guide](JOURNEY.md)** - Full walkthrough from setup to UAT (2-3 hours) ⭐

This guide shows you:
- All 7 stages with concrete examples
- Real code, real commands, real workflows
- Complete traceability from intent to UAT sign-off
- How to use the methodology for actual feature development

---

## Getting Help

- **Quick Start**: [QUICKSTART.md](../../QUICKSTART.md) - Get started in 5 minutes
- **Complete Journey**: [JOURNEY.md](JOURNEY.md) - Full 7-stage walkthrough
- **Documentation**: [docs/README.md](../README.md) - Complete documentation index
- **Example Projects**: [ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples)
- **Component Inventory**: [docs/info/INVENTORY.md](../info/INVENTORY.md)
- **Issues**: https://github.com/foolishimp/ai_sdlc_method/issues

---

**"Excellence or nothing"** 🔥
