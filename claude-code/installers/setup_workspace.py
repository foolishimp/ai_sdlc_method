#!/usr/bin/env python3
"""
AI SDLC Method - Workspace Setup Script

Installs the .ai-workspace/ directory structure into a target project.

The workspace provides:
- Task management (todo, active, finished, archive)
- Session tracking
- Templates for tasks, sessions, pair programming
- Configuration files

# Implements: REQ-F-WORKSPACE-001 (Developer workspace structure)
# Implements: REQ-F-WORKSPACE-002 (Task management templates)
# Implements: REQ-F-WORKSPACE-003 (Session tracking templates)
# Implements: REQ-NFR-CONTEXT-001 (Persistent context across sessions)

Usage:
    python setup_workspace.py [options]

Options:
    --target PATH    Target directory for installation (default: current directory)
    --force          Overwrite existing files
    --no-git         Don't add .gitignore entries
    --help           Show this help message
"""

import sys
import argparse
from pathlib import Path
from common import InstallerBase, print_banner


class WorkspaceSetup(InstallerBase):
    """Setup .ai-workspace in a target project."""

    def __init__(self, target: str = ".", force: bool = False, no_git: bool = False):
        super().__init__(target, force, no_git)
        self.workspace_source = self.templates_root / ".ai-workspace"
        self.workspace_target = self.target / ".ai-workspace"

    def run(self) -> bool:
        """Execute the workspace setup process."""
        self.print_section("AI SDLC Workspace Setup")
        print(f"📁 Target directory: {self.target}")
        print(f"📁 Template source: {self.workspace_source}")

        # Validate
        if not self.validate_target():
            return False

        if not self.validate_templates():
            return False

        if not self.workspace_source.exists():
            self.print_error(f"Workspace template not found at: {self.workspace_source}")
            return False

        # Check current state
        exists = self.workspace_target.exists()
        print(f"\n📋 Current state:")
        print(f"   .ai-workspace/: {'✅ exists' if exists else '❌ missing'}")

        # Install workspace
        if not exists or self.force:
            if exists and self.force:
                print(f"\n🔄 Reinstalling .ai-workspace (--force flag)")
            else:
                print(f"\n📦 Installing .ai-workspace...")

            success = self._install_workspace()
            if not success:
                return False
        else:
            print(f"\n⏭️  Skipping .ai-workspace (already exists)")

        # Update .gitignore
        if not self.no_git:
            self._update_gitignore()

        # Print next steps
        self.print_success("Workspace setup complete!")
        self._print_next_steps()

        return True

    def _install_workspace(self) -> bool:
        """Install the .ai-workspace directory."""
        return self.copy_directory(
            self.workspace_source,
            self.workspace_target,
            description=".ai-workspace/"
        )

    def _update_gitignore(self) -> bool:
        """Add .ai-workspace entries to .gitignore."""
        # Session files should be git-ignored (local state)
        # But tasks, templates, config should be tracked
        entries = [
            ".ai-workspace/session/current_session.md",
            ".ai-workspace/session/history/",
            "*.backup.*",
        ]

        return self.update_gitignore(entries, "AI SDLC Workspace - Local Session Data")

    def _print_next_steps(self):
        """Print next steps for the user."""
        print("\n📚 Next Steps:")
        print("1. Review workspace structure: ls -la .ai-workspace/")
        print("2. Read workspace guide: cat .ai-workspace/README.md")
        print("3. Configure workspace: edit .ai-workspace/config/workspace_config.yml")
        print("4. Start a session: Use /start-session command (if .claude/commands installed)")
        print("5. Add your first task: edit .ai-workspace/tasks/active/ACTIVE_TASKS.md")
        print("\n💡 Tip: Install Claude commands with setup_commands.py for slash command support")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup AI SDLC workspace in your project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install in current directory
  python setup_workspace.py

  # Install in specific directory
  python setup_workspace.py --target /path/to/project

  # Force overwrite existing workspace
  python setup_workspace.py --force

  # Skip .gitignore updates
  python setup_workspace.py --no-git
        """
    )

    parser.add_argument(
        "--target",
        help="Target directory for installation (default: current directory)",
        default="."
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files"
    )

    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Don't add .gitignore entries"
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Run setup
    setup = WorkspaceSetup(
        target=args.target,
        force=args.force,
        no_git=args.no_git
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
