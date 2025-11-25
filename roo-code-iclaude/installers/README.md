# Roo Code AISDLC - Installers

Python-based installers for deploying the AI SDLC Method to Roo Code projects.

**Version**: 1.0.0

## Overview

This directory contains Python scripts that install the **AI SDLC development environment** for Roo Code into target projects. These installers provide:

- **Offline installation** - No network required (with local clone)
- **Enterprise environments** - Where external access may be restricted
- **CI/CD integration** - Automated project setup
- **Custom deployments** - Full control over installation
- **Version management** - Install specific versions, upgrade/downgrade

## What Gets Installed

```
target-project/
├── .roo/
│   ├── modes/                    # 7 SDLC stage custom modes
│   │   ├── aisdlc-requirements.json
│   │   ├── aisdlc-design.json
│   │   ├── aisdlc-tasks.json
│   │   ├── aisdlc-code.json
│   │   ├── aisdlc-system-test.json
│   │   ├── aisdlc-uat.json
│   │   └── aisdlc-runtime.json
│   ├── rules/                    # Methodology guidance
│   │   ├── key-principles.md
│   │   ├── tdd-workflow.md
│   │   ├── bdd-workflow.md
│   │   ├── req-tagging.md
│   │   ├── feedback-protocol.md
│   │   └── workspace-safeguards.md
│   └── memory-bank/              # Persistent project context
│       ├── projectbrief.md
│       ├── techstack.md
│       ├── activecontext.md
│       └── methodref.md
├── .ai-workspace/                # Task management (shared)
│   ├── tasks/
│   │   ├── active/ACTIVE_TASKS.md
│   │   └── finished/
│   ├── templates/
│   └── config/
├── ROOCODE.md                    # Project guidance
└── .gitignore                    # Updated with AISDLC entries
```

---

## Quick Start

### Method 1: Full Installation (Recommended)

```bash
cd /path/to/your/project

# Full installation
python /path/to/ai_sdlc_method/roo-code-iclaude/installers/setup_all.py

# Or with specific options
python setup_all.py --target /my/project --force
```

### Method 2: One-liner via curl (No Clone Needed)

```bash
# Latest version
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py | python3 -

# Specific version
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py | python3 - --version v0.3.0

# Dry run (preview)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py | python3 - --dry-run
```

---

## Available Installers

### `setup_all.py` - Complete Setup (Recommended)

Main orchestrator that installs everything.

**Usage:**
```bash
# Full installation
python setup_all.py

# Install to specific project
python setup_all.py --target /path/to/project

# Force overwrite existing
python setup_all.py --force

# Install only specific components
python setup_all.py --workspace-only
python setup_all.py --modes-only
python setup_all.py --rules-only
python setup_all.py --memory-bank-only

# Reset installation (clean slate)
python setup_all.py --reset
python setup_all.py --reset --version v0.3.0
```

**Options:**
| Option | Description |
|--------|-------------|
| `--target PATH` | Target directory (default: current) |
| `--force` | Overwrite existing files |
| `--reset` | Reset-style install (preserves tasks) |
| `--version TAG` | Version for reset install |
| `--workspace-only` | Install only .ai-workspace |
| `--modes-only` | Install only .roo/modes |
| `--rules-only` | Install only .roo/rules |
| `--memory-bank-only` | Install only .roo/memory-bank |
| `--no-git` | Don't update .gitignore |

---

### `setup_reset.py` - Reset Installation (Clean Updates)

Performs clean reset-style installation that addresses stale files from previous versions.

**Philosophy:** Only immutable framework code is replaced. User work is always preserved.

**PRESERVED (User Data):**
- `.ai-workspace/tasks/active/` - Your current active tasks
- `.ai-workspace/tasks/finished/` - Your completed task documentation
- `.roo/memory-bank/` - Your project context

**REMOVED & REINSTALLED (Framework):**
- `.roo/modes/` - All custom modes
- `.roo/rules/` - All rules
- `.ai-workspace/templates/` - All templates
- `.ai-workspace/config/` - Configuration

**Usage:**
```bash
# Reset to latest
python setup_reset.py

# Reset to specific version
python setup_reset.py --version v0.3.0

# Preview changes
python setup_reset.py --dry-run

# Use local source
python setup_reset.py --source /path/to/templates
```

---

### `aisdlc-reset.py` - Self-Contained Reset (curl-friendly)

Single-file installer that can be run directly via curl - no clone required.

**Usage:**
```bash
# Latest version
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py | python3 -

# Specific version
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py | python3 - --version v0.3.0

# Dry run
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py | python3 - --dry-run

# Or download and run locally
curl -O https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py
python3 aisdlc-reset.py --version v0.3.0
```

This is the **recommended method** for updating existing projects.

---

### `setup_modes.py` - Custom Modes

Installs AISDLC custom modes to `.roo/modes/`.

**Modes included:**
| Mode | Stage | Purpose |
|------|-------|---------|
| `aisdlc-requirements` | 1 | Transform intent into REQ-* keys |
| `aisdlc-design` | 2 | Technical architecture |
| `aisdlc-tasks` | 3 | Work breakdown |
| `aisdlc-code` | 4 | TDD implementation |
| `aisdlc-system-test` | 5 | BDD integration testing |
| `aisdlc-uat` | 6 | Business validation |
| `aisdlc-runtime` | 7 | Production feedback |

**Usage:**
```bash
python setup_modes.py
python setup_modes.py --target /my/project
python setup_modes.py --list  # List available modes
```

---

### `setup_rules.py` - Custom Rules

Installs AISDLC rules to `.roo/rules/`.

**Rules included:**
| Rule | Description |
|------|-------------|
| `key-principles.md` | The 7 Key Principles |
| `tdd-workflow.md` | RED → GREEN → REFACTOR |
| `bdd-workflow.md` | Given/When/Then |
| `req-tagging.md` | REQ-* key format |
| `feedback-protocol.md` | Stage feedback loops |
| `workspace-safeguards.md` | Safety rules |

**Usage:**
```bash
python setup_rules.py
python setup_rules.py --list  # List available rules
```

---

### `setup_memory_bank.py` - Memory Bank

Installs memory bank templates to `.roo/memory-bank/`.

**Templates included:**
| Template | Description |
|----------|-------------|
| `projectbrief.md` | Project overview and goals |
| `techstack.md` | Technology decisions |
| `activecontext.md` | Current work focus |
| `methodref.md` | AISDLC quick reference |

**Usage:**
```bash
python setup_memory_bank.py
python setup_memory_bank.py --list  # List templates

# Note: Memory bank files are user data
# Use --force carefully (will backup first)
python setup_memory_bank.py --force
```

---

### `setup_workspace.py` - Developer Workspace

Installs `.ai-workspace/` directory (shared across AI tools).

**Usage:**
```bash
python setup_workspace.py
python setup_workspace.py --force  # Backs up first
```

---

## Common Usage Patterns

### New Project Setup

```bash
cd /path/to/new/project
python /path/to/ai_sdlc_method/roo-code-iclaude/installers/setup_all.py

# Then open Roo Code and select an AISDLC mode
```

### Upgrade Existing Installation

```bash
cd /my/project

# Reset to latest (preserves tasks)
python /path/to/installers/setup_reset.py

# Or via curl
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py | python3 -
```

### Offline Installation

```bash
# Clone once (when online)
git clone https://github.com/foolishimp/ai_sdlc_method.git

# Install offline
cd /offline/project
python /path/to/ai_sdlc_method/roo-code-iclaude/installers/setup_all.py
```

### CI/CD Integration

```bash
#!/bin/bash
# setup-roo-aisdlc.sh

PROJECT_DIR="${1:-.}"
AI_SDLC_REPO="/tools/ai_sdlc_method"

python "${AI_SDLC_REPO}/roo-code-iclaude/installers/setup_all.py" \
  --target "${PROJECT_DIR}" \
  --force \
  --no-git

echo "Roo Code AISDLC installed for ${PROJECT_DIR}"
```

---

## Testing

Run the test suite:

```bash
cd roo-code-iclaude/installers
python -m pytest tests/ -v
```

Tests cover:
- `test_common.py` - Base installer utilities
- `test_setup_reset.py` - Reset installer functionality

---

## Troubleshooting

### "Templates not found"

```bash
# Ensure you're running from the correct location
cd /path/to/ai_sdlc_method/roo-code-iclaude/installers
python setup_all.py
```

### "Already exists" errors

```bash
# Use --force to overwrite
python setup_all.py --force
```

### Modes not showing in Roo Code

1. Restart Roo Code after installation
2. Check `.roo/modes/` directory exists
3. Verify JSON files are valid

### Permission errors

```bash
# Check directory permissions
ls -la .roo/
```

---

## Comparison: Claude vs Roo Code Installers

| Feature | Claude Code | Roo Code |
|---------|------------|----------|
| Config directory | `.claude/` | `.roo/` |
| Commands | `.claude/commands/*.md` | N/A (modes instead) |
| Agents | `.claude/agents/*.md` | `.roo/modes/*.json` |
| Rules | Inline in agents | `.roo/rules/*.md` |
| Memory | Implicit | `.roo/memory-bank/` |
| Guidance | `CLAUDE.md` | `ROOCODE.md` |
| Workspace | `.ai-workspace/` | `.ai-workspace/` (shared) |

---

## Support

- **Issues**: https://github.com/foolishimp/ai_sdlc_method/issues
- **Documentation**: See `docs/design/roo_aisdlc/`
- **Examples**: https://github.com/foolishimp/ai_sdlc_examples

---

*"Excellence or nothing"* 🔥
