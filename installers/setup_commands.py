#!/usr/bin/env python3
"""
AI SDLC Method - Claude Commands Setup Script

Installs the .claude/commands/ directory into a target project.

# Implements: REQ-F-CMD-001 (Slash commands for workflow)
# Implements: REQ-F-CMD-002 (Persona management commands)

The commands provide slash command functionality:
- /aisdlc-checkpoint-tasks - Save progress and update task status
- /aisdlc-finish-task - Complete task with documentation
- /aisdlc-commit-task - Commit with proper message
- /aisdlc-status - Show task queue status
- /aisdlc-apply-persona - Apply development persona
- And more...

Usage:
    python setup_commands.py [options]

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


class CommandsSetup(InstallerBase):
    """Setup .claude/commands in a target project."""

    def __init__(self, target: str = ".", force: bool = False, no_git: bool = False):
        super().__init__(target, force, no_git)
        self.commands_source = self.templates_root / ".claude"
        self.commands_target = self.target / ".claude"

    def run(self) -> bool:
        """Execute the commands setup process."""
        self.print_section("AI SDLC Claude Commands Setup")
        print(f"📁 Target directory: {self.target}")
        print(f"📁 Template source: {self.commands_source}")

        # Validate
        if not self.validate_target():
            return False

        if not self.validate_templates():
            return False

        if not self.commands_source.exists():
            self.print_error(f"Commands template not found at: {self.commands_source}")
            return False

        # Check current state
        exists = self.commands_target.exists()
        commands_dir = self.commands_target / "commands"
        commands_exist = commands_dir.exists() if exists else False

        print(f"\n📋 Current state:")
        print(f"   .claude/: {'✅ exists' if exists else '❌ missing'}")
        print(f"   .claude/commands/: {'✅ exists' if commands_exist else '❌ missing'}")

        # List available commands
        if self.commands_source.exists():
            available_commands = list((self.commands_source / "commands").glob("*.md"))
            print(f"\n📝 Available commands ({len(available_commands)}):")
            for cmd in sorted(available_commands)[:10]:  # Show first 10
                print(f"   - /{cmd.stem}")
            if len(available_commands) > 10:
                print(f"   ... and {len(available_commands) - 10} more")

        # Install commands
        if not commands_exist or self.force:
            if commands_exist and self.force:
                print(f"\n🔄 Reinstalling .claude/commands (--force flag)")
            else:
                print(f"\n📦 Installing .claude/commands...")

            success = self._install_commands()
            if not success:
                return False
        else:
            print(f"\n⏭️  Skipping .claude/commands (already exists)")

        # Print next steps
        self.print_success("Claude commands setup complete!")
        self._print_next_steps()

        return True

    def _install_commands(self) -> bool:
        """Install the .claude/commands directory."""
        return self.copy_directory(
            self.commands_source,
            self.commands_target,
            description=".claude/"
        )

    def _print_next_steps(self):
        """Print next steps for the user."""
        print("\n📚 Next Steps:")
        print("1. List available commands: ls .claude/commands/")
        print("2. Check task status: /aisdlc-status")
        print("3. Work on tasks from ACTIVE_TASKS.md")
        print("4. View command details: cat .claude/commands/aisdlc-checkpoint-tasks.md")
        print("\n📝 Available slash commands:")

        # List actual commands
        commands_dir = self.commands_target / "commands"
        if commands_dir.exists():
            commands = sorted([f.stem for f in commands_dir.glob("*.md")])
            for cmd in commands:
                print(f"   /{cmd}")

        print("\n💡 Tip: Commands work best with .ai-workspace installed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup AI SDLC Claude commands in your project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install in current directory
  python setup_commands.py

  # Install in specific directory
  python setup_commands.py --target /path/to/project

  # Force overwrite existing commands
  python setup_commands.py --force

  # Skip .gitignore updates
  python setup_commands.py --no-git
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
    setup = CommandsSetup(
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
