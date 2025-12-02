# Task: Update docs/guides to Match Current Reality

**Status**: Completed
**Date**: 2025-12-02
**Time**: 15:00
**Actual Time**: ~30 minutes

**Task ID**: #24 (ad-hoc)
**Requirements**: REQ-F-WORKSPACE-002, REQ-NFR-CONTEXT-001

---

## Problem

The documentation in `docs/guides/` was outdated and contained numerous discrepancies with the current project reality:
- Wrong plugin paths
- Non-existent marketplace commands
- Incorrect version numbers
- Hardcoded line counts that became stale
- References to non-existent installer files
- Wrong slash commands listed

---

## Investigation

Used the requirements agent to analyze the current project structure and compare against documentation:

1. **Plugin Path**: Documentation referenced `claude-code/plugins/aisdlc-methodology/` but actual location is `claude-code/.claude-plugin/plugins/aisdlc-methodology/`
2. **Installation Method**: Documentation showed `/plugin marketplace add` commands that don't exist; actual method is Python installer via curl
3. **Plugin Version**: Documentation claimed v2.0.0, actual is v4.4.0
4. **Config Lines**: Documentation claimed 1,273 lines in stages_config.yml, actual is 790 lines
5. **Commands**: Documentation listed non-existent commands (`/aisdlc-start-session`, `/aisdlc-todo`); only 8 actual commands exist

---

## Solution

**Files Updated**:

1. **docs/guides/README.md** - Rewrote to reflect current plugin-based architecture
2. **docs/guides/PLUGIN_GUIDE.md** - Fixed installation, paths, and configuration
3. **docs/guides/NEW_PROJECT_SETUP.md** - Updated to use actual Python installer
4. **docs/guides/JOURNEY.md** - Fixed all discrepancies

**Key Changes**:
- Replaced all marketplace installation commands with curl one-liner from QUICKSTART.md
- Fixed all plugin paths to use `.claude-plugin/` subdirectory
- Removed all specific line counts (maintenance burden)
- Updated Commands Reference to show actual 8 `/aisdlc-*` commands
- Removed non-existent commands
- Added verification steps with `/plugin` command
- Updated version references

---

## Files Modified

- `docs/guides/README.md` - Modified (rewrote for current architecture)
- `docs/guides/PLUGIN_GUIDE.md` - Modified (fixed paths, installation, config)
- `docs/guides/NEW_PROJECT_SETUP.md` - Modified (updated installer method)
- `docs/guides/JOURNEY.md` - Modified (fixed all discrepancies)

---

## Result

✅ **Task completed successfully**
- All 4 guide files updated to match current reality
- Removed all hardcoded line counts (no more stale numbers)
- Installation instructions now use preferred curl one-liner
- All file paths corrected
- All command references accurate

---

## Key Changes Summary

| Issue | Before | After |
|-------|--------|-------|
| Plugin path | `claude-code/plugins/...` | `claude-code/.claude-plugin/plugins/...` |
| Installation | Marketplace commands | `curl -sL ... \| python3 -` |
| Config lines | 1,273 lines | (removed - no hardcoded counts) |
| Version | v2.0.0 | (removed specific version refs) |
| Commands | 10+ including non-existent | 8 actual commands |

---

## Lessons Learned

1. **Avoid hardcoded metrics**: Line counts, skill counts, etc. become stale quickly
2. **Single source of truth**: QUICKSTART.md has the canonical installation method
3. **Path changes need propagation**: When plugin structure changes, docs need updates

---

## Traceability

**Requirements Coverage**:
- REQ-F-WORKSPACE-002: ✅ Documentation templates updated
- REQ-NFR-CONTEXT-001: ✅ Guides provide accurate context for new users

**Downstream Traceability**:
- Files: docs/guides/README.md, PLUGIN_GUIDE.md, NEW_PROJECT_SETUP.md, JOURNEY.md

---

## Related

- **QUICKSTART.md**: Source of truth for installation method
- **Plugin location**: `claude-code/.claude-plugin/plugins/aisdlc-methodology/`
