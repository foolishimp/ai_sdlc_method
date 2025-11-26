#!/usr/bin/env python3
"""
AI SDLC Method - Plugins Setup Script

Installs AI SDLC plugins directly.

Provides two installation modes:
1. Global: ~/.config/gemini/plugins/ (user-wide)
2. Project: ./.gemini/plugins/ (project-specific)

Supports:
- Individual plugins
- Plugin bundles (startup, datascience, qa, enterprise)
- All plugins at once

Usage:
    python setup_plugins.py [options]

Options:
    --target PATH           Target directory for project installation (default: current)
    --global                Install to user global plugins directory
    --plugins LIST          Comma-separated list of plugins to install
    --bundle NAME           Install a bundle (startup|datascience|qa|enterprise)
    --all                   Install all available plugins
    --list                  List available plugins and bundles
    --force                 Overwrite existing plugins
    --help                  Show this help message

Examples:
    # Install to user global
    python setup_plugins.py --global --bundle startup

    # Install to project
    python setup_plugins.py --target /my/project --plugins aisdlc-core,testing-skills

    # Install all plugins globally
    python setup_plugins.py --global --all

    # List available plugins
    python setup_plugins.py --list
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from common import InstallerBase, print_banner


# Plugin bundles configuration
BUNDLES = {
    "startup": {
        "description": "Essential plugins for getting started",
        "plugins": ["aisdlc-core", "aisdlc-methodology", "principles-key"]
    },
    "datascience": {
        "description": "Data science and ML development",
        "plugins": ["aisdlc-core", "testing-skills", "python-standards", "runtime-skills"]
    },
    "qa": {
        "description": "Quality assurance and testing focus",
        "plugins": ["testing-skills", "code-skills", "requirements-skills", "runtime-skills"]
    },
    "enterprise": {
        "description": "Full enterprise SDLC suite",
        "plugins": [
            "aisdlc-core", "aisdlc-methodology", "design-skills",
            "testing-skills", "runtime-skills", "python-standards",
            "requirements-skills", "code-skills", "principles-key"
        ]
    }
}


class PluginsSetup(InstallerBase):
    """Setup AI SDLC plugins in global or project location."""

    def __init__(self, target: str = ".", install_global: bool = False,
                 plugins: Optional[List[str]] = None, bundle: Optional[str] = None,
                 install_all: bool = False, force: bool = False):
        super().__init__(target, force)
        self.install_global = install_global
        self.plugins_to_install = plugins or []
        self.bundle = bundle
        self.install_all = install_all

        # Plugin source directory
        self.plugins_source = self.ai_sdlc_root / "gemini-code" / "plugins"

        # Determine installation target
        if self.install_global:
            self.plugins_target = Path.home() / ".config" / "gemini" / "plugins"
        else:
            self.plugins_target = self.target / ".gemini" / "plugins"

    def run(self) -> bool:
        """Execute the plugins setup process."""
        self.print_section("AI SDLC Plugins Setup")

        # Validate
        if not self.plugins_source.exists():
            self.print_error(f"Plugins source not found at: {self.plugins_source}")
            return False

        # Discover available plugins
        available_plugins = self._discover_plugins()
        if not available_plugins:
            self.print_error("No plugins found in source directory")
            return False

        print(f"📦 Found {len(available_plugins)} available plugins")
        print(f"📁 Installation target: {self.plugins_target}")
        print(f"📍 Mode: {'Global (user-wide)' if self.install_global else 'Project-local'}")

        # Determine what to install
        plugins_to_install = self._determine_plugins_to_install(available_plugins)

        if not plugins_to_install:
            print("\n⚠️  No plugins selected for installation")
            print("   Use --all, --bundle, or --plugins to select plugins")
            return False

        # Confirm installation
        print(f"\n📝 Plugins to install ({len(plugins_to_install)}):")
        for plugin in sorted(plugins_to_install):
            print(f"   - {plugin}")

        if not self.force:
            response = input(f"\nProceed with installation? [Y/n]: ").strip().lower()
            if response and response not in ['y', 'yes']:
                print("Installation cancelled")
                return False

        # Install plugins
        print(f"\n🚀 Installing plugins...")
        success_count = 0
        for plugin in plugins_to_install:
            if self._install_plugin(plugin, available_plugins[plugin]):
                success_count += 1

        # Summary
        self.print_section("Installation Summary")
        print(f"✅ Successfully installed: {success_count}/{len(plugins_to_install)}")
        print(f"📁 Location: {self.plugins_target}")

        if success_count > 0:
            self._print_next_steps()

        return success_count > 0

    def _discover_plugins(self) -> Dict[str, Path]:
        """Discover all available plugins."""
        plugins = {}

        for plugin_dir in self.plugins_source.iterdir():
            if not plugin_dir.is_dir():
                continue

            # Skip bundles directory
            if plugin_dir.name == "bundles":
                continue

            # Check for .gemini-plugin metadata
            metadata_file = plugin_dir / ".gemini-plugin"
            if metadata_file.exists():
                plugins[plugin_dir.name] = plugin_dir

        return plugins

    def _determine_plugins_to_install(self, available_plugins: Dict[str, Path]) -> List[str]:
        """Determine which plugins to install based on arguments."""
        plugins_to_install = set()

        # Install all
        if self.install_all:
            plugins_to_install.update(available_plugins.keys())

        # Install bundle
        if self.bundle:
            if self.bundle not in BUNDLES:
                print(f"❌ Unknown bundle: {self.bundle}")
                print(f"   Available bundles: {', '.join(BUNDLES.keys())}")
                return []

            bundle_plugins = BUNDLES[self.bundle]["plugins"]
            plugins_to_install.update(bundle_plugins)
            print(f"📦 Bundle '{self.bundle}': {BUNDLES[self.bundle]['description']}")

        # Install specific plugins
        if self.plugins_to_install:
            for plugin in self.plugins_to_install:
                if plugin not in available_plugins:
                    print(f"⚠️  Plugin not found: {plugin}")
                else:
                    plugins_to_install.add(plugin)

        # Validate all plugins exist
        valid_plugins = [p for p in plugins_to_install if p in available_plugins]
        invalid_plugins = plugins_to_install - set(valid_plugins)

        if invalid_plugins:
            print(f"⚠️  Skipping invalid plugins: {', '.join(invalid_plugins)}")

        return valid_plugins

    def _install_plugin(self, plugin_name: str, source_path: Path) -> bool:
        """Install a single plugin."""
        target_path = self.plugins_target / plugin_name

        # Check if already exists
        if target_path.exists() and not self.force:
            print(f"⏭️  {plugin_name} already installed (use --force to overwrite)")
            return True

        # Copy plugin
        return self.copy_directory(
            source_path,
            target_path,
            description=plugin_name
        )

    def _print_next_steps(self):
        """Print next steps for the user."""
        print("\n📚 Next Steps:")

        if self.install_global:
            print("1. Restart your Gemini environment to load global plugins")
        else:
            print("1. Restart your Gemini environment or reload project")


    def list_plugins_and_bundles(self):
        """List all available plugins and bundles."""
        self.print_section("Available Plugins")

        # Discover plugins
        plugins = self._discover_plugins()

        if not plugins:
            print("No plugins found")
            return

        # Group plugins by type (based on name suffix)
        core_plugins = []
        skill_plugins = []
        standard_plugins = []
        other_plugins = []

        for name in sorted(plugins.keys()):
            if "core" in name or "methodology" in name:
                core_plugins.append(name)
            elif "skills" in name:
                skill_plugins.append(name)
            elif "standards" in name:
                standard_plugins.append(name)
            else:
                other_plugins.append(name)

        # Display
        if core_plugins:
            print("\n🔧 Core Plugins:")
            for plugin in core_plugins:
                print(f"   - {plugin}")

        if skill_plugins:
            print("\n🎯 Skill Plugins:")
            for plugin in skill_plugins:
                print(f"   - {plugin}")

        if standard_plugins:
            print("\n📋 Standards Plugins:")
            for plugin in standard_plugins:
                print(f"   - {plugin}")

        if other_plugins:
            print("\n📦 Other Plugins:")
            for plugin in other_plugins:
                print(f"   - {plugin}")

        # Display bundles
        self.print_section("Available Bundles")
        for bundle_name, bundle_info in BUNDLES.items():
            print(f"\n📦 {bundle_name}")
            print(f"   {bundle_info['description']}")
            print(f"   Includes: {', '.join(bundle_info['plugins'])}")

        print(f"\n📊 Total: {len(plugins)} plugins, {len(BUNDLES)} bundles")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup AI SDLC plugins directly",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available plugins and bundles
  python setup_plugins.py --list

  # Install startup bundle globally
  python setup_plugins.py --global --bundle startup

  # Install specific plugins to project
  python setup_plugins.py --plugins aisdlc-core,testing-skills

  # Install all plugins globally
  python setup_plugins.py --global --all

  # Install to specific project
  python setup_plugins.py --target /my/project --bundle enterprise
        """
    )

    parser.add_argument(
        "--target",
        help="Target directory for project installation (default: current)",
        default="."
    )

    parser.add_argument(
        "--global",
        dest="install_global",
        action="store_true",
        help="Install to user global plugins directory (~/.config/gemini/plugins/)"
    )

    parser.add_argument(
        "--plugins",
        help="Comma-separated list of plugins to install",
        default=None
    )

    parser.add_argument(
        "--bundle",
        help="Install a bundle (startup|datascience|qa|enterprise)",
        choices=list(BUNDLES.keys()),
        default=None
    )

    parser.add_argument(
        "--all",
        dest="install_all",
        action="store_true",
        help="Install all available plugins"
    )

    parser.add_argument(
        "--list",
        dest="list_only",
        action="store_true",
        help="List available plugins and bundles"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing plugins"
    )

    args = parser.parse_args()

    # Parse plugins list
    plugins_list = None
    if args.plugins:
        plugins_list = [p.strip() for p in args.plugins.split(",")]

    # Print banner
    print_banner()

    # Create setup instance
    setup = PluginsSetup(
        target=args.target,
        install_global=args.install_global,
        plugins=plugins_list,
        bundle=args.bundle,
        install_all=args.install_all,
        force=args.force
    )

    try:
        # List only
        if args.list_only:
            setup.list_plugins_and_bundles()
            sys.exit(0)

        # Run installation
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