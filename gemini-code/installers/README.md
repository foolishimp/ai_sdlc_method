# AI SDLC Method - Installers

Python-based installers for deploying the AI SDLC Method to any project.

**Version**: 3.0.0

## Overview

This directory contains Python scripts that install the **AI SDLC development environment** into target projects.

## What Gets Installed

- ✅ `.ai-workspace/` - Task management with AI SDLC workflow
- ✅ `.gemini/commands/` - Custom commands
- ✅ `.gemini/agents/` - 7-stage AI agent specifications
- ✅ `gemini-code/plugins/` (optional) - Gemini Code plugins
- ✅ `GEMINI.md` - Project guidance template

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

### `setup_workspace.py` - Developer Workspace

Installs the `.ai-workspace/` directory with task management and session tracking.

### `setup_commands.py` - Gemini Commands

Installs the `.gemini/commands/` directory with custom commands.

### `setup_plugins.py` - Plugin Installer

Installs AI SDLC plugins directly.

---
## Common Usage Patterns

### Quick Start - New Project
```bash
cd /path/to/new/project

# Install workspace and commands with startup bundle
python /path/to/ai_sdlc_method/installers/setup_all.py \
  --with-plugins --bundle startup
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

## Template Source

All installers copy from `gemini-code/project-template/`:
- `.ai-workspace/` - Workspace template
- `.gemini/` - Commands template
- `GEMINI.md.template` - Project guidance template

Plugins are copied from `gemini-code/plugins/` directory.