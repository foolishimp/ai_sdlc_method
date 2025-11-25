#!/usr/bin/env python3
"""
Roo Code AISDLC - Workspace Installer

Installs the .ai-workspace/ directory with task management and session tracking.
This workspace is shared across all AI coding tools (Claude, Codex, Roo, Gemini).

Usage:
    python setup_workspace.py [options]

Options:
    --target PATH    Target directory (default: current)
    --force          Overwrite existing files
    --no-git         Don't update .gitignore
"""

import sys
import argparse
from pathlib import Path

from common import RooInstallerBase, print_banner


class WorkspaceInstaller(RooInstallerBase):
    """Install .ai-workspace/ developer workspace."""

    def run(self) -> bool:
        """Install the developer workspace."""
        print(f"📦 Installing AISDLC developer workspace")
        print(f"   Target: {self.target}")

        # Validate
        if not self.validate_target():
            return False

        if not self.validate_templates():
            return False

        # Workspace template location
        source_dir = self.templates_root / ".ai-workspace"
        dest_dir = self.get_workspace_dir()

        if not source_dir.exists():
            self.print_error(f"Workspace template not found: {source_dir}")
            return False

        # Check if workspace already exists
        if dest_dir.exists() and not self.force:
            print(f"⏭️  .ai-workspace already exists (use --force to overwrite)")
            print(f"   Existing workspace preserved to protect your tasks")
            return True

        # If force, backup existing workspace
        if dest_dir.exists() and self.force:
            self.backup_directory(dest_dir)

        # Copy workspace template
        success = self.copy_directory(
            source_dir,
            dest_dir,
            description=".ai-workspace (developer workspace)"
        )

        if not success:
            return False

        # Ensure task directories exist
        self._ensure_task_directories(dest_dir)

        # Update .gitignore
        if not self.no_git:
            self.update_gitignore([
                ".ai-workspace/tasks/todo/",
                ".ai-workspace/session/",
                "# Keep active and finished tasks in git for continuity",
            ])

        self.print_success("Developer workspace installed successfully!")
        self._print_workspace_info(dest_dir)

        return True

    def _ensure_task_directories(self, workspace_dir: Path) -> None:
        """Ensure all task directories exist."""
        directories = [
            "tasks/todo",
            "tasks/active",
            "tasks/finished",
            "tasks/archive",
            "session/history",
            "templates",
            "config",
        ]

        for dir_name in directories:
            dir_path = workspace_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

    def _print_workspace_info(self, workspace_dir: Path) -> None:
        """Print workspace structure information."""
        print("\n📂 Workspace Structure:")
        print(f"""
{workspace_dir}/
├── tasks/
│   ├── todo/           # Quick capture
│   ├── active/         # Current work (ACTIVE_TASKS.md)
│   ├── finished/       # Completed task docs
│   └── archive/        # Old tasks
├── session/
│   ├── current_session.md
│   └── history/
├── templates/
│   ├── TASK_TEMPLATE.md
│   └── FINISHED_TASK_TEMPLATE.md
└── config/
    └── workspace_config.yml
""")
        print("💡 Key Files:")
        print("   • ACTIVE_TASKS.md - Your current work items")
        print("   • templates/ - Task and session templates")
        print("\n📝 Next Steps:")
        print("   1. Edit .ai-workspace/tasks/active/ACTIVE_TASKS.md")
        print("   2. Add your first task")
        print("   3. Start working with Roo Code!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Install AISDLC developer workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install workspace in current directory
  python setup_workspace.py

  # Install to specific project
  python setup_workspace.py --target /my/project

  # Force overwrite (backs up existing first)
  python setup_workspace.py --force
        """
    )

    parser.add_argument(
        "--target",
        help="Target directory for installation (default: current)",
        default="."
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing workspace (will backup first)"
    )

    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Don't update .gitignore"
    )

    args = parser.parse_args()

    installer = WorkspaceInstaller(
        target=args.target,
        force=args.force,
        no_git=args.no_git
    )

    print_banner("Roo Code - Workspace Setup")

    try:
        success = installer.run()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation interrupted")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
