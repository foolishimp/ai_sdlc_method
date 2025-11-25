#!/usr/bin/env python3
"""
Roo Code AISDLC - Self-Contained Reset Installer

A single-file installer that can be run directly via curl - no clone required.
Downloads and installs the AISDLC framework for Roo Code.

Usage:
    # Latest version
    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py | python3 -

    # Specific version
    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py | python3 - --version v0.3.0

    # Dry run
    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py | python3 - --dry-run

    # Or download and run locally
    curl -O https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py
    python3 aisdlc-reset.py --version v0.3.0

Options:
    --target PATH     Target directory (default: current)
    --version TAG     Version tag to install (default: latest)
    --dry-run         Show plan without making changes
    --no-backup       Skip backup creation

This installer:
1. Downloads the specified version from GitHub
2. Backs up existing installation
3. Removes stale framework files
4. Installs fresh framework files
5. Preserves user data (tasks, memory bank)
"""

import sys
import os
import argparse
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional
from urllib.request import urlopen
from urllib.error import URLError
import zipfile
import io


# GitHub repository
GITHUB_REPO = "foolishimp/ai_sdlc_method"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}"
GITHUB_RAW = f"https://raw.githubusercontent.com/{GITHUB_REPO}"

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


def print_banner(version: str = "unknown"):
    """Print installer banner."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           Roo Code AISDLC - Self-Contained Reset             ║
║                                                              ║
║                    Version {version:<10}                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def get_latest_release() -> Optional[str]:
    """Get the latest release tag from GitHub."""
    try:
        import json
        url = f"{GITHUB_API}/releases/latest"
        with urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            return data.get("tag_name")
    except Exception as e:
        print(f"⚠️  Could not fetch latest release: {e}")
        return None


def download_release(version: str, dest_dir: Path) -> bool:
    """Download and extract a release from GitHub."""
    try:
        # Download zip archive
        url = f"https://github.com/{GITHUB_REPO}/archive/refs/tags/{version}.zip"
        print(f"📥 Downloading {version} from GitHub...")

        with urlopen(url, timeout=60) as response:
            zip_data = response.read()

        # Extract to destination
        print(f"📦 Extracting...")
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            zf.extractall(dest_dir)

        # Find extracted directory (ai_sdlc_method-v0.3.0 or similar)
        extracted = list(dest_dir.iterdir())
        if extracted:
            # Return path to roo-code-iclaude/project-template
            return extracted[0] / "roo-code-iclaude" / "project-template"

        return None
    except URLError as e:
        print(f"❌ Download failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def create_backup(target: Path) -> Optional[Path]:
    """Create backup of current installation."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = target.name
    backup_dir = Path("/tmp") / f"aisdlc-roo-backup-{project_name}-{timestamp}"

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup .roo/
        roo_dir = target / ".roo"
        if roo_dir.exists():
            shutil.copytree(roo_dir, backup_dir / ".roo")
            print(f"✅ Backed up: .roo/")

        # Backup .ai-workspace/
        workspace_dir = target / ".ai-workspace"
        if workspace_dir.exists():
            shutil.copytree(workspace_dir, backup_dir / ".ai-workspace")
            print(f"✅ Backed up: .ai-workspace/")

        # Backup ROOCODE.md
        roocode_md = target / "ROOCODE.md"
        if roocode_md.exists():
            shutil.copy2(roocode_md, backup_dir / "ROOCODE.md")
            print(f"✅ Backed up: ROOCODE.md")

        print(f"📋 Backup created at: {backup_dir}")
        return backup_dir

    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None


def remove_reset_paths(target: Path) -> bool:
    """Remove paths that will be reinstalled."""
    success = True

    for path in RESET_PATHS:
        full_path = target / path
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


def install_fresh(source: Path, target: Path) -> bool:
    """Install fresh framework files from source."""
    success = True

    def copy_dir(src_name: str, dst_name: str, desc: str) -> bool:
        src = source / src_name
        dst = target / dst_name
        if src.exists():
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"✅ Installed: {desc}")
                return True
            except Exception as e:
                print(f"❌ Failed to install {desc}: {e}")
                return False
        else:
            print(f"⚠️  Source not found: {src_name}")
            return False

    # Install modes
    success &= copy_dir("roo/modes", ".roo/modes", ".roo/modes")

    # Install rules
    success &= copy_dir("roo/rules", ".roo/rules", ".roo/rules")

    # Install workspace templates
    success &= copy_dir(".ai-workspace/templates", ".ai-workspace/templates", ".ai-workspace/templates")

    # Install workspace config
    success &= copy_dir(".ai-workspace/config", ".ai-workspace/config", ".ai-workspace/config")

    # Ensure preserved directories exist
    for path in PRESERVE_PATHS:
        full_path = target / path
        full_path.mkdir(parents=True, exist_ok=True)

    # Copy ROOCODE.md
    roocode_src = source / "ROOCODE.md"
    roocode_dst = target / "ROOCODE.md"
    if roocode_src.exists():
        try:
            shutil.copy2(roocode_src, roocode_dst)
            print(f"✅ Installed: ROOCODE.md")
        except Exception as e:
            print(f"⚠️  Could not copy ROOCODE.md: {e}")

    return success


def verify_preserved(target: Path) -> bool:
    """Verify that preserved paths still exist."""
    all_preserved = True

    for path in PRESERVE_PATHS:
        full_path = target / path
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
        description="Self-contained Roo Code AISDLC reset installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install latest version
  python aisdlc-reset.py

  # Install specific version
  python aisdlc-reset.py --version v0.3.0

  # Preview changes
  python aisdlc-reset.py --dry-run

  # Via curl (no download needed)
  curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/roo-code-iclaude/installers/aisdlc-reset.py | python3 -
        """
    )

    parser.add_argument(
        "--target",
        help="Target directory (default: current)",
        default="."
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
        help="Skip backup creation"
    )

    args = parser.parse_args()

    target = Path(args.target).resolve()

    # Get version
    version = args.version
    if not version:
        print("🔍 Fetching latest release...")
        version = get_latest_release()
        if not version:
            print("❌ Could not determine latest version")
            print("   Try specifying --version explicitly")
            return 1

    print_banner(version)

    print(f"📁 Target: {target}")
    print(f"🔖 Version: {version}")
    print(f"🔍 Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")

    # Show plan
    print("\n" + "=" * 60)
    print("Reset Plan")
    print("=" * 60)

    print("\n🔒 PRESERVED (user data):")
    for path in PRESERVE_PATHS:
        full_path = target / path
        exists = "✓" if full_path.exists() else "○"
        print(f"   {exists} {path}")

    print("\n🗑️  REMOVED & REINSTALLED (framework):")
    for path in RESET_PATHS:
        full_path = target / path
        exists = "✓" if full_path.exists() else "○"
        print(f"   {exists} {path}")

    if args.dry_run:
        print("\n✅ Dry run complete - no changes made")
        return 0

    # Download release
    print("\n" + "=" * 60)
    print("Downloading Release")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        source = download_release(version, Path(temp_dir))
        if not source:
            print("❌ Failed to download release")
            return 1

        # Create backup
        if not args.no_backup:
            print("\n" + "=" * 60)
            print("Creating Backup")
            print("=" * 60)
            backup_dir = create_backup(target)
            if not backup_dir:
                print("❌ Backup failed - aborting")
                return 1

        # Remove stale files
        print("\n" + "=" * 60)
        print("Removing Stale Files")
        print("=" * 60)
        remove_reset_paths(target)

        # Install fresh
        print("\n" + "=" * 60)
        print("Installing Fresh Files")
        print("=" * 60)
        success = install_fresh(source, target)

        # Verify preserved
        print("\n" + "=" * 60)
        print("Verifying Preserved Data")
        print("=" * 60)
        verify_preserved(target)

    # Summary
    print("\n" + "=" * 60)
    print("Reset Summary")
    print("=" * 60)

    if success:
        print("\n✅ Roo Code AISDLC reset complete!")
        if not args.no_backup:
            print(f"📋 Backup: {backup_dir}")
        print("\n💡 Your tasks and memory bank were preserved")
        print("   Framework files are now fresh from version", version)
        print("\n🚀 Ready for Roo Code!")
        return 0
    else:
        print("\n❌ Reset completed with some errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
