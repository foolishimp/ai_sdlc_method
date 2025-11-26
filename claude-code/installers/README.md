# AI SDLC Method - Plugin Configuration

Configure Claude Code to load AI SDLC plugins via `settings.json`.

**Version**: 3.0.0

## Overview

Plugins are deployed via `settings.json` configuration - no file copying required. Claude Code discovers and loads plugins directly from configured marketplace sources (GitHub, local directory, or git URL).

This directory contains:
- `setup_settings.py` - Configure `.claude/settings.json` with AISDLC plugins
- `common.py` - Shared utilities
- `validate_traceability.py` - Validate requirement traceability

## Quick Start

```bash
# Clone the repo
git clone https://github.com/foolishimp/ai_sdlc_method.git ~/ai_sdlc_method

# Configure your project with GitHub source (recommended)
python ~/ai_sdlc_method/claude-code/installers/setup_settings.py --target /your/project --source github

# Or with all plugins
python ~/ai_sdlc_method/claude-code/installers/setup_settings.py --target /your/project --source github --all

# Preview changes without writing
python ~/ai_sdlc_method/claude-code/installers/setup_settings.py --target /your/project --dry-run
```

## setup_settings.py

Creates or updates `.claude/settings.json` with AISDLC plugin configuration.

### Source Types

**GitHub (Recommended)**
```bash
python setup_settings.py --source github
```
Plugins load directly from GitHub - always up to date.

**Local Directory (Development)**
```bash
python setup_settings.py --source directory --local-path ~/ai_sdlc_method/claude-code/plugins
```
For offline development or testing local changes.

**Git URL (Self-Hosted)**
```bash
python setup_settings.py --source git --git-url https://git.company.com/team/ai_sdlc_method.git
```
For private/enterprise git repositories.

### Plugin Selection

```bash
# Startup bundle (default)
python setup_settings.py --source github

# Specific bundle
python setup_settings.py --source github --bundle enterprise

# All plugins
python setup_settings.py --source github --all

# Specific plugins
python setup_settings.py --source github --plugins aisdlc-core,testing-skills
```

### Options

| Option | Description |
|--------|-------------|
| `--target PATH` | Target project directory (default: current) |
| `--source TYPE` | Source type: github, directory, git |
| `--local-path PATH` | Path for directory source |
| `--git-url URL` | URL for git source |
| `--plugins LIST` | Comma-separated plugins to enable |
| `--bundle NAME` | Plugin bundle: startup, datascience, qa, enterprise |
| `--all` | Enable all available plugins |
| `--dry-run` | Preview changes without writing |
| `--force` | Overwrite existing AISDLC configuration |

## Available Plugins

| Plugin | Description |
|--------|-------------|
| **aisdlc-core** | Foundation - requirement traceability with REQ-* keys |
| **aisdlc-methodology** | Complete 7-stage SDLC (commands, agents, templates) |
| **principles-key** | Key Principles enforcement (TDD, Fail Fast, etc.) |
| **code-skills** | TDD/BDD code generation skills |
| **testing-skills** | Test coverage validation |
| **requirements-skills** | Intent to requirements transformation |
| **design-skills** | Architecture and ADR generation |
| **runtime-skills** | Production feedback loop |
| **python-standards** | Python language standards |

## Plugin Bundles

| Bundle | Plugins | Use Case |
|--------|---------|----------|
| **startup** | aisdlc-core, aisdlc-methodology, principles-key | Getting started |
| **datascience** | aisdlc-core, testing-skills, python-standards, runtime-skills | Data science |
| **qa** | testing-skills, code-skills, requirements-skills, runtime-skills | QA focus |
| **enterprise** | All 9 plugins | Complete SDLC |

## What Gets Configured

Running `setup_settings.py` creates/updates `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "aisdlc": {
      "source": {
        "source": "github",
        "repo": "foolishimp/ai_sdlc_method",
        "path": "claude-code/plugins"
      }
    }
  },
  "enabledPlugins": {
    "aisdlc-core@aisdlc": true,
    "aisdlc-methodology@aisdlc": true,
    "principles-key@aisdlc": true
  }
}
```

Existing settings are preserved - only AISDLC configuration is added/updated.

## Workspace Setup (Optional)

If you want the `.ai-workspace/` task management structure, create it manually:

```bash
mkdir -p .ai-workspace/tasks/active .ai-workspace/tasks/finished
touch .ai-workspace/tasks/active/ACTIVE_TASKS.md
```

## Updating Plugins

**GitHub source**: Plugins update automatically when you restart Claude Code.

**Local directory source**:
```bash
cd ~/ai_sdlc_method
git pull origin main
# Restart Claude Code
```

## Examples

### New Project Setup

```bash
mkdir my-project && cd my-project
git init
python ~/ai_sdlc_method/claude-code/installers/setup_settings.py --source github
# Restart Claude Code to load plugins
```

### Adding to Existing Project

```bash
cd /path/to/existing/project
python ~/ai_sdlc_method/claude-code/installers/setup_settings.py --source github --force
# Restart Claude Code to load plugins
```

### Enterprise Setup

```bash
python setup_settings.py --target /corporate/project --source github --bundle enterprise
```

### Offline/Development Setup

```bash
# Clone once
git clone https://github.com/foolishimp/ai_sdlc_method.git ~/ai_sdlc_method

# Configure projects with local source
python ~/ai_sdlc_method/claude-code/installers/setup_settings.py --source directory
```

## Troubleshooting

### Plugins not loading

1. Run `/plugin` to see plugin status and specific errors
2. Restart Claude Code after configuring settings.json
3. Check settings.json syntax is valid JSON
4. Verify plugin names match exactly

### Common Errors

**"Marketplace file not found"**
- Ensure `.claude-plugin/marketplace.json` exists at marketplace root
- Plugin `source` paths in marketplace.json must start with `./`

**"Invalid manifest file"**
- `author` must be an object `{"name": "..."}`, not a string
- `agents` must be an array of `.md` file paths, not a directory
- Remove invalid fields: `displayName`, `capabilities`, `configuration`

### Verifying Installation

Run `/plugin` to check status:

```
/plugin

# Expected output:
Marketplaces:
  ✔ aisdlc · Installed

Plugins:
  ✔ aisdlc-core · Installed
  ✔ aisdlc-methodology · Installed
  ✔ principles-key · Installed
```

### Permission errors

Ensure `.claude/` directory is writable:
```bash
mkdir -p .claude
```

### Conflicting settings

Use `--force` to overwrite existing AISDLC configuration:
```bash
python setup_settings.py --source github --force
```

## Support

- **Issues**: https://github.com/foolishimp/ai_sdlc_method/issues
- **Documentation**: [../docs/](../docs/)
- **Examples**: [ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples)

---

*"Excellence or nothing"* 🔥
