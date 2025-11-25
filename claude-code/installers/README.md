# AI SDLC Method - Installers

Python-based installers for deploying the AI SDLC Method to any project.

**Version**: 3.0.0

## Overview

This directory contains Python scripts that install the **AI SDLC development environment** (with homeostatic control) into target projects. These installers provide an **alternative to the Claude marketplace**, useful for:

- **Offline installation** - No network required
- **Enterprise environments** - Where marketplace access may be restricted
- **CI/CD integration** - Automated project setup
- **Custom deployments** - Full control over installation
- **Dogfooding** - Installing into ai_sdlc_method itself for development

## What Gets Installed

- ✅ `.ai-workspace/` - Task management with AI SDLC workflow
- ✅ `.claude/commands/` - Slash commands (/aisdlc-start-session, /aisdlc-checkpoint-tasks, etc.)
- ✅ `.claude/agents/` - 7-stage AI agent specifications
- ✅ `claude-code/claude-code/plugins/` (optional) - Claude Code plugins with homeostatic control
- ✅ `CLAUDE.md` - Project guidance template

## Installation Methods

### Method 1: Python Installers (This Directory)
Direct installation via Python scripts - works offline, fully customizable.

### Method 2: Claude Marketplace (Recommended)
```bash
/plugin marketplace add foolishimp/ai_sdlc_method
/plugin install @aisdlc/startup-bundle
```

---

## Available Installers

### `setup_all.py` - Complete Setup (Recommended)

Main orchestrator that installs everything.

**Usage:**
```bash
# Full installation (workspace + commands, no plugins)
python setup_all.py

# Full installation with startup bundle
python setup_all.py --with-plugins --bundle startup

# Install to specific project
python setup_all.py --target /path/to/project --with-plugins --bundle enterprise

# Force reinstall everything
python setup_all.py --force --with-plugins --plugin-list all
```

**Options:**
- `--target PATH` - Target directory (default: current)
- `--force` - Overwrite existing files
- `--reset` - Reset-style install (clean slate, see below)
- `--version TAG` - Version tag for reset install (default: latest)
- `--workspace-only` - Install only .ai-workspace
- `--commands-only` - Install only .claude/commands
- `--plugins-only` - Install only plugins
- `--with-plugins` - Include plugins in installation
- `--plugin-list LIST` - Comma-separated plugin names or 'all'
- `--bundle BUNDLE` - Install bundle (startup|datascience|qa|enterprise)
- `--global-plugins` - Install plugins globally
- `--no-git` - Don't update .gitignore

---

### `setup_reset.py` - Reset Installation (Clean Updates)

Performs a clean reset-style installation that addresses stale files from previous versions.

**Philosophy:** Only immutable framework code (commands, agents, templates) is replaced.
User work (tasks) is always preserved and can roll forward/backward with versions.

**What gets PRESERVED:**
- `.ai-workspace/tasks/active/` - Your current active tasks
- `.ai-workspace/tasks/finished/` - Your completed task documentation

**What gets REMOVED and reinstalled:**
- `.claude/commands/` - All commands (fresh from version)
- `.claude/agents/` - All agent specs (fresh from version)
- `.ai-workspace/templates/` - All templates (fresh from version)
- `.ai-workspace/config/` - Configuration files (fresh from version)

**Usage:**
```bash
# Reset to latest release (from GitHub)
python setup_reset.py

# Reset to specific version
python setup_reset.py --version v0.2.0

# Preview changes without executing
python setup_reset.py --dry-run

# Use local source (for development)
python setup_reset.py --source /path/to/ai_sdlc_method

# Reset specific project
python setup_reset.py --target /my/project
```

**Options:**
- `--target PATH` - Target directory (default: current)
- `--version TAG` - Version tag to install (default: latest release)
- `--source PATH` - Use local source instead of GitHub
- `--dry-run` - Show plan without making changes
- `--no-backup` - Skip backup creation (not recommended)
- `--no-git` - Don't update .gitignore

**Via setup_all.py:**
```bash
# Reset using main orchestrator
python setup_all.py --reset

# Reset to specific version
python setup_all.py --reset --version v0.2.0
```

**When to use reset:**
- After upgrading to a new version
- When old commands/folders persist that should be removed
- When you want a clean slate without losing your tasks
- When rolling back to a previous version

---

### `aisdlc-reset.py` - Self-Contained Reset (curl-friendly)

A single-file installer that can be run directly via curl - no clone required.

**Usage:**
```bash
# Latest version
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 -

# Specific version
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --version v0.2.0

# Dry run
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --dry-run

# Or download and run locally
curl -O https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py
python3 aisdlc-reset.py --version v0.2.0
```

**Options:**
- `--target PATH` - Target directory (default: current)
- `--version TAG` - Version tag to install (default: latest)
- `--dry-run` - Show plan without executing
- `--no-backup` - Skip backup creation

This is the **recommended method** for updating existing projects since it requires no local clone of the ai_sdlc_method repository.

---

### `setup_workspace.py` - Developer Workspace

Installs `.ai-workspace/` directory with task management and session tracking.

**What it installs:**
- Task management (todo, active, finished, archive)
- Session tracking and templates
- Pair programming guides
- Workspace configuration

**Usage:**
```bash
# Install in current directory
python setup_workspace.py

# Install in specific directory
python setup_workspace.py --target /my/project

# Force overwrite
python setup_workspace.py --force
```

**Options:**
- `--target PATH` - Installation directory
- `--force` - Overwrite existing workspace
- `--no-git` - Skip .gitignore updates

---

### `setup_commands.py` - Claude Commands

Installs `.claude/commands/` directory with slash commands.

**Commands included:**
- `/todo` - Quick task capture
- `/start-session` - Begin development session
- `/finish-task` - Complete task with docs
- `/commit-task` - Generate commit message
- `/apply-persona` - Apply development persona
- `/switch-context` - Switch project context
- And more...

**Usage:**
```bash
# Install in current directory
python setup_commands.py

# Install in specific directory
python setup_commands.py --target /my/project

# Force overwrite
python setup_commands.py --force
```

**Options:**
- `--target PATH` - Installation directory
- `--force` - Overwrite existing commands
- `--no-git` - Skip .gitignore updates

---

### `setup_plugins.py` - Plugin Installer

Installs AI SDLC plugins directly (alternative to marketplace).

**Available Plugins:**

**Core:**
- `aisdlc-core` - Core methodology
- `aisdlc-methodology` - Complete 7-stage SDLC

**Skills:**
- `testing-skills` - Testing patterns
- `code-skills` - Code quality
- `design-skills` - Architecture patterns
- `requirements-skills` - Requirements engineering
- `runtime-skills` - Deployment & monitoring

**Standards:**
- `python-standards` - Python best practices
- `principles-key` - Core principles

**Bundles:**
- `startup` - Essential plugins (aisdlc-core, aisdlc-methodology, principles-key)
- `datascience` - ML/Data science focus
- `qa` - Quality assurance focus
- `enterprise` - Full suite

**Usage:**
```bash
# List available plugins and bundles
python setup_plugins.py --list

# Install startup bundle globally
python setup_plugins.py --global --bundle startup

# Install specific plugins to project
python setup_plugins.py --plugins aisdlc-core,testing-skills

# Install all plugins globally
python setup_plugins.py --global --all

# Install to specific project
python setup_plugins.py --target /my/project --bundle enterprise
```

**Options:**
- `--target PATH` - Project directory
- `--global` - Install to `~/.config/claude/claude-code/claude-code/plugins/`
- `--plugins LIST` - Comma-separated plugin names
- `--bundle NAME` - Install bundle
- `--all` - Install all plugins
- `--list` - List available plugins
- `--force` - Overwrite existing

---

## Common Usage Patterns

### Quick Start - New Project

```bash
cd /path/to/new/project

# Install workspace and commands with startup bundle
python /path/to/ai_sdlc_method/installers/setup_all.py \
  --with-plugins --bundle startup

# Start development
/start-session
```

### Minimal Installation

```bash
# Just workspace and commands (no plugins)
python setup_all.py

# Use marketplace for plugins later
/plugin marketplace add foolishimp/ai_sdlc_method
```

### Enterprise Setup

```bash
# Full installation with enterprise bundle
python setup_all.py \
  --target /corporate/project \
  --with-plugins \
  --bundle enterprise \
  --force

# Verify
ls -la .ai-workspace
ls -la .claude/commands
ls -la .claude/plugins
```

### Data Science Project

```bash
# Install datascience bundle
python setup_all.py \
  --with-plugins \
  --bundle datascience
```

### QA/Testing Project

```bash
# Install qa bundle
python setup_all.py \
  --with-plugins \
  --bundle qa
```

### Global Plugins (User-Wide)

```bash
# Install plugins once for all projects
python setup_plugins.py \
  --global \
  --bundle enterprise

# Then just install workspace/commands per project
cd /my/project
python setup_all.py --workspace-only
python setup_all.py --commands-only
```

### Reset Installation (Upgrade/Downgrade)

**One-liner via curl (no clone needed):**
```bash
cd /my/project

# Reset to latest release
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 -

# Reset to specific version
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --version v0.2.0

# Dry run (preview changes)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --dry-run
```

**Or with local clone:**
```bash
python /path/to/ai_sdlc_method/installers/setup_reset.py --version v0.2.0
python /path/to/ai_sdlc_method/installers/setup_all.py --reset

# Your tasks are preserved in:
# - .ai-workspace/tasks/active/
# - .ai-workspace/tasks/finished/
```

### Offline Installation

```bash
# Clone ai_sdlc_method once (when online)
git clone https://github.com/foolishimp/ai_sdlc_method.git

# Later, install offline (no network needed)
cd /offline/project
python /path/to/ai_sdlc_method/installers/setup_all.py \
  --with-plugins --all
```

### CI/CD Integration

```bash
#!/bin/bash
# setup-ai-sdlc.sh - Add to your CI/CD pipeline

PROJECT_DIR="${1:-.}"
AI_SDLC_REPO="/tools/ai_sdlc_method"

python "${AI_SDLC_REPO}/installers/setup_all.py" \
  --target "${PROJECT_DIR}" \
  --with-plugins \
  --bundle startup \
  --force \
  --no-git

echo "AI SDLC Method installed for ${PROJECT_DIR}"
```

---

## What Gets Installed

### Workspace Installation

Creates `.ai-workspace/` with:
```
.ai-workspace/
├── config/
│   └── workspace_config.yml        # Configuration
├── tasks/
│   ├── todo/
│   │   └── TODO_LIST.md            # Quick capture
│   ├── active/
│   │   └── ACTIVE_TASKS.md         # Formal tasks
│   ├── finished/                   # Completed docs
│   └── archive/                    # Old tasks
├── session/
│   ├── current_session.md          # Active session
│   └── history/                    # Past sessions
└── templates/
    ├── TASK_TEMPLATE.md
    ├── FINISHED_TASK_TEMPLATE.md
    ├── SESSION_TEMPLATE.md
    └── PAIR_PROGRAMMING_GUIDE.md
```

### Commands Installation

Creates `.claude/commands/` with:
```
.claude/
└── commands/
    ├── todo.md
    ├── start-session.md
    ├── finish-task.md
    ├── commit-task.md
    ├── apply-persona.md
    ├── switch-context.md
    ├── load-context.md
    ├── current-context.md
    └── ... (more commands)
```

### Plugins Installation

Creates `.claude/claude-code/claude-code/plugins/` (project) or `~/.config/claude/claude-code/claude-code/plugins/` (global) with:
```
claude-code/claude-code/plugins/
├── aisdlc-core/
├── aisdlc-methodology/
├── testing-skills/
├── code-skills/
└── ... (based on selection)
```

### CLAUDE.md

Creates `CLAUDE.md` project guidance file with:
- Quick start instructions
- Available commands
- Development workflow
- Key principles
- Resources and links

---

## Template Source

All installers copy from `claude-code/project-template/`:
- `.ai-workspace/` - Workspace template
- `.claude/` - Commands template
- `CLAUDE.md.template` - Project guidance template

Plugins are copied from `claude-code/claude-code/plugins/` directory.

---

## Troubleshooting

### "Templates not found"
```bash
# Ensure you're running from ai_sdlc_method/installers/
cd /path/to/ai_sdlc_method/installers
python setup_all.py
```

### "Already exists" errors
```bash
# Use --force to overwrite
python setup_all.py --force
```

### Plugins not showing up
```bash
# Restart Claude Code after plugin installation
# Or check plugin location:
ls ~/.config/claude/claude-code/claude-code/plugins/        # Global
ls ./.claude/claude-code/claude-code/plugins/               # Project
```

### Permission errors
```bash
# For global installation, ensure directory exists
mkdir -p ~/.config/claude/plugins

# Or install project-local instead
python setup_plugins.py --target . --bundle startup
```

---

## Advanced Usage

### Custom Plugin Selection

```bash
# Install only specific plugins you need
python setup_all.py --with-plugins \
  --plugin-list "aisdlc-core,testing-skills,python-standards"
```

### Selective Component Installation

```bash
# Install workspace first
python setup_workspace.py --target /my/project

# Test it out, then add commands
python setup_commands.py --target /my/project

# Later, add plugins
python setup_plugins.py --target /my/project --bundle startup
```

### Multi-Project Setup

```bash
# Install plugins globally once
python setup_plugins.py --global --all

# Then lightweight install per project
for project in /projects/*; do
  python setup_all.py --target "$project"
done
```

---

## Comparison: Installers vs Marketplace

| Feature | Python Installers | Claude Marketplace |
|---------|------------------|-------------------|
| **Offline** | ✅ Yes | ❌ No |
| **Enterprise** | ✅ Works anywhere | May be blocked |
| **CI/CD** | ✅ Scriptable | Difficult |
| **Customization** | ✅ Full control | Limited |
| **Updates** | Manual | ✅ Automatic |
| **Ease of use** | Requires Python | ✅ Very easy |
| **Dependencies** | Explicit | Handled |

**Recommendation:**
- **Development**: Use marketplace for ease
- **Enterprise/Offline**: Use Python installers
- **CI/CD**: Use Python installers

---

## Support

- **Issues**: https://github.com/foolishimp/ai_sdlc_method/issues
- **Documentation**: [../docs/](../docs/)
- **Examples**: [ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples) (separate repo)

---

## Version

**AI SDLC Method**: 1.0
**Installers**: 1.0

---

*"Excellence or nothing"* 🔥
