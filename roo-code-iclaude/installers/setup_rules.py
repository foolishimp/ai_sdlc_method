#!/usr/bin/env python3
"""
Roo Code AISDLC - Custom Rules Installer

Installs AISDLC custom rules/instructions to .roo/rules/ directory.
These rules provide methodology guidance referenced by custom modes.

Usage:
    python setup_rules.py [options]

Options:
    --target PATH    Target directory (default: current)
    --force          Overwrite existing files
    --no-git         Don't update .gitignore
"""

import sys
import argparse
from pathlib import Path

from common import RooInstallerBase, print_banner


class RulesInstaller(RooInstallerBase):
    """Install AISDLC rules to .roo/rules/"""

    # Core methodology rules
    RULES = [
        "key-principles.md",
        "tdd-workflow.md",
        "bdd-workflow.md",
        "req-tagging.md",
        "feedback-protocol.md",
        "workspace-safeguards.md",
    ]

    def run(self) -> bool:
        """Install all AISDLC rules."""
        print(f"📦 Installing AISDLC custom rules")
        print(f"   Target: {self.target}")

        # Validate
        if not self.validate_target():
            return False

        if not self.validate_templates():
            return False

        source_dir = self.templates_root / "roo" / "rules"
        dest_dir = self.get_rules_dir()

        if not source_dir.exists():
            self.print_error(f"Source rules not found: {source_dir}")
            return False

        # Create .roo/rules/ directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        success = True
        installed_count = 0
        skipped_count = 0

        for rule_file in self.RULES:
            src = source_dir / rule_file
            dst = dest_dir / rule_file

            if not src.exists():
                print(f"⚠️  Rule file not found: {rule_file}")
                continue

            if dst.exists() and not self.force:
                print(f"⏭️  {rule_file} already exists")
                skipped_count += 1
                continue

            if self.copy_file(src, dst, f"Rule: {rule_file}"):
                installed_count += 1
            else:
                success = False

        # Update .gitignore
        if not self.no_git:
            self.update_gitignore([
                "# Roo Code rules are project-specific",
                "# .roo/rules/  # Uncomment to exclude from git"
            ])

        # Summary
        print(f"\n📊 Rules Installation Summary:")
        print(f"   Installed: {installed_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Location: {dest_dir}")

        if success:
            self.print_success("Custom rules installed successfully!")
            print("\n💡 Rules are referenced by modes via @rules/filename.md")
            print("   Example: @rules/tdd-workflow.md in aisdlc-code.json")
        else:
            self.print_error("Some rules failed to install")

        return success

    def list_rules(self) -> None:
        """List available AISDLC rules."""
        print("\n📋 Available AISDLC Rules:")
        print("=" * 50)

        rule_descriptions = {
            "key-principles.md": "The 7 Key Principles for Code stage",
            "tdd-workflow.md": "RED → GREEN → REFACTOR → COMMIT cycle",
            "bdd-workflow.md": "Given/When/Then for System Test & UAT",
            "req-tagging.md": "REQ-* key format and tagging rules",
            "feedback-protocol.md": "Bidirectional stage feedback loops",
            "workspace-safeguards.md": "Safety rules for workspace operations",
        }

        for rule in self.RULES:
            desc = rule_descriptions.get(rule, "AISDLC rule")
            print(f"   • {rule}")
            print(f"     {desc}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Install AISDLC custom rules for Roo Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install rules in current directory
  python setup_rules.py

  # Install to specific project
  python setup_rules.py --target /my/project

  # Force overwrite existing
  python setup_rules.py --force

  # List available rules
  python setup_rules.py --list
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
        help="List available rules"
    )

    args = parser.parse_args()

    installer = RulesInstaller(
        target=args.target,
        force=args.force,
        no_git=args.no_git
    )

    if args.list:
        installer.list_rules()
        return 0

    print_banner("Roo Code - Rules Setup")

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
