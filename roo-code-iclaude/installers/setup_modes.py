#!/usr/bin/env python3
"""
Roo Code AISDLC - Custom Modes Installer

Installs AISDLC custom modes to .roo/modes/ directory.
These modes define the 7 SDLC stage personas for Roo Code.

Usage:
    python setup_modes.py [options]

Options:
    --target PATH    Target directory (default: current)
    --force          Overwrite existing files
    --no-git         Don't update .gitignore
"""

import sys
import argparse
from pathlib import Path

from common import RooInstallerBase, print_banner


class ModeInstaller(RooInstallerBase):
    """Install AISDLC custom modes to .roo/modes/"""

    # The 7 SDLC stage modes
    MODES = [
        "aisdlc-requirements.json",
        "aisdlc-design.json",
        "aisdlc-tasks.json",
        "aisdlc-code.json",
        "aisdlc-system-test.json",
        "aisdlc-uat.json",
        "aisdlc-runtime.json",
    ]

    def run(self) -> bool:
        """Install all AISDLC modes."""
        print(f"📦 Installing AISDLC custom modes")
        print(f"   Target: {self.target}")

        # Validate
        if not self.validate_target():
            return False

        if not self.validate_templates():
            return False

        source_dir = self.templates_root / "roo" / "modes"
        dest_dir = self.get_modes_dir()

        if not source_dir.exists():
            self.print_error(f"Source modes not found: {source_dir}")
            return False

        # Create .roo/modes/ directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        success = True
        installed_count = 0
        skipped_count = 0

        for mode_file in self.MODES:
            src = source_dir / mode_file
            dst = dest_dir / mode_file

            if not src.exists():
                print(f"⚠️  Mode file not found: {mode_file}")
                continue

            if dst.exists() and not self.force:
                print(f"⏭️  {mode_file} already exists")
                skipped_count += 1
                continue

            if self.copy_file(src, dst, f"Mode: {mode_file}"):
                installed_count += 1
            else:
                success = False

        # Update .gitignore
        if not self.no_git:
            self.update_gitignore([
                "# Roo Code modes are project-specific",
                "# .roo/modes/  # Uncomment to exclude from git"
            ])

        # Summary
        print(f"\n📊 Modes Installation Summary:")
        print(f"   Installed: {installed_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Location: {dest_dir}")

        if success:
            self.print_success("Custom modes installed successfully!")
            print("\n💡 To use a mode in Roo Code:")
            print("   1. Open Roo Code")
            print("   2. Select mode from mode picker")
            print("   3. Or use @mode aisdlc-code in chat")
        else:
            self.print_error("Some modes failed to install")

        return success

    def list_modes(self) -> None:
        """List available AISDLC modes."""
        print("\n📋 Available AISDLC Modes:")
        print("=" * 50)

        mode_descriptions = {
            "aisdlc-requirements.json": "Stage 1: Requirements Agent - Intent to REQ-* keys",
            "aisdlc-design.json": "Stage 2: Design Agent - Technical architecture",
            "aisdlc-tasks.json": "Stage 3: Tasks Agent - Work breakdown",
            "aisdlc-code.json": "Stage 4: Code Agent - TDD implementation",
            "aisdlc-system-test.json": "Stage 5: System Test Agent - BDD integration",
            "aisdlc-uat.json": "Stage 6: UAT Agent - Business validation",
            "aisdlc-runtime.json": "Stage 7: Runtime Agent - Feedback loop",
        }

        for mode in self.MODES:
            desc = mode_descriptions.get(mode, "AISDLC mode")
            print(f"   • {mode}")
            print(f"     {desc}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Install AISDLC custom modes for Roo Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install modes in current directory
  python setup_modes.py

  # Install to specific project
  python setup_modes.py --target /my/project

  # Force overwrite existing
  python setup_modes.py --force

  # List available modes
  python setup_modes.py --list
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
        help="Overwrite existing files"
    )

    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Don't update .gitignore"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available modes"
    )

    args = parser.parse_args()

    installer = ModeInstaller(
        target=args.target,
        force=args.force,
        no_git=args.no_git
    )

    if args.list:
        installer.list_modes()
        return 0

    print_banner("Roo Code - Modes Setup")

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
