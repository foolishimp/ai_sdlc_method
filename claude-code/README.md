# Claude Code Assets

This directory contains all Claude Code specific assets for the AI SDLC methodology.

---

## Directory Structure

```
claude-code/
├── plugins/               # Marketplace plugins (distributed via marketplace)
│   ├── aisdlc-core/
│   ├── aisdlc-methodology/
│   ├── code-skills/
│   ├── design-skills/
│   ├── principles-key/
│   ├── python-standards/
│   ├── requirements-skills/
│   ├── runtime-skills/
│   ├── testing-skills/
│   └── bundles/           # Pre-configured plugin bundles
│       ├── startup-bundle/
│       ├── datascience-bundle/
│       ├── qa-bundle/
│       └── enterprise-bundle/
│
└── project-template/      # Template for user projects (copied to new projects)
    ├── .claude/
    │   ├── agents/        # 7 SDLC stage agents
    │   ├── commands/      # 6 workflow commands
    │   ├── hooks.json     # Git hooks
    │   └── settings.local.json
    └── .ai-workspace/
        ├── tasks/         # Task management
        ├── templates/     # Method reference
        └── config/        # Workspace config
```

---

## Two Types of Assets

### 1. Plugins (Marketplace Distribution)

**Location**: `claude-code/plugins/`

**Purpose**: Distributed via Claude Code marketplace for installation into user projects

**Usage**:
```bash
# Add marketplace
/plugin marketplace add foolishimp/ai_sdlc_method

# Install plugins
/plugin install @aisdlc/aisdlc-methodology
/plugin install @aisdlc/python-standards
```

**What's Inside**:
- **9 plugins** - Foundation, methodology, and skills layers
- **4 bundles** - Pre-configured combinations (startup, datascience, qa, enterprise)
- **41 skills** - Reusable capabilities across all SDLC stages

**Documentation**: See [plugins/README.md](plugins/README.md)

---

### 2. Project Template (User Setup)

**Location**: `claude-code/project-template/`

**Purpose**: Template structure that users copy to their projects

**Usage**:
```bash
# Copy template to new project
cp -r claude-code/project-template/.claude /path/to/my-project/
cp -r claude-code/project-template/.ai-workspace /path/to/my-project/

# Or use installer
python installers/setup_workspace.py /path/to/my-project
```

**What's Inside**:
- `.claude/agents/` - 7 SDLC stage agent specifications
- `.claude/commands/` - 6 workflow slash commands
- `.ai-workspace/` - Task management and workspace structure
- `CLAUDE.md.template` - Project guidance template
- `README.md` - Setup instructions

**Documentation**: See [project-template/README.md](project-template/README.md)

---

## Why This Structure?

### Problem (Before)

```
ai_sdlc_method/
├── plugins/                    # Claude Code plugins (not obvious)
└── templates/
    └── claude/                 # Claude Code template (obvious)
```

**Confusion**:
- ❌ `plugins/` doesn't indicate "Claude Code plugins"
- ❌ Relationship between plugins (source) and template (destination) unclear
- ❌ Both are Claude Code specific but structure doesn't show this

### Solution (After)

```
ai_sdlc_method/
└── claude-code/
    ├── plugins/               # Marketplace distribution
    └── project-template/      # User setup
```

**Clarity**:
- ✅ All Claude Code assets grouped under `claude-code/`
- ✅ Clear intent: `plugins/` = marketplace source, `project-template/` = user destination
- ✅ Single top-level directory for all Claude Code specifics
- ✅ README explains purpose at each level

---

## Key Concepts

### Plugins vs Template

| Aspect | Plugins | Project Template |
|--------|---------|------------------|
| **Location** | `claude-code/plugins/` | `claude-code/project-template/` |
| **Purpose** | Distribute methodology via marketplace | Initialize user projects |
| **Distribution** | Claude Code marketplace | Copy to user project |
| **Updates** | Pull new versions from marketplace | One-time copy, user customizes |
| **Examples** | aisdlc-methodology, python-standards | .claude/, .ai-workspace/ |

### Federated Architecture

Plugins support organizational hierarchy:

```
Corporate Marketplace → Division Marketplace → Team Marketplace → Project Config
```

Later plugins override earlier ones, enabling customization while maintaining standards.

---

## Documentation

- **Plugin System**: [plugins/README.md](plugins/README.md)
- **Project Template**: [project-template/README.md](project-template/README.md)
- **Complete Methodology**: [../docs/ai_sdlc_method.md](../docs/ai_sdlc_method.md)
- **Quick Start**: [../QUICKSTART.md](../QUICKSTART.md)

---

## Related

- **Marketplace Registry**: [../marketplace.json](../marketplace.json) - Plugin definitions
- **Installers**: [../installers/](../installers/) - Installation scripts
- **Examples**: [ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples) - Complete example projects (separate repo)
- **Design Docs**: [../docs/design/](../docs/design/) - Architecture documentation

---

**"Excellence or nothing"** 🔥
