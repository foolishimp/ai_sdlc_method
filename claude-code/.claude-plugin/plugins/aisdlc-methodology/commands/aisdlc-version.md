# /aisdlc-version - Show AI SDLC Plugin Version

Display the current version of the AI SDLC methodology plugin and its components.

<!-- Implements: REQ-TOOL-005 (Release Management) -->

## Instructions

Read and display version information from the following files:

1. **Plugin Version**: `claude-code/.claude-plugin/plugins/aisdlc-methodology/.claude-plugin/plugin.json` (field: `version`)
2. **Stages Config Version**: `claude-code/.claude-plugin/plugins/aisdlc-methodology/config/stages_config.yml` (field: `ai_sdlc_stages.version`)
3. **Git Tag** (if available): Run `git describe --tags --abbrev=0` to get latest tag

Display output in this format:

```
╔══════════════════════════════════════════════════════════════╗
║               AI SDLC Method - Version Info                  ║
╚══════════════════════════════════════════════════════════════╝

  Plugin:        aisdlc-methodology
  Version:       v{version from plugin.json}
  Stages Config: v{version from stages_config.yml}
  Git Tag:       {latest git tag or "none"}

  Homepage:      https://github.com/foolishimp/ai_sdlc_method

  Components:
  ├─ Agents:     7 (Requirements, Design, Tasks, Code, System Test, UAT, Runtime)
  ├─ Commands:   9 (including this one)
  ├─ Skills:     11 consolidated workflows
  └─ Hooks:      2 (Stop, PreToolUse)

  Changelog (latest):
  {read metadata.changelog from stages_config.yml}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Run /aisdlc-init --force to update framework files
  Run /aisdlc-help for full command reference
```

---

**Usage**: Run `/aisdlc-version` to display version information.
