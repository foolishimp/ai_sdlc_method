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

### Step 1: Install AI SDLC Plugin (One-Time)

**Do this ONCE** - the plugin will be available to all your future projects.

```bash
# In Claude Code
/plugin marketplace add foolishimp/ai_sdlc_method
/plugin install @aisdlc/aisdlc-methodology
```

**Verify installation**:
```bash
/plugin list
# Should see: @aisdlc/aisdlc-methodology v2.0.0
```

✅ **You only need to do this once!** The methodology is now available to all projects.

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

### Step 3: Optional - Install Development Tools

For advanced features like workspace management and custom commands, you can install additional tools from the ai_sdlc_method repository:

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/foolishimp/ai_sdlc_method.git

# Run installer from the repository
cd my-new-project
python ../ai_sdlc_method/installers/setup_all.py

# This installs:
# - .ai-workspace/ (task tracking, session management)
# - .claude/commands/ (slash commands)
# - .claude/agents/ (7-stage agent definitions)
# - CLAUDE.md (project guidance)
```

**Output**:
```
✅ Developer Workspace (.ai-workspace/)
✅ Claude Commands (.claude/commands/)
✅ Agent Definitions (.claude/agents/)
✅ CLAUDE.md
✅ .gitignore
```

**Note**: This step is optional. The plugin alone provides the complete 7-stage methodology.

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
  # Load 7-stage methodology from global plugins
  methodology_plugin: "~/.config/claude/claude-code/plugins/aisdlc-methodology/config/stages_config.yml"
  principles_key: "~/.config/claude/claude-code/plugins/principles-key/config/config.yml"

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

      quality_gates:
        - all_requirements_have_unique_keys: true
        - all_requirements_have_acceptance_criteria: true

    code:
      testing:
        coverage_minimum: 80
        tdd_required: true

      principles_key:
        enabled: true
        enforce_tdd: true

    system_test:
      bdd:
        enabled: true
        framework: cucumber  # or: behave, jest-cucumber

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

### Step 7: Start Your First AI SDLC Session

```bash
# Start development session
# (This command works because you installed .claude/commands/)
/start-session
```

**Claude will prompt you for**:
- Primary goal (e.g., "Generate requirements from INTENT.md")
- Secondary goal
- Working mode (TDD / Exploration / etc.)

---

## Your Project Structure

After setup, your project should look like this:

```
my-new-project/
├── .ai-workspace/               # Developer Workspace
│   ├── README.md
│   ├── config/
│   │   └── workspace_config.yml
│   ├── tasks/
│   │   ├── todo/TODO_LIST.md
│   │   ├── active/ACTIVE_TASKS.md
│   │   ├── finished/
│   │   └── archive/
│   └── templates/
│
├── .claude/                     # Claude Code integration
│   ├── commands/                # Slash commands
│   │   ├── todo.md
│   │   ├── start-session.md
│   │   ├── finish-task.md
│   │   └── ... (10+ more)
│   └── hooks.json
│
├── config/
│   └── config.yml               # AI SDLC configuration
│
├── INTENT.md                    # Your project intent (INT-001)
├── CLAUDE.md                    # Project guidance
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

Once installed, you can use:

```bash
/todo "description"          # Quick capture a todo
/start-session               # Begin development session
/finish-task <id>            # Complete task with documentation
/commit-task <id>            # Generate commit message
/current-context             # Show current stage context
/load-context                # Load project configuration
```

---

## Common Workflows

### Daily Development

```bash
# Morning routine
cd /path/to/my-new-project
/start-session

# Capture thoughts during coding
/todo "add error handling to payment flow"
/todo "investigate slow query"

# Complete a task
/finish-task 5
/commit-task 5

# End of day
cat .ai-workspace/session/current_session.md  # Review progress
```

### Adding Features

```bash
# 1. Create new intent
cat > INTENT_002.md <<EOF
# Intent: New Feature Name
...
EOF

# 2. Start session
/start-session

# 3. Ask Claude to run through 7 stages
# Stage 1: Requirements
# Stage 2: Design
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
ls .claude/commands/

# Reinstall if needed
python /Users/jim/src/apps/ai_sdlc_method/installers/setup_commands.py --force
```

### Issue: Plugins not loading

```bash
# Check global plugins
ls ~/.config/claude/claude-code/plugins/

# Reinstall if needed
cd /Users/jim/src/apps/ai_sdlc_method
python installers/setup_plugins.py --global --bundle startup --force
```

### Issue: Configuration not found

```bash
# Check config file exists
cat config/config.yml

# Verify plugin paths
ls ~/.config/claude/claude-code/plugins/aisdlc-methodology/config/stages_config.yml
```

---

## Quick Reference Card

### One-Time Global Setup
```bash
cd /Users/jim/src/apps/ai_sdlc_method
python installers/setup_plugins.py --global --bundle startup
```

### For Each New Project
```bash
# 1. Create project
mkdir my-new-project && cd my-new-project
git init

# 2. Install tools
python /Users/jim/src/apps/ai_sdlc_method/installers/setup_all.py

# 3. Create intent and config
touch INTENT.md
mkdir config && touch config/config.yml

# 4. Start coding
/start-session
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

### Strategy 1: Reset Installation (Recommended)

**Use Case:** Clean update to a specific version, removes stale files, preserves your work

```bash
cd /path/to/your/project

# One-liner via curl (no clone needed) - updates to latest
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 -

# Or update to specific version
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --version v0.2.0

# Preview changes first (recommended)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --dry-run
```

**What gets PRESERVED** (your work):
- `.ai-workspace/tasks/active/` - Your current tasks
- `.ai-workspace/tasks/finished/` - Your task history

**What gets REPLACED** (framework code):
- `.claude/commands/` - All slash commands (clean, removes obsolete)
- `.claude/agents/` - All agent definitions (fresh from version)
- `.ai-workspace/templates/` - All templates (updated)
- `.ai-workspace/config/` - Configuration files

This is the recommended approach because it cleans up stale files (e.g., removed commands, renamed folders) that `--force` doesn't handle.

### Strategy 2: Force Overwrite (Quick but Leaves Stale Files)

**Use Case:** Quick update, but doesn't remove obsolete files

```bash
cd /path/to/your/project

# Backup current state
git commit -am "Checkpoint before AI SDLC refresh"

# Full refresh from latest
python /Users/jim/src/apps/ai_sdlc_method/installers/setup_all.py \
  --force \
  --with-plugins \
  --bundle startup

# Review changes
git diff

# If satisfied, commit
git add .
git commit -m "Update AI SDLC Method to latest version"
```

**Note**: This overwrites files but doesn't remove obsolete ones. Use reset installation for clean updates.

### Strategy 2: Selective Refresh

**Use Case:** Update specific components only

```bash
# Update only commands (useful after command changes)
python /Users/jim/src/apps/ai_sdlc_method/installers/setup_commands.py --force

# Update workspace templates
python /Users/jim/src/apps/ai_sdlc_method/installers/setup_workspace.py --force

# Update plugins
python /Users/jim/src/apps/ai_sdlc_method/installers/setup_plugins.py \
  --force \
  --bundle startup
```

### Strategy 3: Marketplace Updates (Plugins Only)

**Use Case:** Automatic plugin updates, but manual templates/commands

```bash
# Update plugins via marketplace
/plugin update @aisdlc/aisdlc-methodology
/plugin update @aisdlc/python-standards

# Manually refresh templates/commands when needed
python /Users/jim/src/apps/ai_sdlc_method/installers/setup_commands.py --force
```

### Strategy 4: Create Update Script

Create a project-specific refresh script:

```bash
# Create script
cat > .ai-workspace/scripts/refresh_aisdlc.sh <<'EOF'
#!/bin/bash
# Refresh AI SDLC Method from parent repository

AISDLC_ROOT="/Users/jim/src/apps/ai_sdlc_method"
PROJECT_ROOT="$(pwd)"

echo "🔄 Refreshing AI SDLC Method from: $AISDLC_ROOT"

# Backup
git commit -am "Checkpoint before AISDLC refresh" || true

# Refresh
python "$AISDLC_ROOT/installers/setup_all.py" \
  --target "$PROJECT_ROOT" \
  --force \
  --with-plugins \
  --bundle startup

echo "✅ Refresh complete! Review changes with: git diff"
EOF

chmod +x .ai-workspace/scripts/refresh_aisdlc.sh
```

**Usage:**
```bash
bash .ai-workspace/scripts/refresh_aisdlc.sh
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

### Option 1: Manual Tracking

Check for updates periodically:

```bash
# Navigate to AI SDLC Method repo
cd /Users/jim/src/apps/ai_sdlc_method

# Pull latest changes
git pull

# Review changes
git log --oneline -10

# If significant updates, refresh your projects
cd /path/to/your/project
python /Users/jim/src/apps/ai_sdlc_method/installers/setup_all.py --force
```

### Option 2: Automated Check (Cron Job)

Create a weekly check:

```bash
# Add to crontab
crontab -e

# Add line (runs every Monday at 9 AM):
0 9 * * 1 cd /Users/jim/src/apps/ai_sdlc_method && git pull && echo "AI SDLC updated" | mail -s "AI SDLC Update" your-email@example.com
```

### Option 3: CI/CD Integration

For team projects, add to CI/CD:

```bash
# .github/workflows/update-aisdlc.yml
name: Update AI SDLC Method
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Refresh AI SDLC
        run: |
          python /path/to/ai_sdlc_method/installers/setup_all.py --force
          git diff > aisdlc_changes.txt
      - name: Create PR if changes
        run: gh pr create --title "Update AI SDLC Method"
```

---

## Migration Guide

### From v1.0.0 to v2.0.0

**Breaking Changes:**
1. Slash commands renamed with `aisdlc-` prefix
2. Added 7-stage SDLC agent definitions
3. Updated config.yml schema

**Migration Steps:**

```bash
# 1. Backup your project
git commit -am "Pre-migration checkpoint"

# 2. Run installer with force flag
python /Users/jim/src/apps/ai_sdlc_method/installers/setup_all.py \
  --force \
  --with-plugins \
  --bundle startup

# 3. Update config.yml to use new schema
# (See ai_sdlc_examples repo for config.yml examples)

# 4. Update slash command references in documentation
# Old: /todo "task"
# New: /aisdlc-todo "task"

# 5. Test all commands
/aisdlc-status
/aisdlc-start-session

# 6. Commit migration
git add .
git commit -m "Migrate to AI SDLC Method v2.0.0"
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
