# Claude Code Assets

This directory contains all Claude Code specific assets for the AI SDLC methodology.

---

## Directory Structure (v3.0.0)

```
claude-code/
├── plugins/                   # All plugins (including commands, agents, templates)
│   ├── aisdlc-methodology/    # Master plugin with all features
│   │   ├── .claude-plugin/    # Plugin manifest
│   │   ├── commands/          # 7 slash commands
│   │   ├── agents/            # 7 stage persona agents
│   │   ├── templates/         # Workspace scaffolding (.ai-workspace)
│   │   ├── config/            # Stage specifications
│   │   └── docs/              # Principles and processes
│   ├── aisdlc-core/           # Foundation (traceability, REQ keys)
│   ├── code-skills/           # TDD/BDD/generation skills
│   ├── design-skills/         # ADR and design skills
│   ├── principles-key/        # Key Principles principles
│   ├── python-standards/      # Python language standards
│   ├── requirements-skills/   # Requirement extraction skills
│   ├── runtime-skills/        # Observability skills
│   ├── testing-skills/        # Test coverage skills
│   └── bundles/               # Pre-configured plugin bundles
│
├── installers/                # Installation utilities
│   ├── setup_settings.py      # Configure settings.json
│   ├── common.py              # Shared utilities
│   └── validate_traceability.py  # Traceability validation
│
└── guides/                    # Getting started guides
    └── JOURNEY.md             # Complete installation journey
```

---

## Unified Plugin Architecture (ADR-006)

**Key Insight**: Plugins are the unified container for ALL Claude Code extensibility features.

| Feature | Location in Plugin | Role |
|---------|-------------------|------|
| **Commands** | `commands/` | User-invoked custom slash commands |
| **Agents** | `agents/` | Task-specific autonomous subagents |
| **Skills** | `skills/` | Model-driven capability extensions |
| **Hooks** | `hooks/hooks.json` | Automated event-driven actions |
| **MCP Servers** | `.mcp.json` | External service integration |

The `aisdlc-methodology` plugin contains the complete framework including commands, agents, and workspace templates.

---

## Installation

Plugins are deployed via `settings.json` configuration. Claude Code discovers plugins through:
1. **Marketplace** - A `.claude-plugin/marketplace.json` file listing available plugins
2. **Plugin manifests** - Each plugin has `.claude-plugin/plugin.json`

### Quick Start (Manual)

Create `.claude/settings.json` in your project:

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

Then restart Claude Code and verify with `/plugin`.

### Quick Start (Installer)

```bash
# Clone the repo
git clone https://github.com/foolishimp/ai_sdlc_method.git ~/ai_sdlc_method

# Configure your project with GitHub source (recommended)
python ~/ai_sdlc_method/claude-code/installers/setup_settings.py --target /your/project --source github

# Or with local directory source (for development)
python ~/ai_sdlc_method/claude-code/installers/setup_settings.py --target /your/project --source directory
```

### Verifying Installation

After configuration, restart Claude Code and run:

```
/plugin
```

You should see all plugins as "Installed". If there are errors, the `/plugin` output shows specific validation messages.

---

### Manual Configuration

Alternatively, manually create/edit `.claude/settings.json`:

#### GitHub Repository (Recommended)

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

#### Local Directory (Development)

```json
{
  "extraKnownMarketplaces": {
    "aisdlc-local": {
      "source": {
        "source": "directory",
        "path": "/path/to/ai_sdlc_method/claude-code/plugins"
      }
    }
  },
  "enabledPlugins": {
    "aisdlc-core@aisdlc-local": true,
    "aisdlc-methodology@aisdlc-local": true,
    "principles-key@aisdlc-local": true
  }
}
```

#### Git URL (Self-Hosted)

```json
{
  "extraKnownMarketplaces": {
    "aisdlc-private": {
      "source": {
        "source": "git",
        "url": "https://git.company.com/team/ai_sdlc_method.git",
        "path": "claude-code/plugins"
      }
    }
  },
  "enabledPlugins": {
    "aisdlc-methodology@aisdlc-private": true
  }
}
```

---

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

### Plugin Bundles

Use `--bundle` with setup_settings.py:

| Bundle | Plugins | Use Case |
|--------|---------|----------|
| **startup** | aisdlc-core, aisdlc-methodology, principles-key | Getting started |
| **datascience** | aisdlc-core, testing-skills, python-standards, runtime-skills | Data science |
| **qa** | testing-skills, code-skills, requirements-skills, runtime-skills | QA focus |
| **enterprise** | All 9 plugins | Complete SDLC |

---

## What Gets Loaded

### From `aisdlc-methodology` Plugin

**Commands** (7 slash commands):
- `/aisdlc-checkpoint-tasks` - Save progress and update task status
- `/aisdlc-commit-task` - Commit with proper message and REQ tags
- `/aisdlc-finish-task` - Complete task with documentation
- `/aisdlc-refresh-context` - Refresh methodology context
- `/aisdlc-release` - Release framework to projects
- `/aisdlc-status` - Show task queue status
- `/aisdlc-update` - Update AI SDLC framework

**Agents** (7 stage personas):
- `aisdlc-requirements-agent` - Requirements stage persona
- `aisdlc-design-agent` - Design stage persona
- `aisdlc-tasks-agent` - Tasks stage persona
- `aisdlc-code-agent` - Code stage persona (TDD)
- `aisdlc-system-test-agent` - System test persona (BDD)
- `aisdlc-uat-agent` - UAT stage persona
- `aisdlc-runtime-feedback-agent` - Runtime feedback persona

### From Skill Plugins

41 skills across domains:
- **Requirements**: extraction, disambiguation, business rules
- **Design**: ADRs, traceability, coverage
- **Code**: TDD, BDD, generation, tech debt
- **Testing**: coverage, validation, reports
- **Runtime**: telemetry, observability, tracing

---

## Official Documentation References

| Document | URL |
|----------|-----|
| **Plugins Overview** | https://code.claude.com/docs/en/plugins |
| **Plugin Reference** | https://code.claude.com/docs/en/plugins-reference |
| **Settings Reference** | https://code.claude.com/docs/en/settings |
| **Skills Documentation** | https://code.claude.com/docs/en/skills |

---

## Documentation

- **Plugin System**: [plugins/README.md](plugins/README.md)
- **Complete Methodology**: [../docs/ai_sdlc_method.md](../docs/ai_sdlc_method.md)
- **Quick Start**: [../QUICKSTART.md](../QUICKSTART.md)
- **Journey Guide**: [guides/JOURNEY.md](guides/JOURNEY.md)
- **ADR-006**: [../docs/design/claude_aisdlc/adrs/ADR-006-plugin-configuration-and-discovery.md](../docs/design/claude_aisdlc/adrs/ADR-006-plugin-configuration-and-discovery.md)

---

## Related

- **Examples**: [ai_sdlc_examples](https://github.com/foolishimp/ai_sdlc_examples) - Complete example projects
- **Design Docs**: [../docs/design/](../docs/design/) - Architecture documentation

---

**"Excellence or nothing"** 🔥
