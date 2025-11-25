# Task: Create Reset-Style Installer for Clean Updates

**Status**: Completed
**Date**: 2025-11-25
**Time**: 14:30
**Actual Time**: 1.5 hours

**Task ID**: #14 (Ad-hoc)
**Requirements**: REQ-F-RESET-001 (New)

---

## Problem

Stale installations were retaining old files and folders that had been removed or renamed in newer versions (e.g., the removed `todo` folder, renamed commands). The existing installer only added files but never cleaned up obsolete ones.

User requested:
1. Reset-style install that updates to a specific version tag
2. Scrubs legacy files/folders
3. Preserves `.ai-workspace/tasks/finished/` for historical context
4. Also preserves `.ai-workspace/tasks/active/` (active work)

---

## Solution

### Created New Files

1. **`installers/setup_reset.py`** - Full-featured reset installer
   - Uses local source or clones from GitHub at specific tag
   - Preserves user work (tasks/active, tasks/finished)
   - Removes and reinstalls framework code
   - Creates backup before changes
   - Supports `--dry-run` mode
   - Integrates with `setup_all.py --reset`

2. **`installers/aisdlc-reset.py`** - Self-contained curl-friendly installer
   - Single file, no dependencies on other installer modules
   - Can be run directly via curl:
     ```bash
     curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 -
     ```
   - Fetches latest tag automatically
   - Same preserve/remove logic as setup_reset.py

### Modified Files

3. **`installers/common.py`**
   - Added `get_ai_sdlc_version()` - reads version from git tag
   - Added `get_latest_release_tag(repo_url)` - fetches tags from remote

4. **`installers/setup_all.py`**
   - Added `--reset` flag for reset-style installation
   - Added `--version` flag for specifying target version
   - Delegates to setup_reset.py when `--reset` is specified

5. **`installers/README.md`**
   - Documented `setup_reset.py` with options and examples
   - Documented `aisdlc-reset.py` (curl-friendly)
   - Added "Reset Installation" to Common Usage Patterns

---

## Files Modified

- `installers/setup_reset.py` - NEW (500+ lines, full reset installer)
- `installers/aisdlc-reset.py` - NEW (350+ lines, self-contained curl installer)
- `installers/common.py` - Added version functions (40+ lines)
- `installers/setup_all.py` - Added reset mode support (30+ lines)
- `installers/README.md` - Documentation updates

---

## Testing

**Manual Testing**:
```bash
# Test dry-run (local source)
python installers/setup_reset.py --dry-run --source /Users/jim/src/apps/ai_sdlc_method

# Test self-contained installer
python3 installers/aisdlc-reset.py --dry-run --version v0.2.0
```

**Results**:
- Dry-run correctly identifies files to preserve (16 finished, 1 active)
- Dry-run correctly identifies framework files to remove (19 .claude, 34 .ai-workspace)
- Version fetching works from both local and remote
- Help text displays correctly for all options

---

## Result

**Task completed successfully**

Philosophy implemented: **Only immutable framework code is replaced. User work is always preserved.**

**What gets PRESERVED**:
- `.ai-workspace/tasks/active/` - Current active tasks
- `.ai-workspace/tasks/finished/` - Historical task documentation

**What gets REMOVED and reinstalled**:
- `.claude/commands/` - All commands
- `.claude/agents/` - All agent specs
- `.ai-workspace/templates/` - All templates
- `.ai-workspace/config/` - Configuration files

---

## Usage

### One-liner via curl (recommended for updates):
```bash
# Latest version
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 -

# Specific version
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --version v0.2.0

# Dry run first
curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --dry-run
```

### With local clone:
```bash
python installers/setup_all.py --reset
python installers/setup_all.py --reset --version v0.2.0
python installers/setup_reset.py --dry-run
```

---

## Traceability

**Requirements Coverage**:
- REQ-F-RESET-001: Reset-style installation for clean updates (NEW)

**Upstream Traceability**:
- User request: "update installer to do a reset style install that scrubs legacy files"

**Downstream Traceability**:
- Commit: (pending)
- Release: v0.3.0 (planned)

---

## Metrics

- **Lines Added**: ~900 (setup_reset.py + aisdlc-reset.py + common.py + setup_all.py + README)
- **Files Created**: 2
- **Files Modified**: 3

---

## Related

- **installers/setup_all.py** - Main orchestrator, now supports `--reset`
- **installers/common.py** - Shared utilities, now has version functions
- **installers/README.md** - Documentation hub for installers
