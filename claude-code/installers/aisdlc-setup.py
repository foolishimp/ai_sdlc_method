#!/usr/bin/env python3
"""
AI SDLC Method - One-Line Project Setup

Self-contained installer that can be run directly from GitHub.

# Implements: REQ-F-PLUGIN-001 (Plugin System)

Usage:
    # From GitHub (recommended)
    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -

    # With workspace structure
    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --workspace

    # Preview changes
    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --dry-run

    # Local usage
    python aisdlc-setup.py [options]

Options:
    --target PATH       Target directory (default: current)
    --workspace         Also create .ai-workspace/ structure
    --dry-run           Preview changes without writing
    --help              Show this help

What it does:
    1. Creates .claude/settings.json with AISDLC marketplace configuration
    2. Enables the aisdlc-methodology plugin (loads from GitHub, always up to date)
    3. Plugin includes hooks that load automatically (welcome message, etc.)
    4. Optionally creates .ai-workspace/ for task tracking
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime


# =============================================================================
# Configuration
# =============================================================================

GITHUB_REPO = "foolishimp/ai_sdlc_method"

# The consolidated plugin (contains all skills, agents, commands, and hooks)
PLUGIN_NAME = "aisdlc-methodology"

# Workspace structure (optional)
WORKSPACE_STRUCTURE = {
    ".ai-workspace/tasks/active/ACTIVE_TASKS.md": """# Active Tasks

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
""",
    ".ai-workspace/tasks/finished/.gitkeep": "",
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
    # Note: Only "source" and "repo" are valid fields per Claude Code docs
    # The marketplace.json must be at .claude-plugin/marketplace.json in the repo
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
    """Create .ai-workspace/ structure."""
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    for rel_path, content in WORKSPACE_STRUCTURE.items():
        file_path = target / rel_path
        content = content.format(date=date)

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
  # Basic setup (marketplace + plugin)
  curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 -

  # With workspace structure
  curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/claude-code/installers/aisdlc-setup.py | python3 - --workspace

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
        "--workspace",
        action="store_true",
        help="Also create .ai-workspace/ structure"
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
    if args.workspace:
        print_info("Workspace: Yes")
    if args.dry_run:
        print_warning("DRY RUN - no changes will be made")
    print()

    # Run setup
    success = True

    # 1. Settings (marketplace + plugin)
    print("--- Plugin Configuration ---")
    if not setup_settings(target, args.dry_run):
        success = False
    print()

    # 2. Workspace (optional)
    if args.workspace:
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
        print("  Plugin includes:")
        print("    - 42 skills, 7 agents, 8 commands")
        print("    - Lifecycle hooks (welcome, reminders, formatting)")
    else:
        print("  Setup completed with errors")
    print()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
