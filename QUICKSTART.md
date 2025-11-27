# AI SDLC Method Quick Start Guide

Get started with the **7-Stage AI SDLC Methodology** in 5 minutes.

**Platform**: Claude Code (CLI and VS Code Extension)

---

## What is ai_sdlc_method?

An **Intent-Driven AI SDLC Methodology** providing:

```
Intent → Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
           ↑                                                                    ↓
           └────────────────────── Feedback Loop ──────────────────────────────┘
```

**Key Features**:
- 7-stage lifecycle with AI agent configurations
- Requirement traceability (REQ-F-*, REQ-NFR-*, REQ-DATA-*)
- TDD workflow (RED → GREEN → REFACTOR)
- BDD testing (Given/When/Then)
- Bidirectional feedback loop

---

## Quick Install (One Command)

**From your project directory:**

```bash
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -
```

**That's it!** Restart Claude Code and you're ready.

### Installation Options

```bash
# Basic setup (3 core plugins)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -

# Full setup with task workspace and lifecycle hooks
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --workspace --hooks

# All 9 plugins (enterprise)
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --all

# Preview changes without writing
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --dry-run
```

### Verify Installation

After restarting Claude Code:

```
/plugin
```

You should see:
```
Marketplaces:
  ✔ aisdlc · Installed

Plugins:
  ✔ aisdlc-core · Installed
  ✔ aisdlc-methodology · Installed
  ✔ principles-key · Installed
```

### Try It Out

Ask Claude:
```
"Help me implement user authentication following the AI SDLC methodology"
```

Claude will guide you through all 7 stages with requirement traceability.

---

## Alternative: Manual Configuration

If you prefer manual setup, create `.claude/settings.json`:

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

### Plugin Bundles

Configure in `enabledPlugins`:

| Bundle | Plugins |
|--------|---------|
| **startup** | aisdlc-core, aisdlc-methodology, principles-key |
| **enterprise** | All 8 plugins |

---

## The 7 Stages

| Stage | Purpose | Output |
|-------|---------|--------|
| **1. Requirements** | Transform intent → structured requirements | REQ-F-AUTH-001, REQ-NFR-PERF-001 |
| **2. Design** | Requirements → technical solution | Components, APIs, data models |
| **3. Tasks** | Design → work units | Jira tickets with REQ tags |
| **4. Code** | TDD implementation | Code with `# Implements: REQ-*` |
| **5. System Test** | BDD integration testing | Feature files with Given/When/Then |
| **6. UAT** | Business validation | Sign-off documents |
| **7. Runtime Feedback** | Production telemetry | Alerts → New intents |

---

## Updating

**GitHub source**: Plugins update automatically when you restart Claude Code.

**Local directory source**:
```bash
cd ~/ai_sdlc_method
git pull origin main
# Restart Claude Code
```

---

## Next Steps

- **[Complete Journey](claude-code/guides/JOURNEY.md)** - Full 7-stage walkthrough (2-3 hours)
- **[Plugin Documentation](claude-code/README.md)** - All installation options
- **[Methodology Overview](docs/requirements/AI_SDLC_OVERVIEW.md)** - High-level methodology introduction
- **[Example Projects](https://github.com/foolishimp/ai_sdlc_examples)** - Working examples

---

## Documentation

| Document | Description |
|----------|-------------|
| [claude-code/README.md](claude-code/README.md) | Plugin system and installation |
| [claude-code/guides/JOURNEY.md](claude-code/guides/JOURNEY.md) | Complete setup to UAT walkthrough |
| [docs/requirements/AI_SDLC_OVERVIEW.md](docs/requirements/AI_SDLC_OVERVIEW.md) | Methodology overview (~30 min read) |
| [docs/README.md](docs/README.md) | Documentation index |

---

**"Excellence or nothing"** 🔥
