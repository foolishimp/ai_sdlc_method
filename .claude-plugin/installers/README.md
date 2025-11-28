# AI SDLC Method - Installer

One-command setup for the AI SDLC methodology in Claude Code.

## Quick Install

```bash
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -
```

**That's it!** Restart Claude Code and the methodology is ready.

## What It Does

Creates `.claude/settings.json` with:
1. **Marketplace reference** - Points to the GitHub plugin source
2. **Plugin enabled** - Activates `aisdlc-methodology`

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
    "aisdlc-methodology@aisdlc": true
  }
}
```

## Options

```bash
# Basic setup (marketplace + plugin)
curl -sL .../aisdlc-setup.py | python3 -

# With task workspace structure
curl -sL .../aisdlc-setup.py | python3 - --workspace

# With lifecycle hooks
curl -sL .../aisdlc-setup.py | python3 - --hooks

# Full setup
curl -sL .../aisdlc-setup.py | python3 - --workspace --hooks

# Preview changes
curl -sL .../aisdlc-setup.py | python3 - --dry-run

# Specific target directory
curl -sL .../aisdlc-setup.py | python3 - --target /path/to/project
```

| Option | Description |
|--------|-------------|
| `--target PATH` | Target project directory (default: current) |
| `--workspace` | Create `.ai-workspace/` task tracking structure |
| `--hooks` | Install lifecycle hooks (session start/stop, commit warnings) |
| `--dry-run` | Preview changes without writing |

## Verify Installation

After restarting Claude Code:

```
/plugin
```

Expected output:
```
Marketplaces:
  - aisdlc (Installed)

Plugins:
  - aisdlc-methodology (Installed)
```

## The Plugin

**aisdlc-methodology** is the consolidated plugin containing:
- **42 skills** across 7 categories (core, requirements, design, code, testing, runtime, principles)
- **7 agents** for each SDLC stage
- **7 commands** (`/aisdlc-*`)
- **4 hooks** (optional lifecycle automation)

## Manual Installation

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
    "aisdlc-methodology@aisdlc": true
  }
}
```

## Other Tools

| File | Purpose |
|------|---------|
| `validate_traceability.py` | Validate requirement traceability in a project |

## Troubleshooting

### Plugin not loading

1. Restart Claude Code after installation
2. Run `/plugin` to see status and errors
3. Check `.claude/settings.json` is valid JSON

### Permission errors

```bash
mkdir -p .claude  # Ensure directory exists
```

## Support

- **Issues**: https://github.com/foolishimp/ai_sdlc_method/issues
- **Documentation**: [docs/](../../docs/)
