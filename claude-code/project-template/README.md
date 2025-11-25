# Claude Code Project Template

This directory contains the **project template** that users copy to their own projects to set up the AI SDLC methodology.

---

## What's Included

This template provides the complete workspace structure for Claude Code projects using AI SDLC:

```
project-template/
├── .claude/
│   ├── agents/                    # 7 SDLC stage agents
│   │   ├── aisdlc-requirements-agent.md
│   │   ├── aisdlc-design-agent.md
│   │   ├── aisdlc-tasks-agent.md
│   │   ├── aisdlc-code-agent.md
│   │   ├── aisdlc-system-test-agent.md
│   │   ├── aisdlc-uat-agent.md
│   │   └── aisdlc-runtime-feedback-agent.md
│   ├── commands/                  # 6 workflow commands
│   │   ├── aisdlc-checkpoint-tasks.md
│   │   ├── aisdlc-finish-task.md
│   │   ├── aisdlc-commit-task.md
│   │   ├── aisdlc-status.md
│   │   ├── aisdlc-release.md
│   │   └── aisdlc-refresh-context.md
│   ├── hooks.json                 # Git hooks for automation
│   └── settings.local.json        # Claude Code settings
│
├── .ai-workspace/
│   ├── tasks/
│   │   ├── active/                # Current work
│   │   │   └── ACTIVE_TASKS.md
│   │   └── finished/              # Completed tasks
│   ├── templates/                 # Method reference templates
│   │   ├── AISDLC_METHOD_REFERENCE.md
│   │   ├── TASK_TEMPLATE.md
│   │   └── deprecated/
│   └── config/
│       └── workspace_config.yml   # Workspace configuration
│
├── CLAUDE.md.template             # Project guidance for Claude
│
├── docs/                          # Placeholder directories
├── requirements/
├── src/
└── tests/
```

---

## Purpose: Initialize User Projects

This template is **copied to user projects** to set up the AI SDLC workspace:

1. **User creates new project** → Copy template
2. **Customize for project** → Update CLAUDE.md, config
3. **Start development** → Use agents and commands

**This is NOT installed via marketplace** - it's a one-time copy that users customize.

---

## How to Use

### Option 1: Manual Copy

```bash
# Copy to your project
cd /path/to/your-project
cp -r /path/to/ai_sdlc_method/claude-code/project-template/.claude ./
cp -r /path/to/ai_sdlc_method/claude-code/project-template/.ai-workspace ./
cp /path/to/ai_sdlc_method/claude-code/project-template/CLAUDE.md.template ./CLAUDE.md

# Customize CLAUDE.md for your project
vim CLAUDE.md
```

### Option 2: Use Installer

```bash
# From ai_sdlc_method directory
python installers/setup_workspace.py /path/to/your-project

# This copies template and prompts for customization
```

---

## What's Inside

### .claude/agents/ (7 SDLC Stage Agents)

Each agent file is a **Claude Code agent** that guides Claude through a specific SDLC stage:

1. **Requirements Agent** - Transform intent → structured requirements (REQ-*)
2. **Design Agent** - Requirements → technical solution architecture
3. **Tasks Agent** - Break design into work units
4. **Code Agent** - TDD implementation (RED → GREEN → REFACTOR)
5. **System Test Agent** - BDD integration tests (Given/When/Then)
6. **UAT Agent** - Business validation and sign-off
7. **Runtime Feedback Agent** - Production telemetry → feedback loop

**Usage**: Reference agent files to guide Claude's behavior at each stage

### .claude/commands/ (6 Workflow Commands)

**Slash commands** that integrate AI SDLC workflow into Claude Code:

- `/aisdlc-checkpoint-tasks` - Save task state
- `/aisdlc-finish-task` - Complete and archive task
- `/aisdlc-commit-task` - Git commit with REQ-* traceability
- `/aisdlc-status` - Show task queue status
- `/aisdlc-release` - Create release with traceability
- `/aisdlc-refresh-context` - Reload workspace context

**Usage**: Type slash commands in Claude Code to execute workflows

### .ai-workspace/ (Task & Session Management)

**File-based workspace** for persistent context:

- `tasks/active/ACTIVE_TASKS.md` - Current work (one file, everything here)
- `tasks/finished/` - Completed task documentation
- `templates/` - Method reference and templates
- `config/` - Workspace configuration

**Usage**: Claude reads/writes these files to maintain context across sessions

### CLAUDE.md.template (Project Guidance)

**Template for project-specific guidance** to Claude Code:

```markdown
# CLAUDE.md - My Project Guide

## Project Overview
...

## Development Guidelines
...

## AI SDLC Methodology
This project uses AI SDLC methodology from ai_sdlc_method
...
```

**Usage**: Copy to `CLAUDE.md`, customize for your project

---

## Key Concepts

### Agents vs Commands vs Skills

| Asset | Purpose | Where | Invoked By |
|-------|---------|-------|------------|
| **Agents** | SDLC stage persona | `.claude/agents/` | Reading agent file |
| **Commands** | Workflow shortcuts | `.claude/commands/` | Slash command (e.g., `/aisdlc-status`) |
| **Skills** | Reusable capabilities | Plugins | Agents invoke skills |

### Implicit Session Model

**No explicit session start needed**:

1. **Open Claude Code** → CLAUDE.md auto-loads
2. **Work on tasks** → Update ACTIVE_TASKS.md
3. **Checkpoint** → `/aisdlc-checkpoint-tasks` saves state
4. **Close** → Context persists in ACTIVE_TASKS.md

**Simple**: One file (ACTIVE_TASKS.md) + conversation history = your session

---

## Customization

After copying the template, customize these files:

### 1. CLAUDE.md

Update with your project specifics:
- Project name and description
- Development guidelines
- Tech stack
- Dependencies

### 2. .ai-workspace/config/workspace_config.yml

Configure workspace settings:
- Task management preferences
- Methodology stage enablement
- Context loading behavior

### 3. .claude/settings.local.json

Claude Code settings (optional):
- Plugin loading
- Marketplace configuration
- Hooks configuration

---

## Difference from Plugins

| Template | Plugins |
|----------|---------|
| **One-time copy** | **Installed from marketplace** |
| User customizes after copy | Updates pulled from marketplace |
| Project-specific workspace | Shared methodology/standards |
| `.claude/`, `.ai-workspace/` | `node_modules/.claude-plugins/` |
| User owns the files | Marketplace owns, user references |

**Analogy**:
- **Template** = Project scaffolding (like `create-react-app` template)
- **Plugins** = Shared libraries (like npm packages)

---

## Related

- **Plugins**: [../plugins/README.md](../plugins/README.md) - Methodology plugins
- **Parent Directory**: [../README.md](../README.md) - Claude Code assets overview
- **Installers**: [../../installers/](../../installers/) - Setup scripts
- **Examples**: [ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples) - Complete example projects (separate repo)

---

## Getting Started

1. **Copy this template** to your project (manually or via installer)
2. **Customize** CLAUDE.md and config files
3. **Install plugins** via Claude Code marketplace
4. **Start development** using agents and commands

See [../../QUICKSTART.md](../../QUICKSTART.md) for step-by-step setup.

---

**"Excellence or nothing"** 🔥
