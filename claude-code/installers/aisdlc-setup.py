#!/usr/bin/env python3
"""
AI SDLC Method - One-Line Project Setup

Self-contained installer that can be run directly from GitHub.

# Implements: REQ-F-PLUGIN-001 (Plugin System), REQ-F-WORKSPACE-001 (Workspace)

Usage:
    # From GitHub (recommended) - includes workspace by default
    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -

    # Plugin only (no workspace)
    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --no-workspace

    # Preview changes
    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --dry-run

    # Local usage
    python aisdlc-setup.py [options]

Options:
    --target PATH       Target directory (default: current)
    --no-workspace      Skip .ai-workspace/ creation (plugin only)
    --dry-run           Preview changes without writing
    --help              Show this help

What it does:
    1. Creates .claude/settings.json with AISDLC marketplace configuration
    2. Enables the aisdlc-methodology plugin (loads from GitHub, always up to date)
    3. Creates .ai-workspace/ with task tracking and templates (default)
    4. Plugin includes hooks that load automatically (welcome message, etc.)
"""

import sys
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime


# =============================================================================
# Configuration
# =============================================================================

GITHUB_REPO = "foolishimp/ai_sdlc_method"

# The consolidated plugin (contains all skills, agents, commands, and hooks)
PLUGIN_NAME = "aisdlc-methodology"


# =============================================================================
# Workspace Templates (embedded for curl-friendly one-liner)
# =============================================================================

ACTIVE_TASKS_TEMPLATE = '''# Active Tasks

*Last Updated: {date}*

---

## Summary

**Total Active Tasks**: 0
- High Priority: 0
- Medium Priority: 0
- Not Started: 0
- In Progress: 0

**Recently Completed**: None yet

---

## Recovery Commands

If context is lost, run these commands to get back:
```bash
cat .ai-workspace/tasks/active/ACTIVE_TASKS.md  # This file
git status                                       # Current state
git log --oneline -5                            # Recent commits
/aisdlc-status                                   # Task queue status
```
'''

TASK_TEMPLATE = '''# Task #{ID}: {TITLE}

**Priority**: High | Medium | Low
**Status**: Not Started
**Estimated Time**: X hours
**Dependencies**: None
**Feature Flag**: `task-{id}-{description}` (defaultValue: false)

**Requirements Traceability**:
- REQ-F-XXX-001: Description
- REQ-NFR-XXX-002: Description

---

## Description

What needs to be done and why?

---

## Acceptance Criteria

- [ ] All tests pass (RED → GREEN → REFACTOR)
- [ ] Test coverage ≥ 80%
- [ ] No duplicate code (DRY principle)
- [ ] Error handling for all edge cases
- [ ] Feature flag tested both enabled/disabled
- [ ] Performance requirements met
- [ ] Documentation updated

---

## TDD Checklist

- [ ] RED: Write failing tests
- [ ] GREEN: Implement minimal solution
- [ ] REFACTOR: Improve code quality
- [ ] COMMIT: Create finished task document

---

## Notes

- Promoted From: Todo on YYYY-MM-DD HH:MM (if applicable)
- Additional context or considerations

---

**Created**: {TIMESTAMP}
**Last Updated**: {TIMESTAMP}
'''

FINISHED_TASK_TEMPLATE = '''# Task: {TITLE}

**Status**: Completed
**Date**: {DATE}
**Time**: {TIME}
**Actual Time**: X hours (Estimated: Y hours)

**Task ID**: #{ID}
**Requirements**: REQ-F-XXX-001, REQ-NFR-XXX-002

---

## Problem

What was the issue or requirement that needed to be addressed?

---

## Investigation

What did you discover during analysis?

1. Analyzed...
2. Reviewed...
3. Found...

---

## Solution

**Architectural Changes**:
- Created...
- Implemented...
- Added...

**TDD Process**:
1. **RED Phase** (X min):
   - Wrote N failing tests for...
2. **GREEN Phase** (X min):
   - Implemented... to pass tests
3. **REFACTOR Phase** (X min):
   - Extracted...
   - Improved...
   - Optimized...

---

## Files Modified

- `/path/to/file1.ext` - NEW (description)
- `/path/to/file2.ext` - Modified (description)
- `/path/to/file3.ext` - Refactored (description)

---

## Test Coverage

**Before**: X% (N tests)
**After**: Y% (M tests)

**Test Breakdown**:
- **Unit Tests**: N tests
- **Integration Tests**: M tests
- **Performance Tests**: P tests

---

## Result

✅ **Task completed successfully**
- Outcome 1
- Outcome 2
- Outcome 3

---

## Traceability

**Requirements Coverage**:
- REQ-F-XXX-001: ✅ Tests in `test_file.ext::test_function`
- REQ-NFR-XXX-002: ✅ Tests in `test_file.ext::test_function`

**Downstream Traceability**:
- Commit: `hash` "Commit message"
- Release: vX.Y.Z

---

## Lessons Learned

1. **Lesson 1**: What we learned
2. **Lesson 2**: What we learned
3. **Lesson 3**: What we learned
'''

METHOD_REFERENCE = '''# AI SDLC Method Quick Reference

**Version:** 3.1.0
**Purpose:** Quick reference for AI SDLC methodology

---

## Core Principle

**"Session = Context. Context persists in ACTIVE_TASKS.md."**

---

## Workspace Structure

```
.ai-workspace/
├── tasks/
│   ├── active/
│   │   └── ACTIVE_TASKS.md        # Single file: tasks + status + summary
│   └── finished/                  # Completed task documentation
│       └── YYYYMMDD_HHMM_task_name.md
│
├── templates/                     # Templates for tasks
│   ├── TASK_TEMPLATE.md
│   ├── FINISHED_TASK_TEMPLATE.md
│   └── AISDLC_METHOD_REFERENCE.md (this file)
│
└── config/                        # Workspace configuration
```

---

## Workflow

### During Work
```bash
# Use TodoWrite tool to track progress
# Work on tasks from ACTIVE_TASKS.md
# Follow TDD for code: RED → GREEN → REFACTOR
```

### After Work (CRITICAL!)
```bash
/aisdlc-checkpoint-tasks
# Syncs tasks, creates finished docs, updates ACTIVE_TASKS.md
```

### Commit
```bash
/aisdlc-commit-task <id>
# Generates proper commit message with REQ tags
```

---

## Slash Commands

| When | Command |
|------|---------|
| After work | `/aisdlc-checkpoint-tasks` ⭐ |
| Finish task | `/aisdlc-finish-task <id>` |
| Commit | `/aisdlc-commit-task <id>` |
| Check status | `/aisdlc-status` |
| Release | `/aisdlc-release` |
| Help | `/aisdlc-help` |

---

## The 7 Key Principles (Code Stage)

1. **Test Driven Development** - RED → GREEN → REFACTOR → COMMIT
2. **Fail Fast & Root Cause** - Fix at source, no workarounds
3. **Modular & Maintainable** - Single responsibility
4. **Reuse Before Build** - Check existing first
5. **Open Source First** - Suggest alternatives
6. **No Legacy Baggage** - Start clean
7. **Perfectionist Excellence** - Excellence or nothing 🔥

---

## TDD Cycle

```
RED    → Write failing test first
GREEN  → Implement minimal solution
REFACTOR → Improve code quality
COMMIT → Save with REQ tags
```

---

## 7-Stage AI SDLC

```
Intent → Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback
           ↑                                                                   ↓
           └────────────────────── Feedback Loop ─────────────────────────────┘
```

**Quick stage reference:**
1. Requirements → REQ-F-*, REQ-NFR-*, REQ-DATA-*
2. Design → Components, APIs, ADRs
3. Tasks → Tickets with REQ tags
4. **Code** → TDD (RED→GREEN→REFACTOR), tag with `# Implements: REQ-*` ⭐
5. System Test → BDD (Given/When/Then)
6. UAT → Business validation
7. Runtime Feedback → Telemetry → new intents

---

**"Excellence or nothing"** 🔥
'''

WORKSPACE_CONFIG = '''# Developer Workspace Configuration
version: "1.0"

# Task tracking
task_tracking:
  enabled: true
  active_file: "tasks/active/ACTIVE_TASKS.md"
  finished_dir: "tasks/finished/"
  template: "templates/TASK_TEMPLATE.md"
  finished_template: "templates/FINISHED_TASK_TEMPLATE.md"

# TDD workflow
tdd:
  enforce: true
  workflow: "RED → GREEN → REFACTOR → COMMIT"
  min_coverage: 80

# Requirement key tagging
ai_sdlc:
  require_req_keys: false
  req_key_pattern: "REQ-{TYPE}-{DOMAIN}-{SEQ}"
'''


# =============================================================================
# Workspace Structure
# =============================================================================

def get_workspace_structure(date: str) -> dict:
    """Return workspace structure with templates."""
    return {
        ".ai-workspace/tasks/active/ACTIVE_TASKS.md": ACTIVE_TASKS_TEMPLATE.format(date=date),
        ".ai-workspace/tasks/finished/.gitkeep": "",
        ".ai-workspace/templates/TASK_TEMPLATE.md": TASK_TEMPLATE,
        ".ai-workspace/templates/FINISHED_TASK_TEMPLATE.md": FINISHED_TASK_TEMPLATE,
        ".ai-workspace/templates/AISDLC_METHOD_REFERENCE.md": METHOD_REFERENCE,
        ".ai-workspace/config/workspace_config.yml": WORKSPACE_CONFIG,
    }


# =============================================================================
# Installer Logic
# =============================================================================

def print_banner():
    """Print setup banner."""
    print()
    print("+" + "=" * 62 + "+")
    print("|" + " " * 14 + "AI SDLC Method - Project Setup" + " " * 17 + "|")
    print("+" + "=" * 62 + "+")
    print()


def print_success(msg):
    print(f"  [OK] {msg}")


def print_info(msg):
    print(f"  {msg}")


def print_warning(msg):
    print(f"  [WARN] {msg}")


def clear_plugin_cache(dry_run: bool) -> bool:
    """Clear cached plugin to ensure latest version is fetched."""
    # Claude Code stores marketplace plugins in multiple locations
    cache_locations = [
        # Marketplace cache (main location)
        Path.home() / ".claude" / "plugins" / "marketplaces" / "aisdlc",
        # Version-specific cache
        Path.home() / ".claude" / "plugins" / "cache" / "aisdlc" / PLUGIN_NAME,
    ]

    found_any = False
    for cache_dir in cache_locations:
        if not cache_dir.exists():
            continue

        found_any = True
        if dry_run:
            print_info(f"Would remove: {cache_dir}")
            continue

        try:
            shutil.rmtree(cache_dir)
            print_success(f"Cleared: {cache_dir}")
        except Exception as e:
            print_warning(f"Could not clear {cache_dir}: {e}")

    if not found_any:
        print_info("No cached plugin found (fresh install)")

    return True


def setup_settings(target: Path, dry_run: bool) -> bool:
    """Create or update .claude/settings.json with plugin configuration."""
    settings_file = target / ".claude" / "settings.json"

    # Load existing settings
    existing = {}
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            print_warning("Existing settings.json has invalid JSON, will overwrite")

    # Build marketplace configuration
    marketplace_config = {
        "source": "github",
        "repo": GITHUB_REPO
    }

    # Merge marketplace
    if "extraKnownMarketplaces" not in existing:
        existing["extraKnownMarketplaces"] = {}
    existing["extraKnownMarketplaces"]["aisdlc"] = {"source": marketplace_config}

    # Enable plugin
    if "enabledPlugins" not in existing:
        existing["enabledPlugins"] = {}
    existing["enabledPlugins"][f"{PLUGIN_NAME}@aisdlc"] = True

    if dry_run:
        print_info(f"Would create: {settings_file}")
        print(json.dumps(existing, indent=2))
        return True

    # Write settings
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_file, 'w') as f:
        json.dump(existing, f, indent=2)

    print_success(f"Created {settings_file}")
    return True


def setup_workspace(target: Path, dry_run: bool) -> bool:
    """Create .ai-workspace/ structure with templates."""
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    workspace_structure = get_workspace_structure(date)

    for rel_path, content in workspace_structure.items():
        file_path = target / rel_path

        if dry_run:
            print_info(f"Would create: {file_path}")
            continue

        file_path.parent.mkdir(parents=True, exist_ok=True)

        if not file_path.exists():
            with open(file_path, 'w') as f:
                f.write(content)
            print_success(f"Created {rel_path}")
        else:
            print_info(f"Exists: {rel_path}")

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Set up a project with AI SDLC Method",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full setup (plugin + workspace) - DEFAULT
  curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -

  # Plugin only (no workspace)
  curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --no-workspace

  # Preview changes
  curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --dry-run
        """
    )

    parser.add_argument(
        "--target",
        default=".",
        help="Target directory (default: current)"
    )

    parser.add_argument(
        "--no-workspace",
        action="store_true",
        help="Skip .ai-workspace/ creation (plugin only)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing"
    )

    args = parser.parse_args()

    # Resolve target
    target = Path(args.target).resolve()

    # Print banner
    print_banner()

    print_info(f"Target: {target}")
    print_info(f"Plugin: {PLUGIN_NAME} (includes hooks)")
    print_info(f"Workspace: {'No' if args.no_workspace else 'Yes (with templates)'}")
    if args.dry_run:
        print_warning("DRY RUN - no changes will be made")
    print()

    # Run setup
    success = True

    # 1. Clear plugin cache (ensures latest version)
    print("--- Plugin Cache ---")
    if not clear_plugin_cache(args.dry_run):
        success = False
    print()

    # 2. Settings (marketplace + plugin)
    print("--- Plugin Configuration ---")
    if not setup_settings(target, args.dry_run):
        success = False
    print()

    # 3. Workspace (default: yes)
    if not args.no_workspace:
        print("--- Workspace Structure ---")
        if not setup_workspace(target, args.dry_run):
            success = False
        print()

    # Summary
    print("=" * 64)
    if args.dry_run:
        print("  Dry run complete - no changes made")
    elif success:
        print("  Setup complete!")
        print()
        print("  Next steps:")
        print("    1. Restart Claude Code to load plugin")
        print("    2. You'll see the welcome message on startup")
        print("    3. Run /aisdlc-help for full guide")
        print()
        print("  What's installed:")
        print("    - Plugin: aisdlc-methodology (11 skills, 7 agents, 9 commands)")
        print("    - Hooks: checkpoint reminder, REQ-* tag validation")
        if not args.no_workspace:
            print("    - Workspace: .ai-workspace/ with task tracking")
            print("    - Templates: TASK_TEMPLATE.md, FINISHED_TASK_TEMPLATE.md")
            print("    - Reference: AISDLC_METHOD_REFERENCE.md")
        print()
        print("  Troubleshooting:")
        print("    If plugin doesn't update, manually clear the cache:")
        print("    rm -rf ~/.claude/plugins/marketplaces/aisdlc")
        print("    Then restart Claude Code.")
    else:
        print("  Setup completed with errors")
    print()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
