#!/usr/bin/env python3
"""
AI SDLC Method - Self-Contained Reset Installer

A single-file installer that can be run directly via curl:

    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 -

Or with arguments:

    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --version v0.2.0
    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --dry-run

What it does:
1. Clones ai_sdlc_method repo at specified tag (or latest) to temp directory
2. Preserves your work:
   - .ai-workspace/tasks/active/ (current tasks)
   - .ai-workspace/tasks/finished/ (task history)
3. Removes and reinstalls framework code:
   - .claude/commands/
   - .claude/agents/
   - .ai-workspace/templates/
   - .ai-workspace/config/
4. Cleans up temp directory

Philosophy: Only immutable framework code is replaced. Your work is always preserved.
"""

import sys
import os
import argparse
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple


GITHUB_REPO_URL = "https://github.com/foolishimp/ai_sdlc_method.git"

# Directories to completely remove and reinstall
RESET_DIRECTORIES = [".claude", ".ai-workspace"]

# Paths to preserve (user work)
PRESERVE_PATHS = [
    ".ai-workspace/tasks/finished",
    ".ai-workspace/tasks/active",
]


def print_banner(version: str = "latest"):
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        AI SDLC Method - Self-Contained Reset Installer       ║
║                                                              ║
║                    Target Version: {version:<10}              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def print_section(title: str):
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print('=' * 60)


def get_latest_tag() -> Optional[str]:
    """Fetch latest release tag from GitHub."""
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--tags", "--sort=-version:refname", GITHUB_REPO_URL],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line and 'refs/tags/' in line:
                    tag = line.split('refs/tags/')[-1]
                    if not tag.endswith('^{}'):
                        return tag
        return None
    except Exception as e:
        print(f"   Warning: Could not fetch tags: {e}")
        return None


def clone_repo(version: str, temp_dir: Path) -> Optional[Path]:
    """Clone the repository at specified version."""
    clone_path = temp_dir / "ai_sdlc_method"

    print(f"   Cloning {GITHUB_REPO_URL}")
    print(f"   Version: {version}")

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", version,
             GITHUB_REPO_URL, str(clone_path)],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            print(f"   Error: Clone failed: {result.stderr}")
            return None

        return clone_path
    except subprocess.TimeoutExpired:
        print("   Error: Clone timed out")
        return None
    except Exception as e:
        print(f"   Error: {e}")
        return None


def preserve_files(target: Path, temp_preserve: Path) -> List[Tuple[Path, Path]]:
    """Preserve user work files."""
    preserved = []

    for rel_path in PRESERVE_PATHS:
        source = target / rel_path
        if source.exists():
            dest = temp_preserve / rel_path
            try:
                if source.is_dir():
                    shutil.copytree(source, dest)
                    file_count = len([f for f in source.rglob("*") if f.is_file()])
                    print(f"   Preserved: {rel_path}/ ({file_count} files)")
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
                    print(f"   Preserved: {rel_path}")
                preserved.append((dest, target / rel_path))
            except Exception as e:
                print(f"   Warning: Could not preserve {rel_path}: {e}")
        else:
            print(f"   Skipped: {rel_path} (not present)")

    return preserved


def remove_directories(target: Path):
    """Remove directories to be reset."""
    for dir_name in RESET_DIRECTORIES:
        dir_path = target / dir_name
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"   Removed: {dir_name}/")
            except Exception as e:
                print(f"   Error removing {dir_name}: {e}")
                return False
        else:
            print(f"   Skipped: {dir_name}/ (not present)")
    return True


def install_fresh(templates_root: Path, target: Path) -> bool:
    """Install fresh framework files."""

    # Install .claude/
    claude_source = templates_root / ".claude"
    claude_target = target / ".claude"

    if claude_source.exists():
        try:
            shutil.copytree(claude_source, claude_target)
            cmd_count = len(list((claude_target / "commands").glob("*.md"))) if (claude_target / "commands").exists() else 0
            agent_count = len(list((claude_target / "agents").glob("*.md"))) if (claude_target / "agents").exists() else 0
            print(f"   Installed: .claude/ ({cmd_count} commands, {agent_count} agents)")
        except Exception as e:
            print(f"   Error installing .claude/: {e}")
            return False
    else:
        print(f"   Error: .claude/ template not found")
        return False

    # Install .ai-workspace/
    workspace_source = templates_root / ".ai-workspace"
    workspace_target = target / ".ai-workspace"

    if workspace_source.exists():
        try:
            shutil.copytree(workspace_source, workspace_target)
            print(f"   Installed: .ai-workspace/")
        except Exception as e:
            print(f"   Error installing .ai-workspace/: {e}")
            return False
    else:
        print(f"   Error: .ai-workspace/ template not found")
        return False

    return True


def restore_preserved(preserved: List[Tuple[Path, Path]], target: Path):
    """Restore preserved files."""
    for source, dest in preserved:
        if source.exists():
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()

                if source.is_dir():
                    shutil.copytree(source, dest)
                    file_count = len([f for f in dest.rglob("*") if f.is_file()])
                    print(f"   Restored: {dest.relative_to(target)}/ ({file_count} files)")
                else:
                    shutil.copy2(source, dest)
                    print(f"   Restored: {dest.relative_to(target)}")
            except Exception as e:
                print(f"   Warning: Could not restore {dest.relative_to(target)}: {e}")


def create_backup(target: Path) -> Optional[Path]:
    """Create backup of existing directories."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = target.name
    backup_dir = Path(tempfile.gettempdir()) / f"aisdlc-backup-{project_name}-{timestamp}"

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        for dir_name in RESET_DIRECTORIES:
            source = target / dir_name
            if source.exists():
                shutil.copytree(source, backup_dir / dir_name)
                print(f"   Backed up: {dir_name}/")
        return backup_dir
    except Exception as e:
        print(f"   Warning: Backup failed: {e}")
        return None


def show_plan(target: Path, version: str):
    """Show what will be done (dry run)."""
    print("\n   Will REMOVE (and reinstall fresh):")
    for dir_name in RESET_DIRECTORIES:
        dir_path = target / dir_name
        if dir_path.exists() and dir_path.is_dir():
            items = list(dir_path.rglob("*"))
            print(f"      {dir_name}/ ({len(items)} items)")
        else:
            print(f"      {dir_name}/ (not present)")

    print("\n   Will PRESERVE:")
    for preserve_path in PRESERVE_PATHS:
        full_path = target / preserve_path
        if full_path.exists():
            if full_path.is_dir():
                file_count = len([f for f in full_path.rglob("*") if f.is_file()])
                print(f"      {preserve_path}/ ({file_count} files)")
            else:
                print(f"      {preserve_path}")
        else:
            print(f"      {preserve_path}/ (not present)")

    print(f"\n   Will INSTALL from: GitHub tag {version}")


def main():
    parser = argparse.ArgumentParser(
        description="Self-contained reset installer for AI SDLC Method",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Via curl (latest version)
  curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 -

  # Via curl (specific version)
  curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --version v0.2.0

  # Dry run
  curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/installers/aisdlc-reset.py | python3 - --dry-run

  # Or download and run locally
  python3 aisdlc-reset.py --version v0.2.0
        """
    )

    parser.add_argument("--target", default=".", help="Target directory (default: current)")
    parser.add_argument("--version", help="Version tag to install (default: latest)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")

    args = parser.parse_args()

    target = Path(args.target).resolve()

    # Determine version
    version = args.version
    if not version:
        print("Fetching latest release tag...")
        version = get_latest_tag()
        if not version:
            print("Error: Could not determine latest version. Specify with --version")
            sys.exit(1)

    print_banner(version)

    print_section("Reset Installation")
    print(f"   Target: {target}")
    print(f"   Version: {version}")

    if args.dry_run:
        print(f"   Mode: DRY RUN")

    # Validate target
    if not target.exists():
        print(f"\n   Error: Target directory does not exist: {target}")
        sys.exit(1)

    # Dry run - just show plan
    if args.dry_run:
        print_section("Reset Plan")
        show_plan(target, version)
        print_section("Dry Run Complete")
        print("No changes were made. Remove --dry-run to execute.")
        sys.exit(0)

    # Create temp directories
    temp_dir = Path(tempfile.mkdtemp(prefix="aisdlc_reset_"))
    temp_preserve = Path(tempfile.mkdtemp(prefix="aisdlc_preserve_"))

    try:
        # Backup
        backup_dir = None
        if not args.no_backup:
            print_section("Creating Backup")
            backup_dir = create_backup(target)

        # Clone repo
        print_section("Fetching Framework")
        repo_path = clone_repo(version, temp_dir)
        if not repo_path:
            sys.exit(1)

        templates_root = repo_path / "claude-code" / "project-template"
        if not templates_root.exists():
            print(f"   Error: Templates not found at {templates_root}")
            sys.exit(1)

        # Preserve user work
        print_section("Preserving User Work")
        preserved = preserve_files(target, temp_preserve)

        # Remove old directories
        print_section("Removing Old Framework")
        if not remove_directories(target):
            sys.exit(1)

        # Install fresh
        print_section("Installing Fresh Framework")
        if not install_fresh(templates_root, target):
            sys.exit(1)

        # Restore preserved
        if preserved:
            print_section("Restoring User Work")
            restore_preserved(preserved, target)

        # Summary
        print_section("Reset Complete")
        print(f"\n   Version installed: {version}")
        if backup_dir:
            print(f"   Backup location: {backup_dir}")
        print(f"\n   What was done:")
        print(f"      - Removed old .claude/ and .ai-workspace/")
        print(f"      - Installed fresh from GitHub tag {version}")
        print(f"      - Preserved .ai-workspace/tasks/active/")
        print(f"      - Preserved .ai-workspace/tasks/finished/")
        print(f"\n   Next steps:")
        print(f"      1. Review changes: git status")
        print(f"      2. Verify: ls .claude/commands/")
        print(f"      3. Commit: git add . && git commit -m 'Reset AISDLC to {version}'")

    finally:
        # Cleanup temp directories
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        if temp_preserve.exists():
            shutil.rmtree(temp_preserve, ignore_errors=True)


if __name__ == "__main__":
    main()
