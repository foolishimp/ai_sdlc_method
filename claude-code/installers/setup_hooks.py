#!/usr/bin/env python3
"""
AI SDLC Method - Hooks Setup Script

Installs AISDLC lifecycle hooks into Claude Code's settings.json.

# Implements: REQ-F-HOOKS-001 (Lifecycle hooks for methodology automation)
# Implements: REQ-NFR-CONTEXT-001 (Persistent context across sessions)

This installer:
1. Reads hook definitions from aisdlc-methodology/hooks/settings.json
2. Merges them into ~/.claude/settings.json (or project .claude/settings.json)
3. Preserves existing non-AISDLC hooks
4. Creates backup before modification

Usage:
    python setup_hooks.py [options]

Options:
    --global                Install to ~/.claude/settings.json (default)
    --project               Install to .claude/settings.json in current dir
    --target PATH           Install to specific project directory
    --dry-run               Preview changes without writing
    --force                 Overwrite existing AISDLC hooks
    --remove                Remove AISDLC hooks
    --help                  Show this help message

Examples:
    # Install hooks globally (recommended)
    python setup_hooks.py --global

    # Install to specific project
    python setup_hooks.py --project --target /my/project

    # Preview changes
    python setup_hooks.py --dry-run

    # Remove AISDLC hooks
    python setup_hooks.py --remove
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from common import InstallerBase, print_banner


class HooksSetup(InstallerBase):
    """Setup Claude Code hooks for AISDLC methodology automation."""

    def __init__(
        self,
        target: str = ".",
        global_install: bool = True,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False
    ):
        super().__init__(target, force)
        self.global_install = global_install
        self.dry_run = dry_run
        self.remove = remove

        # Source hooks file (in methodology plugin)
        self.hooks_source = self.methodology_plugin / "hooks" / "settings.json"

        # Target settings file
        if global_install:
            self.settings_file = Path.home() / ".claude" / "settings.json"
        else:
            self.settings_file = self.target / ".claude" / "settings.json"

    def run(self) -> bool:
        """Execute the hooks setup process."""
        self.print_section("AI SDLC Hooks Installation")

        location = "global (~/.claude)" if self.global_install else f"project ({self.target})"
        print(f"📁 Target: {location}")
        print(f"📄 Settings: {self.settings_file}")

        if self.remove:
            print("🗑️  Mode: REMOVE AISDLC hooks")
        elif self.dry_run:
            print("🔍 Mode: DRY RUN (no changes will be made)")

        # Load source hooks
        if not self.remove:
            source_hooks = self._load_source_hooks()
            if source_hooks is None:
                return False

        # Load existing settings
        existing_settings = self._load_existing_settings()

        # Process hooks
        if self.remove:
            new_settings = self._remove_aisdlc_hooks(existing_settings)
        else:
            new_settings = self._merge_hooks(existing_settings, source_hooks)

        # Show changes
        self._show_changes(existing_settings, new_settings)

        if self.dry_run:
            print("\n🔍 Dry run complete - no changes made")
            return True

        # Write settings
        return self._write_settings(new_settings)

    def _load_source_hooks(self) -> Optional[Dict[str, Any]]:
        """Load hook definitions from methodology plugin."""
        if not self.hooks_source.exists():
            self.print_error(f"Hooks source not found: {self.hooks_source}")
            print(f"   Make sure you're running from the ai_sdlc_method directory")
            return None

        try:
            with open(self.hooks_source, 'r') as f:
                data = json.load(f)
                return data.get("hooks", {})
        except json.JSONDecodeError as e:
            self.print_error(f"Invalid JSON in hooks source: {e}")
            return None
        except Exception as e:
            self.print_error(f"Error reading hooks source: {e}")
            return None

    def _load_existing_settings(self) -> Dict[str, Any]:
        """Load existing settings.json or return empty dict."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"⚠️  Warning: Existing settings.json has invalid JSON: {e}")
                print("   Will create backup and start fresh")
                return {}
            except Exception as e:
                print(f"⚠️  Warning: Could not read settings.json: {e}")
                return {}
        return {}

    def _merge_hooks(
        self,
        existing: Dict[str, Any],
        new_hooks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge AISDLC hooks into existing settings."""
        result = existing.copy()

        # Initialize hooks section if needed
        if "hooks" not in result:
            result["hooks"] = {}

        # For each hook type in our source
        for hook_type, hook_configs in new_hooks.items():
            if hook_type not in result["hooks"]:
                result["hooks"][hook_type] = []

            # Check if AISDLC hooks already exist
            existing_hooks = result["hooks"][hook_type]
            aisdlc_indices = self._find_aisdlc_hook_indices(existing_hooks)

            if aisdlc_indices and not self.force:
                print(f"\n⚠️  Existing AISDLC hooks found in {hook_type}")
                print("   Use --force to overwrite")
                continue
            elif aisdlc_indices:
                # Remove existing AISDLC hooks (in reverse order to maintain indices)
                for idx in sorted(aisdlc_indices, reverse=True):
                    del result["hooks"][hook_type][idx]

            # Add new AISDLC hooks with marker
            for hook_config in hook_configs:
                # Add AISDLC marker to command for identification
                marked_config = self._add_aisdlc_marker(hook_config)
                result["hooks"][hook_type].append(marked_config)

        return result

    def _remove_aisdlc_hooks(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Remove all AISDLC hooks from settings."""
        result = settings.copy()

        if "hooks" not in result:
            print("ℹ️  No hooks found in settings")
            return result

        removed_count = 0
        for hook_type in list(result["hooks"].keys()):
            hooks_list = result["hooks"][hook_type]
            aisdlc_indices = self._find_aisdlc_hook_indices(hooks_list)

            # Remove AISDLC hooks (in reverse order)
            for idx in sorted(aisdlc_indices, reverse=True):
                del result["hooks"][hook_type][idx]
                removed_count += 1

            # Remove empty hook type
            if not result["hooks"][hook_type]:
                del result["hooks"][hook_type]

        # Remove empty hooks section
        if not result["hooks"]:
            del result["hooks"]

        print(f"🗑️  Removed {removed_count} AISDLC hook(s)")
        return result

    def _find_aisdlc_hook_indices(self, hooks_list: list) -> list:
        """Find indices of AISDLC hooks in a hooks list."""
        indices = []
        for i, hook in enumerate(hooks_list):
            if self._is_aisdlc_hook(hook):
                indices.append(i)
        return indices

    def _is_aisdlc_hook(self, hook: dict) -> bool:
        """Check if a hook is an AISDLC hook."""
        # Check for AISDLC marker in command
        for sub_hook in hook.get("hooks", []):
            command = sub_hook.get("command", "")
            if "AISDLC" in command or ".ai-workspace" in command:
                return True
        return False

    def _add_aisdlc_marker(self, hook_config: dict) -> dict:
        """Add AISDLC marker comment to hook command for identification."""
        result = hook_config.copy()
        if "hooks" in result:
            result["hooks"] = []
            for sub_hook in hook_config["hooks"]:
                new_sub = sub_hook.copy()
                if "command" in new_sub:
                    # Add marker if not present
                    if "# AISDLC" not in new_sub["command"]:
                        new_sub["command"] = f"# AISDLC hook\n{new_sub['command']}"
                result["hooks"].append(new_sub)
        return result

    def _show_changes(self, old: Dict[str, Any], new: Dict[str, Any]):
        """Show what changes will be made."""
        print("\n📝 Hook Configuration:")
        print("-" * 50)

        if self.remove:
            old_hooks = old.get("hooks", {})
            new_hooks = new.get("hooks", {})

            for hook_type in set(list(old_hooks.keys()) + list(new_hooks.keys())):
                old_count = len(old_hooks.get(hook_type, []))
                new_count = len(new_hooks.get(hook_type, []))
                if old_count != new_count:
                    print(f"   {hook_type}: {old_count} → {new_count}")
        else:
            hooks = new.get("hooks", {})
            for hook_type, hook_configs in hooks.items():
                aisdlc_count = len(self._find_aisdlc_hook_indices(hook_configs))
                total_count = len(hook_configs)
                print(f"   {hook_type}: {aisdlc_count} AISDLC / {total_count} total")

    def _write_settings(self, settings: Dict[str, Any]) -> bool:
        """Write settings to file."""
        try:
            # Ensure .claude directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            # Backup existing if present
            if self.settings_file.exists():
                backup_path = self.backup_file(self.settings_file)
                if backup_path:
                    print(f"📋 Backed up to: {backup_path}")

            # Write new settings
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            print(f"\n✅ Settings written to: {self.settings_file}")

            self._print_summary()
            return True

        except Exception as e:
            self.print_error(f"Failed to write settings: {e}")
            return False

    def _print_summary(self):
        """Print summary of what was installed."""
        if self.remove:
            print("\n🗑️  AISDLC hooks removed")
        else:
            print("\n✅ AISDLC Hooks Installed:")
            print("   • SessionStart - Auto-load context on session start")
            print("   • Stop - Checkpoint reminder after work")
            print("   • PreToolUse - REQ tag validation on commits")
            print("   • PostToolUse - Auto-formatting on edits")

        print("\n📚 Next Steps:")
        print("   1. Restart Claude Code to activate hooks")
        print("   2. Start a new session to see hooks in action")
        if not self.remove:
            print("   3. Run /aisdlc-status to verify context loaded")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Install AISDLC lifecycle hooks into Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install hooks globally (recommended)
  python setup_hooks.py --global

  # Install to current project
  python setup_hooks.py --project

  # Preview changes
  python setup_hooks.py --dry-run

  # Remove AISDLC hooks
  python setup_hooks.py --remove
        """
    )

    location_group = parser.add_mutually_exclusive_group()
    location_group.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        default=True,
        help="Install to ~/.claude/settings.json (default)"
    )
    location_group.add_argument(
        "--project",
        dest="project_install",
        action="store_true",
        help="Install to .claude/settings.json in target directory"
    )

    parser.add_argument(
        "--target",
        help="Target project directory (default: current)",
        default="."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing AISDLC hooks"
    )

    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove AISDLC hooks instead of installing"
    )

    args = parser.parse_args()

    # Determine installation location
    global_install = not args.project_install

    # Print banner
    print_banner()

    # Create setup instance
    setup = HooksSetup(
        target=args.target,
        global_install=global_install,
        dry_run=args.dry_run,
        force=args.force,
        remove=args.remove
    )

    try:
        success = setup.run()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
