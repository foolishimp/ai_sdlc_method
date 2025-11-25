#!/usr/bin/env python3
"""
Roo Code AISDLC - Memory Bank Installer

Installs AISDLC memory bank templates to .roo/memory-bank/ directory.
Memory bank provides persistent context across Roo Code sessions.

Usage:
    python setup_memory_bank.py [options]

Options:
    --target PATH    Target directory (default: current)
    --force          Overwrite existing files (CAUTION: overwrites user data)
    --no-git         Don't update .gitignore
"""

import sys
import argparse
from pathlib import Path

from common import RooInstallerBase, print_banner


class MemoryBankInstaller(RooInstallerBase):
    """Install AISDLC memory bank to .roo/memory-bank/"""

    # Memory bank template files
    TEMPLATES = [
        "projectbrief.md",
        "techstack.md",
        "activecontext.md",
        "methodref.md",
    ]

    def run(self) -> bool:
        """Install memory bank templates."""
        print(f"📦 Installing AISDLC memory bank templates")
        print(f"   Target: {self.target}")

        # Validate
        if not self.validate_target():
            return False

        if not self.validate_templates():
            return False

        source_dir = self.templates_root / "roo" / "memory-bank"
        dest_dir = self.get_memory_bank_dir()

        if not source_dir.exists():
            self.print_error(f"Source memory bank not found: {source_dir}")
            return False

        # Create .roo/memory-bank/ directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        success = True
        installed_count = 0
        skipped_count = 0
        preserved_count = 0

        for template in self.TEMPLATES:
            src = source_dir / template
            dst = dest_dir / template

            if not src.exists():
                print(f"⚠️  Template not found: {template}")
                continue

            # Memory bank files contain user data - don't overwrite by default
            if dst.exists():
                if not self.force:
                    print(f"⏭️  {template} exists (preserving user data)")
                    preserved_count += 1
                    continue
                else:
                    # Backup before overwriting
                    self.backup_file(dst)

            if self.copy_file(src, dst, f"Memory: {template}"):
                installed_count += 1
            else:
                success = False

        # Update .gitignore - memory bank might contain sensitive project info
        if not self.no_git:
            self.update_gitignore([
                "# Memory bank may contain sensitive project context",
                "# .roo/memory-bank/  # Uncomment to exclude from git"
            ])

        # Summary
        print(f"\n📊 Memory Bank Installation Summary:")
        print(f"   Installed: {installed_count}")
        print(f"   Preserved: {preserved_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Location: {dest_dir}")

        if success:
            self.print_success("Memory bank templates installed successfully!")
            print("\n💡 Memory bank provides persistent context:")
            print("   • projectbrief.md - Project overview and goals")
            print("   • techstack.md - Technology decisions")
            print("   • activecontext.md - Current work focus")
            print("   • methodref.md - AISDLC methodology reference")
            print("\n📝 Customize these files for your project!")
        else:
            self.print_error("Some templates failed to install")

        return success

    def list_templates(self) -> None:
        """List memory bank templates."""
        print("\n📋 Memory Bank Templates:")
        print("=" * 50)

        template_descriptions = {
            "projectbrief.md": "Project overview, goals, and constraints",
            "techstack.md": "Technology stack and architectural decisions",
            "activecontext.md": "Current work focus and recent changes",
            "methodref.md": "AISDLC methodology quick reference",
        }

        for template in self.TEMPLATES:
            desc = template_descriptions.get(template, "Memory bank template")
            print(f"   • {template}")
            print(f"     {desc}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Install AISDLC memory bank for Roo Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install memory bank in current directory
  python setup_memory_bank.py

  # Install to specific project
  python setup_memory_bank.py --target /my/project

  # Force overwrite (CAUTION: backs up then overwrites user data)
  python setup_memory_bank.py --force

  # List available templates
  python setup_memory_bank.py --list
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
        help="Overwrite existing files (will backup first)"
    )

    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Don't update .gitignore"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available templates"
    )

    args = parser.parse_args()

    installer = MemoryBankInstaller(
        target=args.target,
        force=args.force,
        no_git=args.no_git
    )

    if args.list:
        installer.list_templates()
        return 0

    print_banner("Roo Code - Memory Bank Setup")

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
