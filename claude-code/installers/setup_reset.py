#!/usr/bin/env python3
"""
AI SDLC Method - Reset Installation Script

Performs a clean reset-style installation that:
1. Preserves user work:
   - .ai-workspace/tasks/finished/ (historical task documentation)
   - .ai-workspace/tasks/active/ (current active tasks)
2. Removes all other .ai-workspace/ and .claude/ content (templates, commands, agents)
3. Installs fresh from the specified version (tag)

This addresses stale installations that retain old folders (e.g., removed 'todo'
folder) and commands that were renamed or deleted.

Philosophy: Only immutable framework code (commands, agents, templates) is replaced.
User work (tasks) is always preserved and can roll forward/backward with versions.

# Implements: REQ-F-RESET-001 (Reset-style installation for clean updates)

Usage:
    python setup_reset.py [options]

Options:
    --target PATH       Target directory for installation (default: current)
    --version TAG       Version tag to install (default: latest)
    --source PATH       Local source instead of GitHub (for development)
    --dry-run           Show what would be done without making changes
    --no-backup         Skip backup creation (not recommended)
    --no-git            Don't update .gitignore
    --help              Show this help message

Examples:
    # Reset install with latest release
    python setup_reset.py

    # Reset install specific version
    python setup_reset.py --version v0.2.0

    # Preview changes without executing
    python setup_reset.py --dry-run

    # Use local source (development)
    python setup_reset.py --source /path/to/ai_sdlc_method
"""

import sys
import argparse
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

from common import (
    InstallerBase,
    print_banner,
    get_ai_sdlc_version,
    get_latest_release_tag
)


GITHUB_REPO_URL = "https://github.com/foolishimp/ai_sdlc_method.git"

# Directories to completely remove and reinstall
RESET_DIRECTORIES = [
    ".claude",
    ".ai-workspace"
]

# Files/directories to preserve during reset (user work that shouldn't be lost)
PRESERVE_PATHS = [
    ".ai-workspace/tasks/finished",  # Historical task documentation
    ".ai-workspace/tasks/active",    # Current active tasks
]


class ResetInstaller(InstallerBase):
    """Reset-style installer that scrubs and reinstalls cleanly."""

    def __init__(
        self,
        target: str = ".",
        version: str = None,
        source: str = None,
        dry_run: bool = False,
        no_backup: bool = False,
        no_git: bool = False
    ):
        # Don't call super().__init__ with force=True since we handle this specially
        self.target = Path(target).resolve()
        self.force = True  # Reset always forces
        self.no_git = no_git

        self.version = version
        self.source_path = Path(source).resolve() if source else None
        self.dry_run = dry_run
        self.no_backup = no_backup

        # Will be set during run()
        self.templates_root = None
        self.temp_dir = None
        self.backup_dir = None
        self.preserved_paths: List[Tuple[Path, Path]] = []

    def run(self) -> bool:
        """Execute the reset installation process."""
        print_banner()

        self.print_section("AI SDLC Method - Reset Installation")
        print(f"   Target directory: {self.target}")
        print(f"   Current version: {get_ai_sdlc_version()}")

        if self.dry_run:
            print(f"   Mode: DRY RUN (no changes will be made)")

        # Step 1: Determine version and source
        if not self._resolve_source():
            return False

        # Step 2: Validate target
        if not self._validate_target():
            return False

        # Step 3: Show what will happen
        self.print_section("Reset Plan")
        self._show_plan()

        if self.dry_run:
            self.print_section("Dry Run Complete")
            print("No changes were made. Remove --dry-run to execute.")
            return True

        # Step 4: Create backup
        if not self.no_backup:
            if not self._create_backup():
                return False

        # Step 5: Preserve important files
        if not self._preserve_files():
            return False

        # Step 6: Remove old directories
        if not self._remove_old_directories():
            self._restore_preserved()
            return False

        # Step 7: Install fresh
        if not self._install_fresh():
            self._restore_preserved()
            return False

        # Step 8: Restore preserved files
        if not self._restore_preserved():
            return False

        # Step 9: Update .gitignore
        if not self.no_git:
            self._update_gitignore()

        # Step 10: Cleanup
        self._cleanup()

        # Final summary
        self.print_section("Reset Complete")
        self._print_summary()

        return True

    def _resolve_source(self) -> bool:
        """Resolve the source for installation (local or GitHub)."""

        if self.source_path:
            # Use local source
            if not self.source_path.exists():
                self.print_error(f"Source path not found: {self.source_path}")
                return False

            self.templates_root = self.source_path / "claude-code" / "project-template"
            if not self.templates_root.exists():
                self.print_error(f"Templates not found at: {self.templates_root}")
                return False

            print(f"   Source: Local ({self.source_path})")
            print(f"   Version: {get_ai_sdlc_version()}")
            return True

        # Determine version from GitHub
        if not self.version:
            print("   Fetching latest release tag from GitHub...")
            self.version = get_latest_release_tag(GITHUB_REPO_URL)
            if not self.version:
                self.print_error("Could not determine latest release tag")
                return False

        print(f"   Source: GitHub ({GITHUB_REPO_URL})")
        print(f"   Version: {self.version}")

        if self.dry_run:
            return True

        # Clone repository at specific tag
        self.temp_dir = Path(tempfile.mkdtemp(prefix="aisdlc_reset_"))
        print(f"   Temp directory: {self.temp_dir}")

        print(f"   Cloning repository at tag {self.version}...")
        try:
            result = subprocess.run(
                [
                    "git", "clone",
                    "--depth", "1",
                    "--branch", self.version,
                    GITHUB_REPO_URL,
                    str(self.temp_dir / "ai_sdlc_method")
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                self.print_error(f"Failed to clone repository: {result.stderr}")
                return False

            self.templates_root = self.temp_dir / "ai_sdlc_method" / "claude-code" / "project-template"

            if not self.templates_root.exists():
                self.print_error(f"Templates not found in cloned repo at: {self.templates_root}")
                return False

            print(f"   Clone successful")
            return True

        except subprocess.TimeoutExpired:
            self.print_error("Clone operation timed out")
            return False
        except Exception as e:
            self.print_error(f"Clone failed: {e}")
            return False

    def _validate_target(self) -> bool:
        """Validate the target directory."""
        if not self.target.exists():
            self.print_error(f"Target directory does not exist: {self.target}")
            return False

        # Check if this looks like a valid project
        has_claude = (self.target / ".claude").exists()
        has_workspace = (self.target / ".ai-workspace").exists()

        if not has_claude and not has_workspace:
            print(f"   Warning: Target has no existing .claude or .ai-workspace")
            print(f"            This appears to be a fresh installation")

        return True

    def _show_plan(self) -> None:
        """Show what the reset will do."""
        print("\n   Will REMOVE (and reinstall fresh):")
        for dir_name in RESET_DIRECTORIES:
            dir_path = self.target / dir_name
            if dir_path.exists():
                # Count items
                if dir_path.is_dir():
                    items = list(dir_path.rglob("*"))
                    print(f"      {dir_name}/ ({len(items)} items)")
                else:
                    print(f"      {dir_name}")
            else:
                print(f"      {dir_name}/ (not present)")

        print("\n   Will PRESERVE:")
        for preserve_path in PRESERVE_PATHS:
            full_path = self.target / preserve_path
            if full_path.exists():
                if full_path.is_dir():
                    items = list(full_path.rglob("*"))
                    file_count = len([i for i in items if i.is_file()])
                    print(f"      {preserve_path}/ ({file_count} files)")
                else:
                    print(f"      {preserve_path}")
            else:
                print(f"      {preserve_path}/ (not present)")

        if self.dry_run:
            print("\n   Will INSTALL from source:")
        else:
            print("\n   Will INSTALL fresh from:")

        if self.source_path:
            print(f"      {self.templates_root}")
        else:
            print(f"      GitHub tag: {self.version}")

    def _create_backup(self) -> bool:
        """Create a backup of existing directories."""
        self.print_section("Creating Backup")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = self.target.name
        self.backup_dir = Path(tempfile.gettempdir()) / f"aisdlc-backup-{project_name}-{timestamp}"

        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            print(f"   Backup location: {self.backup_dir}")

            for dir_name in RESET_DIRECTORIES:
                source = self.target / dir_name
                if source.exists():
                    dest = self.backup_dir / dir_name
                    shutil.copytree(source, dest)
                    print(f"   Backed up: {dir_name}/")

            print(f"   Backup complete")
            return True

        except Exception as e:
            self.print_error(f"Backup failed: {e}")
            return False

    def _preserve_files(self) -> bool:
        """Preserve files that should survive the reset."""
        self.print_section("Preserving Files")

        preserve_temp = Path(tempfile.mkdtemp(prefix="aisdlc_preserve_"))

        for rel_path in PRESERVE_PATHS:
            source = self.target / rel_path
            if source.exists():
                dest = preserve_temp / rel_path
                try:
                    if source.is_dir():
                        shutil.copytree(source, dest)
                        file_count = len([f for f in source.rglob("*") if f.is_file()])
                        print(f"   Preserved: {rel_path}/ ({file_count} files)")
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, dest)
                        print(f"   Preserved: {rel_path}")

                    self.preserved_paths.append((dest, self.target / rel_path))

                except Exception as e:
                    print(f"   Warning: Could not preserve {rel_path}: {e}")
            else:
                print(f"   Skipped: {rel_path} (not present)")

        return True

    def _remove_old_directories(self) -> bool:
        """Remove old directories to be reset."""
        self.print_section("Removing Old Directories")

        for dir_name in RESET_DIRECTORIES:
            dir_path = self.target / dir_name
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    print(f"   Removed: {dir_name}/")
                except Exception as e:
                    self.print_error(f"Failed to remove {dir_name}: {e}")
                    return False
            else:
                print(f"   Skipped: {dir_name}/ (not present)")

        return True

    def _install_fresh(self) -> bool:
        """Install fresh from templates."""
        self.print_section("Installing Fresh")

        # Install .claude/
        claude_source = self.templates_root / ".claude"
        claude_target = self.target / ".claude"

        if claude_source.exists():
            try:
                shutil.copytree(claude_source, claude_target)
                cmd_count = len(list((claude_target / "commands").glob("*.md"))) if (claude_target / "commands").exists() else 0
                agent_count = len(list((claude_target / "agents").glob("*.md"))) if (claude_target / "agents").exists() else 0
                print(f"   Installed: .claude/ ({cmd_count} commands, {agent_count} agents)")
            except Exception as e:
                self.print_error(f"Failed to install .claude/: {e}")
                return False
        else:
            self.print_error(f".claude/ template not found at {claude_source}")
            return False

        # Install .ai-workspace/
        workspace_source = self.templates_root / ".ai-workspace"
        workspace_target = self.target / ".ai-workspace"

        if workspace_source.exists():
            try:
                shutil.copytree(workspace_source, workspace_target)
                print(f"   Installed: .ai-workspace/")
            except Exception as e:
                self.print_error(f"Failed to install .ai-workspace/: {e}")
                return False
        else:
            self.print_error(f".ai-workspace/ template not found at {workspace_source}")
            return False

        return True

    def _restore_preserved(self) -> bool:
        """Restore preserved files to their original locations."""
        if not self.preserved_paths:
            return True

        self.print_section("Restoring Preserved Files")

        for source, dest in self.preserved_paths:
            if source.exists():
                try:
                    # Ensure parent exists
                    dest.parent.mkdir(parents=True, exist_ok=True)

                    # Remove destination if it exists (from fresh install)
                    if dest.exists():
                        if dest.is_dir():
                            shutil.rmtree(dest)
                        else:
                            dest.unlink()

                    # Copy preserved content back
                    if source.is_dir():
                        shutil.copytree(source, dest)
                        file_count = len([f for f in dest.rglob("*") if f.is_file()])
                        print(f"   Restored: {dest.relative_to(self.target)}/ ({file_count} files)")
                    else:
                        shutil.copy2(source, dest)
                        print(f"   Restored: {dest.relative_to(self.target)}")

                except Exception as e:
                    print(f"   Warning: Could not restore {dest.relative_to(self.target)}: {e}")

        return True

    def _update_gitignore(self) -> bool:
        """Update .gitignore with standard entries."""
        entries = [
            ".ai-workspace/session/current_session.md",
            ".ai-workspace/session/history/",
            "*.backup.*",
        ]

        gitignore_path = self.target / ".gitignore"
        section_header = "# AI SDLC"

        try:
            if gitignore_path.exists():
                content = gitignore_path.read_text()
                if section_header in content:
                    return True

                if not content.endswith("\n"):
                    content += "\n"
                content += f"\n{section_header}\n"
                content += "\n".join(entries) + "\n"
                gitignore_path.write_text(content)
            else:
                content = f"{section_header}\n" + "\n".join(entries) + "\n"
                gitignore_path.write_text(content)

            return True
        except Exception as e:
            print(f"   Warning: Could not update .gitignore: {e}")
            return True  # Non-fatal

    def _cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass  # Best effort cleanup

    def _print_summary(self) -> None:
        """Print final summary."""
        print(f"\n   Reset installation complete!")
        print(f"\n   Version installed: {self.version or get_ai_sdlc_version()}")

        if self.backup_dir:
            print(f"   Backup location: {self.backup_dir}")

        print(f"\n   What was done:")
        print(f"      - Removed old .claude/ and .ai-workspace/ (framework code)")
        print(f"      - Installed fresh from {'local source' if self.source_path else f'GitHub tag {self.version}'}")
        print(f"      - Preserved .ai-workspace/tasks/active/ (your active tasks)")
        print(f"      - Preserved .ai-workspace/tasks/finished/ (your task history)")

        print(f"\n   Next steps:")
        print(f"      1. Review changes: git status")
        print(f"      2. Verify installation: ls .claude/commands/")
        print(f"      3. Commit if satisfied: git add . && git commit -m 'Reset AISDLC to {self.version or 'latest'}'")

    def print_section(self, title: str, width: int = 60):
        """Print a section header."""
        print(f"\n{'=' * width}")
        print(f" {title}")
        print('=' * width)

    def print_error(self, message: str):
        """Print an error message."""
        print(f"\n   ERROR: {message}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reset-style installation of AI SDLC Method",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reset install with latest release
  python setup_reset.py

  # Reset install specific version
  python setup_reset.py --version v0.2.0

  # Preview changes without executing
  python setup_reset.py --dry-run

  # Use local source (development)
  python setup_reset.py --source /path/to/ai_sdlc_method

  # Install to specific project
  python setup_reset.py --target /my/project --version v0.2.0
        """
    )

    parser.add_argument(
        "--target",
        help="Target directory for installation (default: current directory)",
        default="."
    )

    parser.add_argument(
        "--version",
        help="Version tag to install (default: latest release)"
    )

    parser.add_argument(
        "--source",
        help="Local source directory instead of GitHub (for development)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
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

    # Run reset installer
    installer = ResetInstaller(
        target=args.target,
        version=args.version,
        source=args.source,
        dry_run=args.dry_run,
        no_backup=args.no_backup,
        no_git=args.no_git
    )

    try:
        success = installer.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n   Reset interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n   Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
