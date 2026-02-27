# ADR-018: Plugin Marketplace Distribution

**Status**: Accepted
**Date**: 2026-02-24
**Deciders**: Methodology Author
**Requirements**: REQ-TOOL-011 (Installability), REQ-TOOL-003 (Workflow Commands)
**Extends**: ADR-012 (Two-Command UX)

---

## Context

The genesis methodology is distributed as a Claude Code plugin via a GitHub-hosted marketplace. Getting plugin discovery, installation, and hook delivery to work correctly required understanding undocumented behaviours of Claude Code's plugin system. This ADR captures the distribution architecture and the hard-won constraints discovered during implementation.

### Key Problem

The plugin source code lives deep in the repository (`imp_claude/code/.claude-plugin/plugins/genesis/`) because the repo is multi-tenant (Claude, Gemini, Codex, Bedrock implementations). The marketplace mechanism must bridge from the repo root to the plugin location.

---

## Decision

### Marketplace Structure

The repository root contains `.claude-plugin/marketplace.json` — this is the entry point Claude Code reads when a marketplace is registered.

```
ai_sdlc_method/                          # repo root (= clone root)
├── .claude-plugin/
│   └── marketplace.json                 # marketplace entry point
└── imp_claude/code/.claude-plugin/
    ├── marketplace.json                 # inner marketplace (for local dev)
    └── plugins/genesis/                 # the actual plugin
        ├── plugin.json
        ├── commands/
        ├── agents/
        ├── hooks/
        │   ├── hooks.json               # hook definitions (${CLAUDE_PLUGIN_ROOT})
        │   └── *.sh                     # hook scripts
        └── config/
```

### Path Resolution Rules (empirically determined)

1. **Source paths in `marketplace.json` resolve from the repo clone root**, not from the `.claude-plugin/` directory
2. `../` in source paths is **rejected by schema validation** — returns "Invalid input"
3. Correct source path: `"source": "./imp_claude/code/.claude-plugin/plugins/genesis"`
4. Claude Code clones marketplace repos to `~/.claude/plugins/marketplaces/<name>/`

### Installation Flow

```
1. curl | python3 -          → gen-setup.py writes .claude/settings.json + .ai-workspace/
2. Restart Claude Code       → reads settings.json, discovers marketplace
3. /plugin install genesis@genesis → fetches plugin from marketplace, installs hooks/commands/agents
4. /gen-start                → methodology begins
```

### What the Installer Delivers

The installer (`gen-setup.py`) creates **only**:
- `.claude/settings.json` — marketplace registration + plugin enablement
- `.ai-workspace/` — workspace structure (events, features, tasks, graph, context)
- `specification/INTENT.md` — intent template
- `CLAUDE.md` — Genesis Bootloader (appended)

The installer does **not** deliver hooks, commands, or agents. These are delivered natively by the plugin system via `/plugin install`.

### What the Plugin Delivers

Via `plugin.json`:
- 13 commands (gen-start, gen-status, gen-init, gen-iterate, etc.)
- 4 agents (gen-iterate, gen-dev-observer, gen-cicd-observer, gen-ops-observer)
- 4 hooks via `hooks.json` (SessionStart, UserPromptSubmit, PostToolUse, Stop)

Hooks use `${CLAUDE_PLUGIN_ROOT}` for script paths — Claude Code resolves this to the installed plugin location.

### Legacy Migration

The installer removes pre-genesis keys on re-install:
- `aisdlc` marketplace → removed from `extraKnownMarketplaces`
- `gen-methodology-v2@aisdlc` → removed from `enabledPlugins`
- Stale plugin caches cleared from `~/.claude/plugins/`

### Cache Architecture

Claude Code maintains several caches that can become stale:

| Cache | Location | Purpose |
|-------|----------|---------|
| Marketplace clone | `~/.claude/plugins/marketplaces/<name>/` | Full repo clone |
| Plugin install | `~/.claude/plugins/cache/<marketplace>/<plugin>/` | Installed plugin files |
| Marketplace registry | `~/.claude/plugins/known_marketplaces.json` | Known marketplace metadata |
| Install records | `~/.claude/plugins/installed_plugins.json` | Which plugins are installed where |

**Stale caches are the primary cause of "plugin not found" errors.** When the plugin structure changes, all four caches must be cleared for a clean re-fetch.

### Development vs. Production

In the development repo, `.claude/commands/` contains symlinks to plugin command files for non-namespaced `/gen-start` access. In production (installed projects), commands are namespaced as `/genesis:gen-start` or available as `/gen-start` when installed.

---

## Consequences

### Positive
- Single GitHub repo serves as both source and distribution — no separate package registry
- Plugin system handles hook, command, and agent delivery natively
- Installer stays simple — just settings + workspace scaffolding
- Legacy migration is automatic on re-install

### Negative
- Source path resolution from repo root (not `.claude-plugin/`) is undocumented and was discovered empirically
- Cache invalidation requires manual clearing or installer assistance — no built-in cache-bust mechanism
- Multi-tenant repos require deep nesting of the plugin path

### Risks
- Claude Code plugin system is evolving — path resolution behaviour could change
- No schema documentation for `marketplace.json` — constraints discovered by trial and error

---

## References

- ADR-012: Two-Command UX Layer
- REQ-TOOL-011: Installability
- `imp_claude/code/installers/gen-setup.py`: Installer implementation
- `.claude-plugin/marketplace.json`: Root marketplace entry point
- `imp_claude/code/.claude-plugin/plugins/genesis/plugin.json`: Plugin manifest
- `anthropics/claude-plugins-official`: Reference marketplace implementation
