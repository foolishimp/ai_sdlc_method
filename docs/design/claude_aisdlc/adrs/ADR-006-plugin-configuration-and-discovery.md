# ADR-006: Plugin Configuration and Discovery

**Status**: Accepted
**Date**: 2025-11-26
**Deciders**: Development Tools Team
**Requirements**: REQ-F-PLUGIN-001 (Plugin System), REQ-F-PLUGIN-002 (Federated Loading)
**Depends On**: ADR-001 (Claude Code as Platform), ADR-004 (Skills for Reusable Capabilities)

---

## Context

During dogfooding of the AI SDLC Method on 2025-11-26, we discovered that our plugin configuration was using an **incorrect format**. This ADR documents the **correct official Claude Code plugin configuration** based on research from official documentation.

### Key Insight: Plugins are the Organizational Structure

**Plugins are the unified container for ALL Claude Code extensibility features:**

| Feature | Location in Plugin | Role |
|---------|-------------------|------|
| **Commands** | `commands/` | User-invoked custom slash commands |
| **Agents** | `agents/` | Task-specific autonomous subagents |
| **Skills** | `skills/` | Model-driven capability extensions |
| **Hooks** | `hooks/hooks.json` | Automated event-driven actions |
| **MCP Servers** | `.mcp.json` | External service integration |

This means our separate `.claude/commands/`, `.claude/agents/`, etc. can ALL be organized under plugins for better distribution, versioning, and team sharing.

### The Problem

Our initial `.claude/settings.json` used:
```json
{
  "plugins": [
    "file://claude-code/plugins/aisdlc-core",
    "file://claude-code/plugins/aisdlc-methodology"
  ]
}
```

This format is **NOT valid**. The `plugins` key does not exist in Claude Code's settings schema.

---

## Decision

**We will use the official Claude Code plugin configuration format using `extraKnownMarketplaces` and `enabledPlugins`.**

### Correct Configuration Format

```json
{
  "extraKnownMarketplaces": {
    "marketplace-name": {
      "source": {
        "source": "directory",
        "path": "./.claude/plugins"
      }
    }
  },
  "enabledPlugins": {
    "plugin-name@marketplace-name": true
  }
}
```

### Marketplace Source Types

| Source Type | Format | Use Case |
|-------------|--------|----------|
| `directory` | `"path": "/local/path"` | Local development |
| `github` | `"repo": "owner/repo"` | GitHub repositories |
| `git` | `"url": "https://..."` | Any git URL |

---

## Official Documentation References

**IMPORTANT**: These URLs are the authoritative source for Claude Code plugin configuration.

### Primary References

| Document | URL | Content |
|----------|-----|---------|
| **Plugins Overview** | https://code.claude.com/docs/en/plugins | How plugins work, installation, team setup |
| **Plugin Reference** | https://code.claude.com/docs/en/plugins-reference | Complete plugin.json schema, directory structure |
| **Settings Reference** | https://code.claude.com/docs/en/settings | settings.json format, enabledPlugins, extraKnownMarketplaces |
| **Skills Documentation** | https://code.claude.com/docs/en/skills | SKILL.md format, skill discovery |

### Key Findings from Documentation

1. **Plugin Commands Exist**: `/plugin` command provides interactive plugin management
2. **No `plugins` key**: Settings use `enabledPlugins` and `extraKnownMarketplaces`
3. **Directory source**: For local development, use `"source": "directory"` with `"path"`
4. **Skills auto-discovered**: Skills in `plugin-root/skills/*/SKILL.md` are automatically found
5. **Debug mode**: Run `claude --debug` to see plugin loading details

---

## Implementation

### 1. Plugin Directory Structure (Official)

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # REQUIRED - manifest
├── commands/                 # Slash commands (default location)
├── agents/                   # Subagent definitions
├── skills/                   # Auto-discovered skills
│   └── skill-name/
│       └── SKILL.md         # Skill definition
├── hooks/
│   └── hooks.json           # Event hooks
├── .mcp.json                # MCP server config
└── scripts/                 # Supporting scripts
```

**Critical**: `.claude-plugin/` contains ONLY `plugin.json`. All other directories at plugin root.

### 2. plugin.json Schema (Official)

```json
{
  "name": "plugin-name",           // REQUIRED - kebab-case
  "version": "1.0.0",              // Semantic version
  "description": "What it does",
  "author": {
    "name": "Author Name",
    "email": "email@example.com"
  },
  "homepage": "https://...",
  "repository": "https://...",
  "license": "MIT",
  "keywords": ["tag1", "tag2"],

  // Component paths (optional - defaults exist)
  "commands": "./commands",        // or array of paths
  "agents": "./agents",
  "hooks": "./hooks/hooks.json",   // or inline object
  "mcpServers": "./.mcp.json"      // or inline object
}
```

### 3. settings.json for Local Development

For the ai_sdlc_method project (dogfooding):

```json
{
  "extraKnownMarketplaces": {
    "aisdlc-local": {
      "source": {
        "source": "directory",
        "path": "./.claude/plugins"
      }
    }
  },
  "enabledPlugins": {
    "aisdlc-core@aisdlc-local": true,
    "aisdlc-methodology@aisdlc-local": true,
    "principles-key@aisdlc-local": true,
    "code-skills@aisdlc-local": true,
    "testing-skills@aisdlc-local": true,
    "requirements-skills@aisdlc-local": true,
    "design-skills@aisdlc-local": true,
    "runtime-skills@aisdlc-local": true,
    "python-standards@aisdlc-local": true
  }
}
```

### 4. settings.json for External Users (GitHub)

For users installing from GitHub:

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
    "aisdlc-core@aisdlc": true,
    "aisdlc-methodology@aisdlc": true,
    "principles-key@aisdlc": true
  }
}
```

### 5. SKILL.md Format (Official)

```yaml
---
name: skill-name                    # lowercase, hyphens only
description: What it does and when  # max 1024 chars
allowed-tools: [Read, Write, Edit]  # optional tool restrictions
---

# skill-name

Detailed instructions for Claude...
```

---

## Rationale

### Why This Configuration

1. **Official format**: Matches Claude Code documentation
2. **Marketplace support**: Works with both local and remote sources
3. **Team sharing**: `extraKnownMarketplaces` enables team-wide plugin distribution
4. **Granular control**: `enabledPlugins` allows individual plugin toggling
5. **Debug support**: Official format enables `claude --debug` for troubleshooting

### What We Learned

| Assumption | Reality |
|------------|---------|
| `plugins: []` array | Does NOT exist |
| `file://` URLs | NOT supported |
| `/plugin` command | EXISTS and works |
| Skills in `.claude/skills/` only | Also discovered in plugin subdirectories |

---

## Installation Process

### For AI SDLC Method Project (Dogfooding)

1. **Run installer** to copy plugins to `.claude/plugins/`:
   ```bash
   python claude-code/installers/setup_plugins.py --bundle enterprise --force
   ```

2. **Configure settings.json** with marketplace and enabled plugins

3. **Restart Claude Code** to load plugins

4. **Verify** with `/plugin` command or `claude --debug`

### For External Users

1. **Add marketplace** to settings.json pointing to GitHub repo
2. **Enable plugins** in settings.json
3. **Restart Claude Code**

---

## Consequences

### Positive

✅ **Correct configuration** - Plugins load properly
✅ **Future-proof** - Aligned with official Claude Code evolution
✅ **Team distribution** - Easy to share plugins via marketplace
✅ **Documented** - Official URLs provide authoritative reference

### Negative

⚠️ **Breaking change** - Old `plugins: []` format no longer works

**Mitigation**: Update JOURNEY.md and installers to use correct format

⚠️ **Marketplace required** - Can't just point to directories directly

**Mitigation**: Use `"source": "directory"` for local development

---

## Related Decisions

- **ADR-001**: Claude Code as Platform
- **ADR-004**: Skills for Reusable Capabilities
- **ADR-005**: Iterative Refinement Feedback Loops

---

## Validation Checklist

After configuration:

- [ ] `/plugin` command shows installed plugins
- [ ] Skills from plugins are discoverable (ask Claude "what skills are available?")
- [ ] `claude --debug` shows plugin loading without errors
- [ ] Commands from plugins appear in `/help`

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2025-11-26 | Initial creation after dogfooding discovery |

---

**Status**: ✅ Accepted
**Implemented**: v0.3.0
**Next Review**: After plugin system validation
