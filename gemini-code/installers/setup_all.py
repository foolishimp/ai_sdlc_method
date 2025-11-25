#!/usr/bin/env python3
"""
AI SDLC Method - Complete Setup Script

Installs the complete AI SDLC development environment into a target project:
- Developer Workspace (.ai-workspace/)
- Claude Commands (.claude/commands/)
- Plugins (optional - via direct install)
- Project guidance (CLAUDE.md)

This is the main orchestrator that coordinates all installers.

Usage:
    python setup_all.py [options]

Options:
    --target PATH           Target directory for installation (default: current)
    --force                 Overwrite existing files
    --reset                 Reset-style install: scrub old files and install fresh
    --version TAG           Version tag for reset install (default: latest)
    --workspace-only        Install only .ai-workspace
    --commands-only         Install only .claude/commands
    --plugins-only          Install only plugins
    --with-plugins          Include plugins in installation
    --plugin-list LIST      Comma-separated plugin names (default: all)
    --bundle BUNDLE         Install a plugin bundle (startup|datascience|qa|enterprise)
    --global-plugins        Install plugins globally instead of project-local
    --no-git                Don't update .gitignore
    --help                  Show this help message

Examples:
    # Full installation with startup bundle
    python setup_all.py --with-plugins --bundle startup

    # Workspace and commands only (no plugins)
    python setup_all.py

    # Everything with all plugins
    python setup_all.py --with-plugins --plugin-list all

    # Specific directory
    python setup_all.py --target /my/project --with-plugins --bundle enterprise

    # Force reinstall
    python setup_all.py --force

    # Reset install (clean slate, preserves finished tasks)
    python setup_all.py --reset

    # Reset to specific version
    python setup_all.py --reset --version v0.2.0
"""

import sys
import argparse
import subprocess
from pathlib import Path
from common import InstallerBase, print_banner, get_ai_sdlc_version


class AISDLCSetup(InstallerBase):
    """Complete AI SDLC Method setup orchestrator."""

    def __init__(self, target: str = ".", force: bool = False,
                 workspace_only: bool = False, commands_only: bool = False,
                 plugins_only: bool = False, with_plugins: bool = False,
                 plugin_list: str = None, bundle: str = None,
                 global_plugins: bool = False, no_git: bool = False,
                 reset: bool = False, version: str = None):
        super().__init__(target, force, no_git)

        self.workspace_only = workspace_only
        self.commands_only = commands_only
        self.plugins_only = plugins_only
        self.with_plugins = with_plugins
        self.plugin_list = plugin_list
        self.bundle = bundle
        self.global_plugins = global_plugins
        self.reset = reset
        self.version = version

        # Paths to individual installers
        self.installers_dir = Path(__file__).parent
        self.workspace_installer = self.installers_dir / "setup_workspace.py"
        self.commands_installer = self.installers_dir / "setup_commands.py"
        self.plugins_installer = self.installers_dir / "setup_plugins.py"
        self.reset_installer = self.installers_dir / "setup_reset.py"

    def run(self) -> bool:
        """Execute the complete setup process."""
        # Handle reset mode separately
        if self.reset:
            return self._run_reset_installer()

        print_banner()

        self.print_section("AI SDLC Method - Complete Setup")
        print(f"📁 Target directory: {self.target}")
        print(f"📁 AI SDLC source: {self.ai_sdlc_root}")
        print(f"🔖 Version: {get_ai_sdlc_version()}")

        # Validate installers exist
        if not self._validate_installers():
            return False

        # Determine what to install
        install_workspace = not self.commands_only and not self.plugins_only
        install_commands = not self.workspace_only and not self.plugins_only
        install_plugins = self.with_plugins or self.plugins_only

        # Print installation plan
        self.print_section("Installation Plan")
        self._print_plan(install_workspace, install_commands, install_plugins)

        # Execute installations
        success = True
        results = {}

        # Install workspace
        if install_workspace:
            self.print_section("Installing Developer Workspace")
            results['workspace'] = self._run_workspace_installer()
            success &= results['workspace']

        # Install commands
        if install_commands:
            self.print_section("Installing Claude Commands")
            results['commands'] = self._run_commands_installer()
            success &= results['commands']

        # Install plugins
        if install_plugins:
            self.print_section("Installing Plugins")
            results['plugins'] = self._run_plugins_installer()
            success &= results['plugins']

        # Create/update CLAUDE.md
        if install_workspace or install_commands:
            self.print_section("Setting Up Project Guidance")
            results['claude_md'] = self._setup_claude_md()
            success &= results['claude_md']

        # Final summary
        self.print_section("Installation Summary")
        self._print_summary(results)

        if success:
            self.print_success("AI SDLC Method installation complete!")
            self._print_next_steps(install_workspace, install_commands, install_plugins)
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
            "--source", str(self.ai_sdlc_root)  # Use local source
        ]

        if self.version:
            cmd.extend(["--version", self.version])

        if self.no_git:
            cmd.append("--no-git")

        return self._run_subprocess(cmd, "Reset installation")

    def _validate_installers(self) -> bool:
        """Validate that all required installer scripts exist."""
        missing = []

        if not self.workspace_installer.exists():
            missing.append(f"Workspace installer: {self.workspace_installer}")

        if not self.commands_installer.exists():
            missing.append(f"Commands installer: {self.commands_installer}")

        if not self.plugins_installer.exists():
            missing.append(f"Plugins installer: {self.plugins_installer}")

        if missing:
            self.print_error("Missing installer scripts:")
            for item in missing:
                print(f"   - {item}")
            print(f"\nEnsure you're running from the ai_sdlc_method/installers directory")
            return False

        return True

    def _print_plan(self, workspace: bool, commands: bool, plugins: bool):
        """Print what will be installed."""
        if workspace:
            print("   ✅ Developer Workspace (.ai-workspace/)")
        else:
            print("   ⏭️  Developer Workspace (skipped)")

        if commands:
            print("   ✅ Claude Commands (.claude/commands/)")
        else:
            print("   ⏭️  Claude Commands (skipped)")

        if plugins:
            plugin_desc = "all plugins"
            if self.bundle:
                plugin_desc = f"{self.bundle} bundle"
            elif self.plugin_list:
                plugin_desc = self.plugin_list

            location = "global" if self.global_plugins else "project-local"
            print(f"   ✅ Plugins ({plugin_desc}, {location})")
        else:
            print("   ⏭️  Plugins (skipped)")

        print(f"   {'✅' if not self.no_git else '⏭️ '} .gitignore updates")

    def _run_workspace_installer(self) -> bool:
        """Run the workspace installer."""
        cmd = [
            sys.executable,
            str(self.workspace_installer),
            "--target", str(self.target)
        ]

        if self.force:
            cmd.append("--force")
        if self.no_git:
            cmd.append("--no-git")

        return self._run_subprocess(cmd, "Workspace installation")

    def _run_commands_installer(self) -> bool:
        """Run the commands installer."""
        cmd = [
            sys.executable,
            str(self.commands_installer),
            "--target", str(self.target)
        ]

        if self.force:
            cmd.append("--force")
        if self.no_git:
            cmd.append("--no-git")

        return self._run_subprocess(cmd, "Commands installation")

    def _run_plugins_installer(self) -> bool:
        """Run the plugins installer."""
        cmd = [
            sys.executable,
            str(self.plugins_installer),
            "--target", str(self.target)
        ]

        if self.force:
            cmd.append("--force")

        if self.global_plugins:
            cmd.append("--global")

        if self.bundle:
            cmd.extend(["--bundle", self.bundle])
        elif self.plugin_list:
            if self.plugin_list.lower() == "all":
                cmd.append("--all")
            else:
                cmd.extend(["--plugins", self.plugin_list])
        else:
            # Default to startup bundle
            cmd.extend(["--bundle", "startup"])

        return self._run_subprocess(cmd, "Plugins installation")

    def _run_subprocess(self, cmd: list, description: str) -> bool:
        """Run a subprocess and return success status."""
        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running {description}: {e}")
            return False

    def _setup_claude_md(self) -> bool:
        """Create or update CLAUDE.md file."""
        claude_md_path = self.target / "CLAUDE.md"
        template_path = self.templates_root / "CLAUDE.md.template"

        # Check if template exists
        if not template_path.exists():
            print(f"⚠️  CLAUDE.md.template not found, creating basic version")
            return self._create_basic_claude_md(claude_md_path)

        # If CLAUDE.md already exists, don't overwrite unless force
        if claude_md_path.exists() and not self.force:
            print(f"⏭️  CLAUDE.md already exists (use --force to overwrite)")
            return True

        # Copy template
        return self.copy_file(
            template_path,
            claude_md_path,
            description="CLAUDE.md"
        )

    def _create_basic_claude_md(self, path: Path) -> bool:
        """Create a basic CLAUDE.md if template doesn't exist."""
        content = f"""# CLAUDE.md

This file provides guidance to Claude Code when working with this project.

## AI SDLC Method

This project uses the AI SDLC Method for development with AI assistance.

### Key Resources
- `.ai-workspace/` - Task management and session tracking
- `.claude/commands/` - Slash commands for workflow
- View README: `cat .ai-workspace/README.md`

### Getting Started
1. Start a session: `/start-session`
2. Review tasks: `cat .ai-workspace/tasks/active/ACTIVE_TASKS.md`
3. Quick capture: `/todo "description"`

### Development Workflow
Follow TDD: RED → GREEN → REFACTOR

See `.ai-workspace/templates/PAIR_PROGRAMMING_GUIDE.md` for collaboration patterns.

## Project-Specific Notes
[Add your project-specific guidance here]
"""

        try:
            path.write_text(content)
            print(f"✅ Created basic CLAUDE.md")
            return True
        except Exception as e:
            print(f"❌ Error creating CLAUDE.md: {e}")
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

    def _print_next_steps(self, workspace: bool, commands: bool, plugins: bool):
        """Print next steps for the user."""
        print("\n📚 Next Steps:")

        step = 1

        if workspace:
            print(f"{step}. Review workspace: cat .ai-workspace/README.md")
            step += 1

        if commands:
            print(f"{step}. Try a command: /start-session")
            step += 1

        if plugins:
            print(f"{step}. Verify plugins: /plugin list (after restart)")
            step += 1

        print(f"{step}. Read project guidance: cat CLAUDE.md")
        step += 1

        print(f"{step}. Add your first task: edit .ai-workspace/tasks/active/ACTIVE_TASKS.md")
        step += 1

        print(f"{step}. Commit the setup:")
        print(f"   git add .")
        print(f"   git commit -m 'Add AI SDLC Method development environment'")

        print(f"\n🚀 Ready for AI-assisted development!")
        print(f"\n💡 Quick Start:")
        print(f"   /start-session              # Begin your development session")
        print(f"   /todo \"task description\"    # Quick capture ideas")
        print(f"   /finish-task <id>           # Complete a task")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup complete AI SDLC Method development environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full installation (workspace + commands, no plugins)
  python setup_all.py

  # Full installation with startup bundle
  python setup_all.py --with-plugins --bundle startup

  # Full installation with all plugins
  python setup_all.py --with-plugins --plugin-list all

  # Install to specific directory
  python setup_all.py --target /my/project --with-plugins --bundle enterprise

  # Workspace only
  python setup_all.py --workspace-only

  # Commands only
  python setup_all.py --commands-only

  # Plugins only (global)
  python setup_all.py --plugins-only --global-plugins --bundle qa

  # Force reinstall everything
  python setup_all.py --force --with-plugins --plugin-list all

  # Reset install (clean slate, preserves finished tasks)
  python setup_all.py --reset

  # Reset to specific version
  python setup_all.py --reset --version v0.2.0
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
        "--reset",
        action="store_true",
        help="Reset-style install: scrub old files and install fresh (preserves finished tasks)"
    )

    parser.add_argument(
        "--version",
        help="Version tag for reset install (default: latest release)"
    )

    parser.add_argument(
        "--workspace-only",
        action="store_true",
        help="Install only .ai-workspace"
    )

    parser.add_argument(
        "--commands-only",
        action="store_true",
        help="Install only .claude/commands"
    )

    parser.add_argument(
        "--plugins-only",
        action="store_true",
        help="Install only plugins"
    )

    parser.add_argument(
        "--with-plugins",
        action="store_true",
        help="Include plugins in installation"
    )

    parser.add_argument(
        "--plugin-list",
        help="Comma-separated plugin names or 'all' (default: startup bundle)",
        default=None
    )

    parser.add_argument(
        "--bundle",
        help="Install a plugin bundle (startup|datascience|qa|enterprise)",
        choices=["startup", "datascience", "qa", "enterprise"],
        default=None
    )

    parser.add_argument(
        "--global-plugins",
        action="store_true",
        help="Install plugins globally instead of project-local"
    )

    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Don't update .gitignore"
    )

    # Validate conflicting options
    args = parser.parse_args()

    exclusive_count = sum([args.workspace_only, args.commands_only, args.plugins_only])
    if exclusive_count > 1:
        print("Error: Cannot specify multiple --*-only options together")
        sys.exit(1)

    # Reset mode is exclusive of other options
    if args.reset and any([args.workspace_only, args.commands_only, args.plugins_only,
                           args.with_plugins, args.force]):
        print("Error: --reset cannot be combined with --*-only, --with-plugins, or --force options")
        print("       Reset mode does a complete clean reinstall automatically")
        sys.exit(1)

    # --version requires --reset
    if args.version and not args.reset:
        print("Error: --version requires --reset flag")
        sys.exit(1)

    # Run setup
    setup = AISDLCSetup(
        target=args.target,
        force=args.force,
        workspace_only=args.workspace_only,
        commands_only=args.commands_only,
        plugins_only=args.plugins_only,
        with_plugins=args.with_plugins,
        plugin_list=args.plugin_list,
        bundle=args.bundle,
        global_plugins=args.global_plugins,
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
