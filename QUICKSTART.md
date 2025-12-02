# AI SDLC Method - Quick Start

Get the **7-Stage AI SDLC Methodology** running in under a minute.

## Install

```bash
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -
```

Restart Claude Code. Done.

## What Gets Created

```
your-project/
├── .claude/settings.json          # Plugin configuration (GitHub marketplace)
└── .ai-workspace/                  # Task tracking workspace
    ├── tasks/
    │   ├── active/ACTIVE_TASKS.md  # Your current tasks
    │   └── finished/               # Completed task docs
    ├── templates/                  # Task templates
    │   ├── TASK_TEMPLATE.md
    │   ├── FINISHED_TASK_TEMPLATE.md
    │   └── AISDLC_METHOD_REFERENCE.md
    └── config/workspace_config.yml
```

## Verify

```
/plugin
```

You should see:
```
Marketplaces:
  - aisdlc (Installed)

Plugins:
  - aisdlc-methodology (Installed)
```

## Try It

Ask Claude:
```
"Help me implement user authentication following the AI SDLC methodology"
```

Claude will guide you through the 7-stage lifecycle with requirement traceability.

---

## What You Get

**aisdlc-methodology** - The complete AI SDLC plugin:
- **42 skills** (requirements, design, code, testing, runtime, principles)
- **7 agents** (one per SDLC stage)
- **8 commands** (`/aisdlc-*`)
- **Requirement traceability** (REQ-F-*, REQ-NFR-*, REQ-DATA-*)
- **Task workspace** with templates

## The 7 Stages

```
Intent -> Requirements -> Design -> Tasks -> Code -> System Test -> UAT -> Runtime
           ^                                                                  |
           +--------------------------- Feedback Loop ------------------------+
```

| Stage | Purpose | Output |
|-------|---------|--------|
| **Requirements** | Transform intent | REQ-F-AUTH-001, REQ-NFR-PERF-001 |
| **Design** | Technical solution | Components, APIs, data models |
| **Tasks** | Work breakdown | Tickets with REQ tags |
| **Code** | TDD implementation | Code with `# Implements: REQ-*` |
| **System Test** | BDD integration | Given/When/Then scenarios |
| **UAT** | Business validation | Sign-off documents |
| **Runtime** | Production feedback | Alerts -> New intents |

---

## Installation Options

```bash
# Full setup (plugin + workspace) - DEFAULT
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -

# Plugin only (no workspace)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --no-workspace

# Preview changes without writing
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --dry-run
```

**Safe to re-run**: Existing files (tasks, finished work) are preserved.

## Manual Installation

Create `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "aisdlc": {
      "source": {
        "source": "github",
        "repo": "foolishimp/ai_sdlc_method"
      }
    }
  },
  "enabledPlugins": {
    "aisdlc-methodology@aisdlc": true
  }
}
```

---

## Key Commands

| Command | Purpose |
|---------|---------|
| `/aisdlc-help` | Full methodology guide |
| `/aisdlc-status` | Task queue status |
| `/aisdlc-checkpoint-tasks` | Save progress, create finished docs |
| `/aisdlc-finish-task <id>` | Complete a specific task |
| `/aisdlc-commit-task <id>` | Generate commit message |
| `/aisdlc-release` | Create new release |

---

## Next Steps

- **[README.md](README.md)** - Full documentation
- **[CLAUDE.md](CLAUDE.md)** - Project guide and methodology overview
- **[Example Projects](https://github.com/foolishimp/ai_sdlc_examples)** - Working examples
