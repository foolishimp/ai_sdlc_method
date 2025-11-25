#!/usr/bin/env python3
"""
Roo Code AISDLC - Complete Setup Script

Installs the complete AISDLC development environment for Roo Code:
- Developer Workspace (.ai-workspace/)
- Custom Modes (.roo/modes/)
- Custom Rules (.roo/rules/)
- Memory Bank (.roo/memory-bank/)
- Project guidance (ROOCODE.md)

This is the main orchestrator that coordinates all installers.

Usage:
    python setup_all.py [options]

Options:
    --target PATH           Target directory (default: current)
    --force                 Overwrite existing files
    --reset                 Reset-style install (clean slate, preserves tasks)
    --version TAG           Version tag for reset install (default: latest)
    --workspace-only        Install only .ai-workspace
    --modes-only            Install only .roo/modes
    --rules-only            Install only .roo/rules
    --memory-bank-only      Install only .roo/memory-bank
    --no-git                Don't update .gitignore
"""

import sys
import argparse
import subprocess
from pathlib import Path

from common import RooInstallerBase, print_banner, get_ai_sdlc_version


class RooAISDLCSetup(RooInstallerBase):
    """Complete Roo Code AISDLC setup orchestrator."""

    def __init__(self, target: str = ".", force: bool = False,
                 workspace_only: bool = False, modes_only: bool = False,
                 rules_only: bool = False, memory_bank_only: bool = False,
                 no_git: bool = False, reset: bool = False, version: str = None):
        super().__init__(target, force, no_git)

        self.workspace_only = workspace_only
        self.modes_only = modes_only
        self.rules_only = rules_only
        self.memory_bank_only = memory_bank_only
        self.reset = reset
        self.version = version

        # Paths to individual installers
        self.installers_dir = Path(__file__).parent
        self.workspace_installer = self.installers_dir / "setup_workspace.py"
        self.modes_installer = self.installers_dir / "setup_modes.py"
        self.rules_installer = self.installers_dir / "setup_rules.py"
        self.memory_bank_installer = self.installers_dir / "setup_memory_bank.py"
        self.reset_installer = self.installers_dir / "setup_reset.py"

    def run(self) -> bool:
        """Execute the complete setup process."""
        # Handle reset mode separately
        if self.reset:
            return self._run_reset_installer()

        print_banner("Roo Code AISDLC Setup")

        self.print_section("Roo Code AISDLC - Complete Setup")
        print(f"📁 Target directory: {self.target}")
        print(f"📁 Templates source: {self.templates_root}")
        print(f"🔖 Version: {get_ai_sdlc_version()}")

        # Validate
        if not self.validate_target():
            return False

        if not self.validate_templates():
            return False

        # Determine what to install
        install_workspace = not any([self.modes_only, self.rules_only, self.memory_bank_only])
        install_modes = not any([self.workspace_only, self.rules_only, self.memory_bank_only])
        install_rules = not any([self.workspace_only, self.modes_only, self.memory_bank_only])
        install_memory_bank = not any([self.workspace_only, self.modes_only, self.rules_only])

        # Print installation plan
        self.print_section("Installation Plan")
        self._print_plan(install_workspace, install_modes, install_rules, install_memory_bank)

        # Execute installations
        success = True
        results = {}

        # Install workspace
        if install_workspace:
            self.print_section("Installing Developer Workspace")
            results['workspace'] = self._run_installer(self.workspace_installer, "Workspace")
            success &= results['workspace']

        # Install modes
        if install_modes:
            self.print_section("Installing Custom Modes")
            results['modes'] = self._run_installer(self.modes_installer, "Modes")
            success &= results['modes']

        # Install rules
        if install_rules:
            self.print_section("Installing Custom Rules")
            results['rules'] = self._run_installer(self.rules_installer, "Rules")
            success &= results['rules']

        # Install memory bank
        if install_memory_bank:
            self.print_section("Installing Memory Bank")
            results['memory_bank'] = self._run_installer(self.memory_bank_installer, "Memory Bank")
            success &= results['memory_bank']

        # Create ROOCODE.md
        if install_workspace or install_modes:
            self.print_section("Setting Up Project Guidance")
            results['roocode_md'] = self._setup_roocode_md()
            success &= results['roocode_md']

        # Final summary
        self.print_section("Installation Summary")
        self._print_summary(results)

        if success:
            self.print_success("Roo Code AISDLC installation complete!")
            self._print_next_steps()
        else:
            self.print_error("Installation completed with errors - see messages above")

        return success

    def _run_reset_installer(self) -> bool:
        """Run reset-style installation that scrubs and reinstalls."""
        if not self.reset_installer.exists():
            self.print_error(f"Reset installer not found: {self.reset_installer}")
            return False

        cmd = [
            sys.executable,
            str(self.reset_installer),
            "--target", str(self.target),
            "--source", str(self.roo_code_root)
        ]

        if self.version:
            cmd.extend(["--version", self.version])

        if self.no_git:
            cmd.append("--no-git")

        return self._run_subprocess(cmd, "Reset installation")

    def _print_plan(self, workspace: bool, modes: bool, rules: bool, memory_bank: bool):
        """Print what will be installed."""
        if workspace:
            print("   ✅ Developer Workspace (.ai-workspace/)")
        else:
            print("   ⏭️  Developer Workspace (skipped)")

        if modes:
            print("   ✅ Custom Modes (.roo/modes/)")
        else:
            print("   ⏭️  Custom Modes (skipped)")

        if rules:
            print("   ✅ Custom Rules (.roo/rules/)")
        else:
            print("   ⏭️  Custom Rules (skipped)")

        if memory_bank:
            print("   ✅ Memory Bank (.roo/memory-bank/)")
        else:
            print("   ⏭️  Memory Bank (skipped)")

        print(f"   {'✅' if not self.no_git else '⏭️ '} .gitignore updates")

    def _run_installer(self, installer_path: Path, description: str) -> bool:
        """Run an individual installer script."""
        if not installer_path.exists():
            print(f"⚠️  {description} installer not found: {installer_path}")
            return False

        cmd = [
            sys.executable,
            str(installer_path),
            "--target", str(self.target)
        ]

        if self.force:
            cmd.append("--force")
        if self.no_git:
            cmd.append("--no-git")

        return self._run_subprocess(cmd, f"{description} installation")

    def _run_subprocess(self, cmd: list, description: str) -> bool:
        """Run a subprocess and return success status."""
        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running {description}: {e}")
            return False

    def _setup_roocode_md(self) -> bool:
        """Create or update ROOCODE.md file."""
        roocode_md_path = self.target / "ROOCODE.md"
        template_path = self.templates_root / "ROOCODE.md"

        # Check if template exists
        if template_path.exists():
            return self.copy_file(
                template_path,
                roocode_md_path,
                description="ROOCODE.md"
            )
        else:
            # Create basic ROOCODE.md
            return self._create_basic_roocode_md(roocode_md_path)

    def _create_basic_roocode_md(self, path: Path) -> bool:
        """Create a basic ROOCODE.md if template doesn't exist."""
        content = f"""# ROOCODE.md

This file provides guidance to Roo Code when working with this project.

## AI SDLC Method

This project uses the AI SDLC Method with Roo Code custom modes.

### Available Modes

Select from the mode picker or use @mode in chat:

| Mode | Stage | Purpose |
|------|-------|---------|
| aisdlc-requirements | 1 | Transform intent into REQ-* keys |
| aisdlc-design | 2 | Technical architecture and design |
| aisdlc-tasks | 3 | Work breakdown and planning |
| aisdlc-code | 4 | TDD implementation |
| aisdlc-system-test | 5 | BDD integration testing |
| aisdlc-uat | 6 | Business validation |
| aisdlc-runtime | 7 | Production feedback loop |

### Key Resources

- `.ai-workspace/` - Task management and session tracking
- `.roo/modes/` - AISDLC custom modes (7 stages)
- `.roo/rules/` - Methodology rules (TDD, BDD, tagging)
- `.roo/memory-bank/` - Persistent project context

### Getting Started

1. Review tasks: `cat .ai-workspace/tasks/active/ACTIVE_TASKS.md`
2. Select appropriate mode for your current work
3. Follow TDD workflow: RED → GREEN → REFACTOR → COMMIT

### Development Workflow

**Code Stage (aisdlc-code mode):**
1. Write failing test first (RED)
2. Write minimal code to pass (GREEN)
3. Improve code quality (REFACTOR)
4. Commit with REQ-* tags (COMMIT)

See `.roo/rules/tdd-workflow.md` for details.

## Project-Specific Notes

[Add your project-specific guidance here]

---

*Generated by AI SDLC Method - Version {get_ai_sdlc_version()}*
"""

        try:
            if path.exists() and not self.force:
                print(f"⏭️  ROOCODE.md already exists (use --force to overwrite)")
                return True

            path.write_text(content)
            print(f"✅ Created: ROOCODE.md")
            return True
        except Exception as e:
            print(f"❌ Error creating ROOCODE.md: {e}")
            return False

    def _print_summary(self, results: dict):
        """Print installation summary."""
        print("\n📊 Installation Results:")

        for component, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            component_name = component.replace('_', ' ').title()
            print(f"   {status}: {component_name}")

        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        print(f"\n   {success_count}/{total_count} components installed successfully")

    def _print_next_steps(self):
        """Print next steps for the user."""
        print("\n📚 Next Steps:")
        print("   1. Review workspace: cat .ai-workspace/tasks/active/ACTIVE_TASKS.md")
        print("   2. Review ROOCODE.md: cat ROOCODE.md")
        print("   3. Open Roo Code and select an AISDLC mode")
        print("   4. Customize .roo/memory-bank/ for your project")
        print("")
        print("🚀 Available AISDLC Modes:")
        print("   • aisdlc-requirements - Stage 1: Requirements")
        print("   • aisdlc-design       - Stage 2: Design")
        print("   • aisdlc-tasks        - Stage 3: Tasks")
        print("   • aisdlc-code         - Stage 4: Code (TDD)")
        print("   • aisdlc-system-test  - Stage 5: System Test (BDD)")
        print("   • aisdlc-uat          - Stage 6: UAT")
        print("   • aisdlc-runtime      - Stage 7: Runtime Feedback")
        print("")
        print("💡 Quick Start:")
        print("   Select 'aisdlc-code' mode and start coding with TDD!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup complete Roo Code AISDLC development environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full installation
  python setup_all.py

  # Install to specific directory
  python setup_all.py --target /my/project

  # Force overwrite
  python setup_all.py --force

  # Workspace only
  python setup_all.py --workspace-only

  # Modes only
  python setup_all.py --modes-only

  # Reset install (clean slate, preserves tasks)
  python setup_all.py --reset

  # Reset to specific version
  python setup_all.py --reset --version v0.3.0
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
        "--reset",
        action="store_true",
        help="Reset-style install: clean slate preserving tasks"
    )

    parser.add_argument(
        "--version",
        help="Version tag for reset install (default: latest)"
    )

    parser.add_argument(
        "--workspace-only",
        action="store_true",
        help="Install only .ai-workspace"
    )

    parser.add_argument(
        "--modes-only",
        action="store_true",
        help="Install only .roo/modes"
    )

    parser.add_argument(
        "--rules-only",
        action="store_true",
        help="Install only .roo/rules"
    )

    parser.add_argument(
        "--memory-bank-only",
        action="store_true",
        help="Install only .roo/memory-bank"
    )

    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Don't update .gitignore"
    )

    args = parser.parse_args()

    # Validate conflicting options
    exclusive_count = sum([
        args.workspace_only,
        args.modes_only,
        args.rules_only,
        args.memory_bank_only
    ])
    if exclusive_count > 1:
        print("Error: Cannot specify multiple --*-only options together")
        sys.exit(1)

    # Reset mode is exclusive
    if args.reset and any([args.workspace_only, args.modes_only,
                           args.rules_only, args.memory_bank_only, args.force]):
        print("Error: --reset cannot be combined with --*-only or --force")
        print("       Reset mode does a complete clean reinstall automatically")
        sys.exit(1)

    # --version requires --reset
    if args.version and not args.reset:
        print("Error: --version requires --reset flag")
        sys.exit(1)

    # Run setup
    setup = RooAISDLCSetup(
        target=args.target,
        force=args.force,
        workspace_only=args.workspace_only,
        modes_only=args.modes_only,
        rules_only=args.rules_only,
        memory_bank_only=args.memory_bank_only,
        no_git=args.no_git,
        reset=args.reset,
        version=args.version
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
