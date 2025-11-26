#!/usr/bin/env python3
"""
AI SDLC Method - Settings Setup Script

Creates or updates .claude/settings.json with AISDLC plugin configuration.

# Implements: REQ-F-PLUGIN-001 (Plugin system with marketplace support)
# Implements: REQ-F-PLUGIN-002 (Federated plugin loading)

This installer intelligently:
1. Creates .claude/settings.json if it doesn't exist
2. Merges AISDLC configuration into existing settings.json
3. Supports multiple source types (github, directory, git)

Usage:
    python setup_settings.py [options]

Options:
    --target PATH           Target project directory (default: current)
    --source TYPE           Source type: github (default), directory, git
    --local-path PATH       Path for directory source (default: auto-detect)
    --git-url URL           URL for git source
    --plugins LIST          Comma-separated plugins to enable (default: startup bundle)
    --all                   Enable all available plugins
    --dry-run               Preview changes without writing
    --force                 Overwrite existing AISDLC configuration
    --help                  Show this help message

Examples:
    # Configure with GitHub source (recommended)
    python setup_settings.py --target /my/project --source github

    # Configure with local directory
    python setup_settings.py --source directory --local-path ~/ai_sdlc_method/claude-code/plugins

    # Configure with all plugins
    python setup_settings.py --source github --all

    # Preview changes
    python setup_settings.py --source github --dry-run
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from common import InstallerBase, print_banner


# Plugin bundles
PLUGIN_BUNDLES = {
    "startup": ["aisdlc-core", "aisdlc-methodology", "principles-key"],
    "datascience": ["aisdlc-core", "testing-skills", "runtime-skills"],
    "qa": ["testing-skills", "code-skills", "requirements-skills", "runtime-skills"],
    "enterprise": [
        "aisdlc-core", "aisdlc-methodology", "design-skills",
        "testing-skills", "runtime-skills",
        "requirements-skills", "code-skills", "principles-key"
    ]
}

# All available plugins
ALL_PLUGINS = [
    "aisdlc-core", "aisdlc-methodology", "principles-key",
    "code-skills", "testing-skills", "requirements-skills",
    "design-skills", "runtime-skills"
]


class SettingsSetup(InstallerBase):
    """Setup Claude Code settings.json with AISDLC plugin configuration."""

    def __init__(
        self,
        target: str = ".",
        source_type: str = "github",
        local_path: Optional[str] = None,
        git_url: Optional[str] = None,
        plugins: Optional[List[str]] = None,
        enable_all: bool = False,
        dry_run: bool = False,
        force: bool = False
    ):
        super().__init__(target, force)
        self.source_type = source_type
        self.local_path = local_path
        self.git_url = git_url
        self.dry_run = dry_run
        self.enable_all = enable_all

        # Determine plugins to enable
        if enable_all:
            self.plugins_to_enable = ALL_PLUGINS
        elif plugins:
            self.plugins_to_enable = plugins
        else:
            # Default to startup bundle
            self.plugins_to_enable = PLUGIN_BUNDLES["startup"]

        # Settings file path
        self.settings_file = self.target / ".claude" / "settings.json"

    def run(self) -> bool:
        """Execute the settings setup process."""
        self.print_section("AI SDLC Settings Configuration")

        print(f"📁 Target: {self.target}")
        print(f"🔌 Source: {self.source_type}")
        print(f"📦 Plugins: {', '.join(self.plugins_to_enable)}")

        if self.dry_run:
            print("🔍 Mode: DRY RUN (no changes will be made)")

        # Build the configuration
        marketplace_config = self._build_marketplace_config()
        plugins_config = self._build_plugins_config()

        if not marketplace_config:
            return False

        # Load or create settings
        existing_settings = self._load_existing_settings()

        # Merge configurations
        new_settings = self._merge_settings(existing_settings, marketplace_config, plugins_config)

        # Show diff
        self._show_changes(existing_settings, new_settings)

        if self.dry_run:
            print("\n🔍 Dry run complete - no changes made")
            return True

        # Write settings
        return self._write_settings(new_settings)

    def _build_marketplace_config(self) -> Optional[Dict[str, Any]]:
        """Build the marketplace configuration based on source type."""
        if self.source_type == "github":
            return {
                "aisdlc": {
                    "source": {
                        "source": "github",
                        "repo": "foolishimp/ai_sdlc_method",
                        "path": "claude-code/plugins"
                    }
                }
            }
        elif self.source_type == "directory":
            # Determine local path
            if self.local_path:
                path = self.local_path
            else:
                # Auto-detect from installer location
                path = str(self.plugins_root)

            return {
                "aisdlc-local": {
                    "source": {
                        "source": "directory",
                        "path": path
                    }
                }
            }
        elif self.source_type == "git":
            if not self.git_url:
                self.print_error("Git URL required for git source type (--git-url)")
                return None

            return {
                "aisdlc-git": {
                    "source": {
                        "source": "git",
                        "url": self.git_url,
                        "path": "claude-code/plugins"
                    }
                }
            }
        else:
            self.print_error(f"Unknown source type: {self.source_type}")
            return None

    def _build_plugins_config(self) -> Dict[str, bool]:
        """Build the enabled plugins configuration."""
        # Determine marketplace name suffix
        if self.source_type == "github":
            suffix = "@aisdlc"
        elif self.source_type == "directory":
            suffix = "@aisdlc-local"
        elif self.source_type == "git":
            suffix = "@aisdlc-git"
        else:
            suffix = "@aisdlc"

        return {f"{plugin}{suffix}": True for plugin in self.plugins_to_enable}

    def _load_existing_settings(self) -> Dict[str, Any]:
        """Load existing settings.json or return empty dict."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"⚠️  Warning: Existing settings.json has invalid JSON: {e}")
                print("   Will create backup and overwrite")
                return {}
            except Exception as e:
                print(f"⚠️  Warning: Could not read settings.json: {e}")
                return {}
        return {}

    def _merge_settings(
        self,
        existing: Dict[str, Any],
        marketplace: Dict[str, Any],
        plugins: Dict[str, bool]
    ) -> Dict[str, Any]:
        """Merge AISDLC config into existing settings."""
        result = existing.copy()

        # Merge extraKnownMarketplaces
        if "extraKnownMarketplaces" not in result:
            result["extraKnownMarketplaces"] = {}

        # Check for existing AISDLC marketplace
        aisdlc_keys = [k for k in result["extraKnownMarketplaces"] if k.startswith("aisdlc")]

        if aisdlc_keys and not self.force:
            print(f"\n⚠️  Existing AISDLC marketplace found: {', '.join(aisdlc_keys)}")
            print("   Use --force to overwrite")
            # Still add new one, don't remove existing
        else:
            # Remove old AISDLC entries if force
            for key in aisdlc_keys:
                del result["extraKnownMarketplaces"][key]

        result["extraKnownMarketplaces"].update(marketplace)

        # Merge enabledPlugins
        if "enabledPlugins" not in result:
            result["enabledPlugins"] = {}

        # Remove old AISDLC plugin entries if force
        if self.force:
            old_plugins = [k for k in result["enabledPlugins"] if "@aisdlc" in k]
            for key in old_plugins:
                del result["enabledPlugins"][key]

        result["enabledPlugins"].update(plugins)

        return result

    def _show_changes(self, old: Dict[str, Any], new: Dict[str, Any]):
        """Show what changes will be made."""
        print("\n📝 Configuration to be written:")
        print("-" * 40)

        # Show marketplace
        print("\n📦 extraKnownMarketplaces:")
        for name, config in new.get("extraKnownMarketplaces", {}).items():
            if name.startswith("aisdlc"):
                source = config.get("source", {})
                print(f"   {name}:")
                print(f"     source: {source.get('source')}")
                if source.get('repo'):
                    print(f"     repo: {source.get('repo')}")
                if source.get('path'):
                    print(f"     path: {source.get('path')}")
                if source.get('url'):
                    print(f"     url: {source.get('url')}")

        # Show plugins
        print("\n🔌 enabledPlugins:")
        for name, enabled in new.get("enabledPlugins", {}).items():
            if "@aisdlc" in name:
                status = "✅" if enabled else "❌"
                print(f"   {status} {name}")

    def _write_settings(self, settings: Dict[str, Any]) -> bool:
        """Write settings to file."""
        try:
            # Ensure .claude directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            # Backup existing if present
            if self.settings_file.exists():
                backup_path = self.settings_file.with_suffix('.json.bak')
                import shutil
                shutil.copy(self.settings_file, backup_path)
                print(f"\n📋 Backed up existing settings to: {backup_path}")

            # Write new settings
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            print(f"\n✅ Settings written to: {self.settings_file}")

            self._print_next_steps()
            return True

        except Exception as e:
            self.print_error(f"Failed to write settings: {e}")
            return False

    def _print_next_steps(self):
        """Print next steps for the user."""
        print("\n📚 Next Steps:")
        print("1. Restart Claude Code to load plugins")
        print("2. Verify plugins: /plugin")
        print("3. (Optional) Install workspace: python setup_workspace.py --target .")
        print("\n💡 Plugin Configuration Location:")
        print(f"   {self.settings_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Configure Claude Code settings.json with AISDLC plugins",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Configure with GitHub source (recommended)
  python setup_settings.py --target /my/project --source github

  # Configure with local directory
  python setup_settings.py --source directory --local-path ~/ai_sdlc_method/claude-code/plugins

  # Enable all plugins
  python setup_settings.py --source github --all

  # Preview changes without writing
  python setup_settings.py --source github --dry-run

  # Overwrite existing AISDLC configuration
  python setup_settings.py --source github --force
        """
    )

    parser.add_argument(
        "--target",
        help="Target project directory (default: current)",
        default="."
    )

    parser.add_argument(
        "--source",
        choices=["github", "directory", "git"],
        default="github",
        help="Source type for plugins (default: github)"
    )

    parser.add_argument(
        "--local-path",
        help="Path for directory source (default: auto-detect from installer location)"
    )

    parser.add_argument(
        "--git-url",
        help="URL for git source"
    )

    parser.add_argument(
        "--plugins",
        help="Comma-separated plugins to enable (default: startup bundle)"
    )

    parser.add_argument(
        "--bundle",
        choices=list(PLUGIN_BUNDLES.keys()),
        help="Install a plugin bundle"
    )

    parser.add_argument(
        "--all",
        dest="enable_all",
        action="store_true",
        help="Enable all available plugins"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing AISDLC configuration"
    )

    args = parser.parse_args()

    # Parse plugins list
    plugins_list = None
    if args.plugins:
        plugins_list = [p.strip() for p in args.plugins.split(",")]
    elif args.bundle:
        plugins_list = PLUGIN_BUNDLES[args.bundle]

    # Print banner
    print_banner()

    # Create setup instance
    setup = SettingsSetup(
        target=args.target,
        source_type=args.source,
        local_path=args.local_path,
        git_url=args.git_url,
        plugins=plugins_list,
        enable_all=args.enable_all,
        dry_run=args.dry_run,
        force=args.force
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
