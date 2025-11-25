#!/usr/bin/env python3
"""
Roo Code AISDLC - Reset Installation

Performs a clean reset-style installation that addresses stale files
from previous versions while preserving user work.

Philosophy:
- Only immutable framework code (modes, rules, templates) is replaced
- User work (tasks, memory bank) is always preserved
- Can roll forward/backward with versions

PRESERVED:
- .ai-workspace/tasks/active/      - Your current active tasks
- .ai-workspace/tasks/finished/    - Your completed task documentation
- .roo/memory-bank/                - Your project context (user data)

REMOVED & REINSTALLED:
- .roo/modes/                      - All custom modes (fresh from version)
- .roo/rules/                      - All rules (fresh from version)
- .ai-workspace/templates/         - All templates (fresh from version)
- .ai-workspace/config/            - Configuration (fresh from version)

Usage:
    python setup_reset.py [options]

Options:
    --target PATH     Target directory (default: current)
    --source PATH     Use local source instead of templates
    --version TAG     Version tag to install (default: latest)
    --dry-run         Show plan without making changes
    --no-backup       Skip backup creation (not recommended)
    --no-git          Don't update .gitignore
"""

import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime

from common import RooInstallerBase, print_banner, get_ai_sdlc_version


class ResetInstaller(RooInstallerBase):
    """Reset-style installer that cleans and reinstalls framework files."""

    # Paths to preserve (user data)
    PRESERVE_PATHS = [
        ".ai-workspace/tasks/active",
        ".ai-workspace/tasks/finished",
        ".roo/memory-bank",
    ]

    # Paths to remove and reinstall (framework files)
    RESET_PATHS = [
        ".roo/modes",
        ".roo/rules",
        ".ai-workspace/templates",
        ".ai-workspace/config",
    ]

    def __init__(self, target: str = ".", source: str = None,
                 version: str = None, dry_run: bool = False,
                 no_backup: bool = False, no_git: bool = False):
        super().__init__(target, force=True, no_git=no_git)

        self.source = Path(source) if source else self.templates_root
        self.version = version or get_ai_sdlc_version()
        self.dry_run = dry_run
        self.no_backup = no_backup
        self.backup_dir = None

    def _validate_source(self) -> bool:
        """Validate that source directory exists and has expected structure."""
        if not self.source.exists():
            self.print_error(f"Source path not found: {self.source}")
            return False

        # Check for expected directories (at least one should exist)
        modes_dir = self.source / "roo" / "modes"
        rules_dir = self.source / "roo" / "rules"
        templates_dir = self.source / ".ai-workspace" / "templates"

        has_content = modes_dir.exists() or rules_dir.exists() or templates_dir.exists()
        if not has_content:
            self.print_error(f"Source has no installable content: {self.source}")
            self.print_error("Expected: roo/modes/, roo/rules/, or .ai-workspace/templates/")
            return False

        return True

    def run(self) -> bool:
        """Execute reset installation."""
        print_banner("Roo Code AISDLC Reset")

        self.print_section("Reset Installation")
        print(f"📁 Target: {self.target}")
        print(f"📁 Source: {self.source}")
        print(f"🔖 Version: {self.version}")
        print(f"🔍 Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")

        # Validate target
        if not self.validate_target():
            return False

        # Validate source
        if not self._validate_source():
            return False

        # Show plan
        self.print_section("Reset Plan")
        self._print_plan()

        if self.dry_run:
            self.print_success("Dry run complete - no changes made")
            return True

        # Create backup
        if not self.no_backup:
            self.print_section("Creating Backup")
            if not self._create_backup():
                self.print_error("Backup failed - aborting reset")
                return False

        # Execute reset
        self.print_section("Removing Stale Files")
        if not self._remove_reset_paths():
            self.print_error("Failed to remove some paths")
            # Continue anyway - some paths might not exist

        self.print_section("Installing Fresh Files")
        success = self._install_fresh()

        # Verify preserved paths
        self.print_section("Verifying Preserved Data")
        self._verify_preserved()

        # Summary
        self.print_section("Reset Summary")
        if success:
            self.print_success("Reset installation complete!")
            print(f"\n📋 Backup location: {self.backup_dir}")
            print("\n💡 Your tasks and memory bank were preserved")
            print("   Framework files (modes, rules, templates) are now fresh")
        else:
            self.print_error("Reset completed with some errors")
            if self.backup_dir:
                print(f"\n📋 Restore from backup: {self.backup_dir}")

        return success

    def _print_plan(self):
        """Print what will be done."""
        print("\n🔒 PRESERVED (user data):")
        for path in self.PRESERVE_PATHS:
            full_path = self.target / path
            exists = "✓" if full_path.exists() else "○"
            print(f"   {exists} {path}")

        print("\n🗑️  REMOVED & REINSTALLED (framework):")
        for path in self.RESET_PATHS:
            full_path = self.target / path
            exists = "✓" if full_path.exists() else "○"
            print(f"   {exists} {path}")

        print("\n📄 CREATED/UPDATED:")
        print("   ○ ROOCODE.md")

    def _create_backup(self) -> bool:
        """Create backup of current installation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = self.target.name
        self.backup_dir = Path("/tmp") / f"aisdlc-roo-backup-{project_name}-{timestamp}"

        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup .roo/
            roo_dir = self.target / ".roo"
            if roo_dir.exists():
                shutil.copytree(roo_dir, self.backup_dir / ".roo")
                print(f"✅ Backed up: .roo/")

            # Backup .ai-workspace/
            workspace_dir = self.target / ".ai-workspace"
            if workspace_dir.exists():
                shutil.copytree(workspace_dir, self.backup_dir / ".ai-workspace")
                print(f"✅ Backed up: .ai-workspace/")

            # Backup ROOCODE.md
            roocode_md = self.target / "ROOCODE.md"
            if roocode_md.exists():
                shutil.copy2(roocode_md, self.backup_dir / "ROOCODE.md")
                print(f"✅ Backed up: ROOCODE.md")

            print(f"\n📋 Backup created at: {self.backup_dir}")
            return True

        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False

    def _remove_reset_paths(self) -> bool:
        """Remove paths that will be reinstalled."""
        success = True

        for path in self.RESET_PATHS:
            full_path = self.target / path
            if full_path.exists():
                try:
                    if full_path.is_dir():
                        shutil.rmtree(full_path)
                    else:
                        full_path.unlink()
                    print(f"🗑️  Removed: {path}")
                except Exception as e:
                    print(f"⚠️  Could not remove {path}: {e}")
                    success = False

        return success

    def _install_fresh(self) -> bool:
        """Install fresh framework files from source."""
        success = True

        # Install modes
        modes_src = self.source / "roo" / "modes"
        modes_dst = self.target / ".roo" / "modes"
        if modes_src.exists():
            success &= self.copy_directory(modes_src, modes_dst, ".roo/modes")

        # Install rules
        rules_src = self.source / "roo" / "rules"
        rules_dst = self.target / ".roo" / "rules"
        if rules_src.exists():
            success &= self.copy_directory(rules_src, rules_dst, ".roo/rules")

        # Install workspace templates
        templates_src = self.source / ".ai-workspace" / "templates"
        templates_dst = self.target / ".ai-workspace" / "templates"
        if templates_src.exists():
            success &= self.copy_directory(templates_src, templates_dst, ".ai-workspace/templates")

        # Install workspace config
        config_src = self.source / ".ai-workspace" / "config"
        config_dst = self.target / ".ai-workspace" / "config"
        if config_src.exists():
            success &= self.copy_directory(config_src, config_dst, ".ai-workspace/config")

        # Ensure preserved directories exist
        for path in self.PRESERVE_PATHS:
            full_path = self.target / path
            full_path.mkdir(parents=True, exist_ok=True)

        # Update ROOCODE.md
        roocode_src = self.source / "ROOCODE.md"
        roocode_dst = self.target / "ROOCODE.md"
        if roocode_src.exists():
            success &= self.copy_file(roocode_src, roocode_dst, "ROOCODE.md")

        return success

    def _verify_preserved(self):
        """Verify that preserved paths still exist."""
        all_preserved = True

        for path in self.PRESERVE_PATHS:
            full_path = self.target / path
            if full_path.exists():
                print(f"✅ Preserved: {path}")
            else:
                print(f"⚠️  Missing: {path} (creating empty)")
                full_path.mkdir(parents=True, exist_ok=True)
                all_preserved = False

        return all_preserved


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reset Roo Code AISDLC installation (clean slate, preserves tasks)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reset current directory
  python setup_reset.py

  # Reset specific project
  python setup_reset.py --target /my/project

  # Preview changes (dry run)
  python setup_reset.py --dry-run

  # Use local source instead of GitHub
  python setup_reset.py --source /path/to/ai_sdlc_method/roo-code-iclaude/project-template

What gets PRESERVED (user data):
  - .ai-workspace/tasks/active/    - Your current tasks
  - .ai-workspace/tasks/finished/  - Your completed task docs
  - .roo/memory-bank/              - Your project context

What gets REMOVED and reinstalled (framework):
  - .roo/modes/                    - Custom modes
  - .roo/rules/                    - Methodology rules
  - .ai-workspace/templates/       - Task templates
  - .ai-workspace/config/          - Configuration
        """
    )

    parser.add_argument(
        "--target",
        help="Target directory (default: current)",
        default="."
    )

    parser.add_argument(
        "--source",
        help="Use local source instead of templates"
    )

    parser.add_argument(
        "--version",
        help="Version tag to install (default: latest)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show plan without making changes"
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup creation (not recommended)"
    )

    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Don't update .gitignore"
    )

    args = parser.parse_args()

    installer = ResetInstaller(
        target=args.target,
        source=args.source,
        version=args.version,
        dry_run=args.dry_run,
        no_backup=args.no_backup,
        no_git=args.no_git
    )

    try:
        success = installer.run()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Reset interrupted")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
