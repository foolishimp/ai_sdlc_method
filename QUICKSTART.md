# AI SDLC Method - Quick Start

Get the **7-Stage AI SDLC Methodology** running in under a minute.

## Install

```bash
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/.claude-plugin/installers/aisdlc-setup.py | python3 -
```

Restart Claude Code. Done.

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
- **7 commands** (`/aisdlc-*`)
- **Requirement traceability** (REQ-F-*, REQ-NFR-*, REQ-DATA-*)

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
| **Tasks** | Work breakdown | Jira tickets with REQ tags |
| **Code** | TDD implementation | Code with `# Implements: REQ-*` |
| **System Test** | BDD integration | Given/When/Then scenarios |
| **UAT** | Business validation | Sign-off documents |
| **Runtime** | Production feedback | Alerts -> New intents |

---

## Installation Options

```bash
# Basic (marketplace + plugin, hooks included automatically)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/.claude-plugin/installers/aisdlc-setup.py | python3 -

# With task workspace (.ai-workspace/ structure)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/.claude-plugin/installers/aisdlc-setup.py | python3 - --workspace

# Preview changes without writing
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/.claude-plugin/installers/aisdlc-setup.py | python3 - --dry-run
```

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

## Next Steps

- **[Journey Guide](.claude-plugin/guides/JOURNEY.md)** - Full 7-stage walkthrough
- **[Methodology Overview](docs/requirements/AI_SDLC_OVERVIEW.md)** - High-level introduction
- **[Example Projects](https://github.com/foolishimp/ai_sdlc_examples)** - Working examples
