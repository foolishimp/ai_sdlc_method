# Task: Fix GitHub Marketplace Plugin Loading

**Status**: Completed
**Date**: 2025-12-02
**Time**: ~2 hours
**Actual Time**: 2 hours (Estimated: N/A - debugging task)

**Task ID**: #23
**Requirements**: REQ-F-PLUGIN-001 (Plugin System)

---

## Problem

The `.claude-plugin` marketplace was not loading correctly when using GitHub source in `extraKnownMarketplaces`. Plugins like `hello-world` and `aisdlc-methodology` showed "Plugin not found" errors despite being present in the repository.

---

## Investigation

1. Analyzed marketplace.json at `.claude-plugin/marketplace.json`
2. Reviewed Claude Code plugin documentation at code.claude.com
3. Discovered key insight: **Plugin source paths are resolved from repo root, not from where marketplace.json lives**
4. Found cache location: `~/.claude/plugins/marketplaces/{name}/` and `~/.claude/plugins/known_marketplaces.json`
5. Tested with local marketplace add via CLI: `/plugin marketplace add ./path` - worked
6. Tested with GitHub source in settings.json - initially failed due to path resolution

---

## Solution

**Root Cause**: When Claude Code loads a marketplace from GitHub:
1. It clones the entire repo to `~/.claude/plugins/marketplaces/{marketplace-name}/`
2. Plugin paths in marketplace.json are resolved **from repo root**, not relative to `.claude-plugin/`

**Fix**: Restructured plugin paths to be relative to repo root:

**Before** (broken):
```json
{
  "plugins": [
    {"name": "hello-world", "source": "./plugins/hello-world"}
  ]
}
```

**After** (working):
```json
{
  "plugins": [
    {"name": "hello-world", "source": "./testmkt/plugins/hello-world"},
    {"name": "aisdlc-methodology", "source": "./claude-code/.claude-plugin/plugins/aisdlc-methodology"}
  ]
}
```

---

## Files Modified

- `.claude-plugin/marketplace.json` - Modified (consolidated to single marketplace, fixed plugin paths)
- `testmkt/plugins/hello-world/.claude-plugin/plugin.json` - NEW (test plugin)
- `testmkt/plugins/hello-world/commands/hello.md` - NEW (test command)
- `.claude/settings.json` (project) - Modified (cleared enabledPlugins for testing)
- `~/.claude/settings.json` (user) - Modified (enabled plugins from aisdlc marketplace)
- `claude-code/installers/aisdlc-setup.py` - Verified (correct GitHub source format)

**Deleted** (cleanup):
- `claude-code/tests/sdk/test-marketplace/` - Removed (duplicate of testmkt)

---

## Testing

**Manual Testing**:
```bash
# Clear cache
rm -rf ~/.claude/plugins/marketplaces/*
rm -f ~/.claude/plugins/known_marketplaces.json

# Restart Claude Code
# Check plugins loaded
/plugin
```

**Results**:
- `hello-world@aisdlc` - Installed ✅
- `aisdlc-methodology@aisdlc` - Installed ✅
- GitHub source loading works ✅
- Installer generates correct bootstrap settings.json ✅

---

## Result

✅ **Task completed successfully**
- Both plugins load from GitHub marketplace
- Test plugin (`hello-world`) validates marketplace structure
- Production plugin (`aisdlc-methodology`) loads with all skills, agents, commands
- `aisdlc-setup.py` installer generates correct settings.json for new projects
- Cache clearing procedure documented

---

## Key Learnings

1. **Path Resolution**: Plugin source paths in marketplace.json are relative to **repo root** when using GitHub source, NOT relative to the `.claude-plugin/` directory

2. **Cache Location**: Claude Code caches marketplaces at:
   - `~/.claude/plugins/marketplaces/{name}/` - Full repo clone
   - `~/.claude/plugins/known_marketplaces.json` - Registry

3. **Clear Cache Procedure**:
   ```bash
   rm -rf ~/.claude/plugins/marketplaces/*
   rm -f ~/.claude/plugins/known_marketplaces.json
   ```

4. **Valid Source Format**: Settings.json requires nested structure:
   ```json
   {
     "extraKnownMarketplaces": {
       "aisdlc": {
         "source": {
           "source": "github",
           "repo": "foolishimp/ai_sdlc_method"
         }
       }
     }
   }
   ```

5. **Local Testing**: Use `/plugin marketplace add ./path` for quick local testing before pushing to GitHub

---

## Traceability

**Requirements Coverage**:
- REQ-F-PLUGIN-001: ✅ Plugin marketplace loading from GitHub works

**Downstream Traceability**:
- Commits: Multiple commits during debugging session
- Marketplace: `aisdlc` with 2 plugins (hello-world, aisdlc-methodology)

---

## Related

- **Related Tasks**: Task #22 (Simplify Installer to Single-Plugin Model)
- **Documentation**: https://code.claude.com/docs/en/plugin-marketplaces
- **Bootstrap Installer**: `claude-code/installers/aisdlc-setup.py`
