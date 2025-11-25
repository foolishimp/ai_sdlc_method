#!/usr/bin/env python3
"""
Common utilities for Roo Code AISDLC installers.

Shared functionality used across all setup scripts.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime


class RooInstallerBase:
    """Base class for all Roo Code installers with common functionality."""

    def __init__(self, target: str = ".", force: bool = False, no_git: bool = False):
        self.target = Path(target).resolve()
        self.force = force
        self.no_git = no_git

        # Get the ai_sdlc_method root directory
        # roo-code-iclaude/installers/common.py -> go up two levels
        self.installers_dir = Path(__file__).parent
        self.roo_code_root = self.installers_dir.parent
        self.ai_sdlc_root = self.roo_code_root.parent

        # Templates are in roo-code-iclaude/project-template/
        self.templates_root = self.roo_code_root / "project-template"

    def get_roo_config_dir(self) -> Path:
        """Get the .roo/ configuration directory."""
        return self.target / ".roo"

    def get_modes_dir(self) -> Path:
        """Get the modes directory."""
        return self.get_roo_config_dir() / "modes"

    def get_rules_dir(self) -> Path:
        """Get the rules directory."""
        return self.get_roo_config_dir() / "rules"

    def get_memory_bank_dir(self) -> Path:
        """Get the memory bank directory."""
        return self.get_roo_config_dir() / "memory-bank"

    def get_workspace_dir(self) -> Path:
        """Get the .ai-workspace directory."""
        return self.target / ".ai-workspace"

    def validate_target(self) -> bool:
        """Validate that target directory exists or can be created."""
        if not self.target.exists():
            try:
                self.target.mkdir(parents=True, exist_ok=True)
                return True
            except Exception as e:
                print(f"❌ Cannot create target directory: {e}")
                return False
        return True

    def validate_templates(self) -> bool:
        """Validate that template directory exists."""
        if not self.templates_root.exists():
            print(f"❌ Templates not found at: {self.templates_root}")
            print(f"   Make sure you're running from the ai_sdlc_method directory")
            return False
        return True

    def copy_directory(self, source: Path, destination: Path,
                       description: str = None) -> bool:
        """Copy a directory tree from source to destination."""
        if not source.exists():
            print(f"❌ Source not found: {source}")
            return False

        if destination.exists() and not self.force:
            print(f"⏭️  {description or destination.name} already exists (use --force to overwrite)")
            return False

        try:
            if destination.exists():
                shutil.rmtree(destination)

            shutil.copytree(source, destination)
            print(f"✅ Installed: {description or destination.name}")
            return True
        except Exception as e:
            print(f"❌ Error copying {source} to {destination}: {e}")
            return False

    def copy_file(self, source: Path, destination: Path,
                  description: str = None) -> bool:
        """Copy a single file from source to destination."""
        if not source.exists():
            print(f"❌ Source file not found: {source}")
            return False

        if destination.exists() and not self.force:
            print(f"⏭️  {description or destination.name} already exists (use --force to overwrite)")
            return False

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            print(f"✅ Copied: {description or destination.name}")
            return True
        except Exception as e:
            print(f"❌ Error copying {source} to {destination}: {e}")
            return False

    def update_gitignore(self, entries: List[str], section_name: str = "AI SDLC (Roo Code)") -> bool:
        """Add entries to .gitignore file."""
        if self.no_git:
            return True

        gitignore_path = self.target / ".gitignore"

        # Prepare section
        section_header = f"\n# {section_name}\n"
        entries_text = "\n".join(entries) + "\n"
        full_section = section_header + entries_text

        try:
            if gitignore_path.exists():
                content = gitignore_path.read_text()

                # Check if already has this section
                if section_header.strip() in content:
                    print(f"✓ .gitignore already has {section_name} section")
                    return True

                # Append section
                if not content.endswith("\n"):
                    content += "\n"
                content += full_section
                gitignore_path.write_text(content)
                print(f"✅ Updated .gitignore with {section_name} entries")
            else:
                # Create new .gitignore
                gitignore_path.write_text(full_section)
                print(f"✅ Created .gitignore with {section_name} entries")

            return True
        except Exception as e:
            print(f"❌ Error updating .gitignore: {e}")
            return False

    def create_file_from_template(self, template_content: str,
                                  destination: Path,
                                  replacements: dict = None) -> bool:
        """Create a file from template content with optional replacements."""
        if destination.exists() and not self.force:
            print(f"⏭️  {destination.name} already exists (use --force to overwrite)")
            return False

        try:
            content = template_content

            # Apply replacements
            if replacements:
                for key, value in replacements.items():
                    content = content.replace(key, value)

            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content)
            print(f"✅ Created: {destination.name}")
            return True
        except Exception as e:
            print(f"❌ Error creating {destination}: {e}")
            return False

    def backup_directory(self, dir_path: Path, backup_base: Path = None) -> Optional[Path]:
        """Create a backup of an existing directory."""
        if not dir_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if backup_base is None:
            backup_base = Path("/tmp")

        project_name = self.target.name
        backup_path = backup_base / f"aisdlc-backup-{project_name}-{timestamp}" / dir_path.name

        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(dir_path, backup_path)
            print(f"📋 Backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"⚠️  Could not create backup: {e}")
            return None

    def backup_file(self, file_path: Path) -> Optional[Path]:
        """Create a backup of an existing file."""
        if not file_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup.{timestamp}")

        try:
            shutil.copy2(file_path, backup_path)
            print(f"📋 Backed up to: {backup_path.name}")
            return backup_path
        except Exception as e:
            print(f"⚠️  Could not create backup: {e}")
            return None

    def remove_directory(self, dir_path: Path, description: str = None) -> bool:
        """Remove a directory if it exists."""
        if not dir_path.exists():
            return True

        try:
            shutil.rmtree(dir_path)
            print(f"🗑️  Removed: {description or dir_path.name}")
            return True
        except Exception as e:
            print(f"❌ Error removing {dir_path}: {e}")
            return False

    def print_section(self, title: str, width: int = 60):
        """Print a section header."""
        print(f"\n{'=' * width}")
        print(f"{title}")
        print('=' * width)

    def print_success(self, message: str):
        """Print a success message."""
        print(f"\n✅ {message}")

    def print_error(self, message: str):
        """Print an error message."""
        print(f"\n❌ {message}")

    def confirm_action(self, message: str, default: bool = True) -> bool:
        """Ask user for confirmation."""
        if self.force:
            return True

        prompt = f"{message} [{'Y/n' if default else 'y/N'}]: "
        response = input(prompt).strip().lower()

        if not response:
            return default

        return response in ['y', 'yes']


def get_ai_sdlc_version() -> str:
    """Get the AI SDLC Method version from git tag."""
    try:
        import subprocess
        # Go up to ai_sdlc_method root
        ai_sdlc_root = Path(__file__).parent.parent.parent
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            cwd=ai_sdlc_root
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return "unknown"
    except Exception:
        return "unknown"


def get_latest_release_tag(repo_url: str = None) -> Optional[str]:
    """Get the latest release tag from a git repository.

    Args:
        repo_url: Optional remote URL. If None, uses local repo tags.

    Returns:
        Latest tag version string (e.g., "v0.3.0") or None if not found.
    """
    try:
        import subprocess

        if repo_url:
            # Fetch tags from remote without cloning
            result = subprocess.run(
                ["git", "ls-remote", "--tags", "--sort=-version:refname", repo_url],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout:
                # Parse output: "sha\trefs/tags/v0.3.0"
                for line in result.stdout.strip().split('\n'):
                    if line and 'refs/tags/' in line:
                        tag = line.split('refs/tags/')[-1]
                        # Skip ^{} dereferenced tags
                        if not tag.endswith('^{}'):
                            return tag
        else:
            # Use local repository
            ai_sdlc_root = Path(__file__).parent.parent.parent
            result = subprocess.run(
                ["git", "tag", "-l", "--sort=-version:refname"],
                capture_output=True,
                text=True,
                cwd=ai_sdlc_root
            )
            if result.returncode == 0 and result.stdout:
                tags = result.stdout.strip().split('\n')
                if tags and tags[0]:
                    return tags[0]

        return None
    except Exception:
        return None


def print_banner(title: str = "Roo Code AISDLC Setup"):
    """Print the installer banner."""
    version = get_ai_sdlc_version()
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              {title:^38}              ║
║                                                              ║
║                    Version {version:<10}                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
