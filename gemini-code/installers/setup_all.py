#!/usr/bin/env python3
"""
AI SDLC Method - Complete Setup Script

Installs the complete AI SDLC development environment into a target project:
- Developer Workspace (.ai-workspace/)
- Gemini Commands (.gemini/commands/)
- Plugins (optional - via direct install)
- Project guidance (GEMINI.md)

This is the main orchestrator that coordinates all installers.

Usage:
    python setup_all.py [options]

Options:
    --target PATH           Target directory for installation (default: current)
    --force                 Overwrite existing files
    --reset                 Reset-style install: scrub old files and install fresh
    --version TAG           Version tag for reset install (default: latest)
    --workspace-only        Install only .ai-workspace
    --commands-only         Install only .gemini/commands
    --plugins-only          Install only plugins
    --with-plugins          Include plugins in installation
    --plugin-list LIST      Comma-separated plugin names (default: all)
    --bundle BUNDLE         Install a plugin bundle (startup|datascience|qa|enterprise)
    --global-plugins        Install plugins globally instead of project-local
    --no-git                Don't update .gitignore
    --help                  Show this help message
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
        if self.reset:
            return self._run_reset_installer()

        print_banner()

        self.print_section("AI SDLC Method - Complete Setup")
        print(f"📁 Target directory: {self.target}")
        print(f"📁 AI SDLC source: {self.ai_sdlc_root}")
        print(f"🔖 Version: {get_ai_sdlc_version()}")

        if not self._validate_installers():
            return False

        install_workspace = not self.commands_only and not self.plugins_only
        install_commands = not self.workspace_only and not self.plugins_only
        install_plugins = self.with_plugins or self.plugins_only

        self.print_section("Installation Plan")
        self._print_plan(install_workspace, install_commands, install_plugins)

        success = True
        results = {}

        if install_workspace:
            self.print_section("Installing Developer Workspace")
            results['workspace'] = self._run_workspace_installer()
            success &= results['workspace']

        if install_commands:
            self.print_section("Installing Gemini Commands")
            results['commands'] = self._run_commands_installer()
            success &= results['commands']

        if install_plugins:
            self.print_section("Installing Plugins")
            results['plugins'] = self._run_plugins_installer()
            success &= results['plugins']

        if install_workspace or install_commands:
            self.print_section("Setting Up Project Guidance")
            results['gemini_md'] = self._setup_gemini_md()
            success &= results['gemini_md']

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
            "--source", str(self.ai_sdlc_root)
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
        print(f"   {'✅' if workspace else '⏭️ '} Developer Workspace (.ai-workspace/)")
        print(f"   {'✅' if commands else '⏭️ '} Gemini Commands (.gemini/commands/)")
        if plugins:
            plugin_desc = "startup bundle"
            if self.bundle:
                plugin_desc = f"{self.bundle} bundle"
            elif self.plugin_list:
                plugin_desc = self.plugin_list
            location = "global" if self.global_plugins else "project-local"
            print(f"   ✅ Plugins ({plugin_desc}, {location})")
        else:
            print("   ⏭️  Plugins (skipped)")
        print(f"   {'✅' if not self.no_git else '⏭️ '} .gitignore updates")

    def _run_installer(self, installer_path: Path, description: str, extra_args: list = None) -> bool:
        cmd = [sys.executable, str(installer_path), "--target", str(self.target)]
        if self.force:
            cmd.append("--force")
        if self.no_git:
            cmd.append("--no-git")
        if extra_args:
            cmd.extend(extra_args)
        return self._run_subprocess(cmd, description)
    
    def _run_workspace_installer(self) -> bool:
        return self._run_installer(self.workspace_installer, "Workspace installation")

    def _run_commands_installer(self) -> bool:
        return self._run_installer(self.commands_installer, "Commands installation")

    def _run_plugins_installer(self) -> bool:
        extra_args = []
        if self.global_plugins:
            extra_args.append("--global")
        if self.bundle:
            extra_args.extend(["--bundle", self.bundle])
        elif self.plugin_list:
            if self.plugin_list.lower() == "all":
                extra_args.append("--all")
            else:
                extra_args.extend(["--plugins", self.plugin_list])
        else:
             extra_args.extend(["--bundle", "startup"])
        return self._run_installer(self.plugins_installer, "Plugins installation", extra_args)

    def _run_subprocess(self, cmd: list, description: str) -> bool:
        """Run a subprocess and return success status."""
        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running {description}: {e}")
            return False

    def _setup_gemini_md(self) -> bool:
        """Create or update GEMINI.md file."""
        gemini_md_path = self.target / "GEMINI.md"
        template_path = self.templates_root / "GEMINI.md.template"

        if not template_path.exists():
            print(f"⚠️  GEMINI.md.template not found, creating basic version")
            return self._create_basic_gemini_md(gemini_md_path)

        if gemini_md_path.exists() and not self.force:
            print(f"⏭️  GEMINI.md already exists (use --force to overwrite)")
            return True

        return self.copy_file(template_path, gemini_md_path, description="GEMINI.md")

    def _create_basic_gemini_md(self, path: Path) -> bool:
        content = f"""# GEMINI.md

This file provides guidance to Gemini when working with this project.

## AI SDLC Method

This project uses the AI SDLC Method for development with AI assistance.

### Key Resources
- .ai-workspace/ - Task management and session tracking
- .gemini/commands/ - Custom commands for workflow

### Getting Started
1. Review tasks: `cat .ai-workspace/tasks/active/ACTIVE_TASKS.md`
2. To add a task, edit `.ai-workspace/tasks/active/ACTIVE_TASKS.md`

### Development Workflow
Follow TDD: RED → GREEN → REFACTOR

See `.ai-workspace/templates/PAIR_PROGRAMMING_GUIDE.md` for collaboration patterns.

## Project-Specific Notes
[Add your project-specific guidance here]
"""
        try:
            path.write_text(content)
            print(f"✅ Created basic GEMINI.md")
            return True
        except Exception as e:
            print(f"❌ Error creating GEMINI.md: {e}")
            return False

    def _print_summary(self, results: dict):
        print("\n📊 Installation Results:")
        for component, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            component_name = component.replace('_', ' ').title()
            print(f"   {status}: {component_name}")
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        print(f"\n   {success_count}/{total_count} components installed successfully")

    def _print_next_steps(self, workspace: bool, commands: bool, plugins: bool):
        print("\n📚 Next Steps:")
        step = 1
        if workspace:
            print(f"{step}. Review workspace: cat .ai-workspace/README.md")
            step += 1
        if commands:
            print(f"{step}. Try a command by typing its name in the chat.")
            step += 1
        if plugins:
            print(f"{step}. Verify plugins are loaded in your Gemini environment (after restart).")
            step += 1
        print(f"{step}. Read project guidance: cat GEMINI.md")
        step += 1
        print(f"{step}. Add your first task: edit .ai-workspace/tasks/active/ACTIVE_TASKS.md")
        step += 1
        print(f"{step}. Commit the setup:")
        print(f"   git add .")
        print(f"   git commit -m 'Add AI SDLC Method development environment'")
        print(f"\n🚀 Ready for AI-assisted development!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup complete AI SDLC Method development environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # ... (rest of the argument parsing is the same)
    args = parser.parse_args()

    # ... (argument validation is the same)

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