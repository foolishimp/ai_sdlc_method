#!/usr/bin/env python3
"""
AI SDLC Method - Gemini Commands Setup Script

Installs the .gemini/commands/ directory into a target project.

The commands provide custom command functionality.

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


class GeminiCommandsSetup(InstallerBase):
    """Setup .gemini/commands in a target project."""

    def __init__(self, target: str = ".", force: bool = False, no_git: bool = False):
        super().__init__(target, force, no_git)
        self.commands_source = self.templates_root / ".gemini"
        self.commands_target = self.target / ".gemini"

    def run(self) -> bool:
        """Execute the commands setup process."""
        self.print_section("AI SDLC Gemini Commands Setup")
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
        print(f"   .gemini/: {'✅ exists' if exists else '❌ missing'}")
        print(f"   .gemini/commands/: {'✅ exists' if commands_exist else '❌ missing'}")

        # List available commands
        if self.commands_source.exists() and (self.commands_source / "commands").exists():
            available_commands = list((self.commands_source / "commands").glob("*.md"))
            print(f"\n📝 Available commands ({len(available_commands)}):")
            for cmd in sorted(available_commands)[:10]:  # Show first 10
                print(f"   - /{cmd.stem}")
            if len(available_commands) > 10:
                print(f"   ... and {len(available_commands) - 10} more")

        # Install commands
        if not commands_exist or self.force:
            if commands_exist and self.force:
                print(f"\n🔄 Reinstalling .gemini/commands (--force flag)")
            else:
                print(f"\n📦 Installing .gemini/commands...")

            success = self._install_commands()
            if not success:
                return False
        else:
            print(f"\n⏭️  Skipping .gemini/commands (already exists)")

        # Print next steps
        self.print_success("Gemini commands setup complete!")
        self._print_next_steps()

        return True

    def _install_commands(self) -> bool:
        """Install the .gemini/ directory."""
        return self.copy_directory(
            self.commands_source,
            self.commands_target,
            description=".gemini/"
        )

    def _print_next_steps(self):
        """Print next steps for the user."""
        print("\n📚 Next Steps:")
        print("1. List available commands: ls .gemini/commands/")
        print("2. To use a command, type its name in the chat.")
        print("\n💡 Tip: Commands work best with .ai-workspace installed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup AI SDLC Gemini commands in your project",
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
    setup = GeminiCommandsSetup(
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