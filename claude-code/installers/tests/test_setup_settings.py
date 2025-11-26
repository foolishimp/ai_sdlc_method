"""
Tests for installers/setup_settings.py

Validates: REQ-F-PLUGIN-001 (Plugin system with marketplace support)
           REQ-F-PLUGIN-002 (Federated plugin loading)
           REQ-F-PLUGIN-003 (Plugin bundles)

Test Cases: TC-SET-001 through TC-SET-015
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch

# Add installers directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_settings import SettingsSetup, PLUGIN_BUNDLES, ALL_PLUGINS


class TestSettingsSetupInit:
    """Test SettingsSetup initialization."""

    def test_init_default_values(self, temp_target):
        """
        TC-SET-001: Default initialization
        Validates: REQ-F-PLUGIN-001
        """
        setup = SettingsSetup(target=str(temp_target))

        assert setup.source_type == "github"
        assert setup.dry_run is False
        assert setup.force is False
        assert setup.enable_all is False
        # Default is startup bundle
        assert setup.plugins_to_enable == PLUGIN_BUNDLES["startup"]

    def test_init_with_all_plugins(self, temp_target):
        """
        TC-SET-002: Initialization with all plugins
        Validates: REQ-F-PLUGIN-001
        """
        setup = SettingsSetup(target=str(temp_target), enable_all=True)

        assert setup.plugins_to_enable == ALL_PLUGINS

    def test_init_with_custom_plugins(self, temp_target):
        """
        TC-SET-003: Initialization with custom plugin list
        Validates: REQ-F-PLUGIN-001
        """
        custom_plugins = ["aisdlc-core", "testing-skills"]
        setup = SettingsSetup(target=str(temp_target), plugins=custom_plugins)

        assert setup.plugins_to_enable == custom_plugins

    def test_init_with_directory_source(self, temp_target):
        """
        TC-SET-004: Initialization with directory source
        Validates: REQ-F-PLUGIN-002
        """
        setup = SettingsSetup(
            target=str(temp_target),
            source_type="directory",
            local_path="/custom/path"
        )

        assert setup.source_type == "directory"
        assert setup.local_path == "/custom/path"


class TestBuildMarketplaceConfig:
    """Test marketplace configuration building."""

    def test_github_source_config(self, temp_target):
        """
        TC-SET-005: GitHub source configuration
        Validates: REQ-F-PLUGIN-002
        """
        setup = SettingsSetup(target=str(temp_target), source_type="github")
        config = setup._build_marketplace_config()

        assert "aisdlc" in config
        assert config["aisdlc"]["source"]["source"] == "github"
        assert config["aisdlc"]["source"]["repo"] == "foolishimp/ai_sdlc_method"
        assert config["aisdlc"]["source"]["path"] == "claude-code/plugins"

    def test_directory_source_config(self, temp_target):
        """
        TC-SET-006: Directory source configuration
        Validates: REQ-F-PLUGIN-002
        """
        setup = SettingsSetup(
            target=str(temp_target),
            source_type="directory",
            local_path="/my/local/path"
        )
        config = setup._build_marketplace_config()

        assert "aisdlc-local" in config
        assert config["aisdlc-local"]["source"]["source"] == "directory"
        assert config["aisdlc-local"]["source"]["path"] == "/my/local/path"

    def test_git_source_config(self, temp_target):
        """
        TC-SET-007: Git URL source configuration
        Validates: REQ-F-PLUGIN-002
        """
        setup = SettingsSetup(
            target=str(temp_target),
            source_type="git",
            git_url="https://git.company.com/repo.git"
        )
        config = setup._build_marketplace_config()

        assert "aisdlc-git" in config
        assert config["aisdlc-git"]["source"]["source"] == "git"
        assert config["aisdlc-git"]["source"]["url"] == "https://git.company.com/repo.git"

    def test_git_source_without_url_fails(self, temp_target):
        """
        TC-SET-008: Git source without URL returns None
        Validates: REQ-F-PLUGIN-002
        """
        setup = SettingsSetup(target=str(temp_target), source_type="git")
        config = setup._build_marketplace_config()

        assert config is None


class TestBuildPluginsConfig:
    """Test plugins configuration building."""

    def test_github_plugin_naming(self, temp_target):
        """
        TC-SET-009: Plugin naming with GitHub source
        Validates: REQ-F-PLUGIN-001
        """
        setup = SettingsSetup(target=str(temp_target), source_type="github")
        config = setup._build_plugins_config()

        for plugin in setup.plugins_to_enable:
            assert f"{plugin}@aisdlc" in config
            assert config[f"{plugin}@aisdlc"] is True

    def test_directory_plugin_naming(self, temp_target):
        """
        TC-SET-010: Plugin naming with directory source
        Validates: REQ-F-PLUGIN-001
        """
        setup = SettingsSetup(target=str(temp_target), source_type="directory")
        config = setup._build_plugins_config()

        for plugin in setup.plugins_to_enable:
            assert f"{plugin}@aisdlc-local" in config
            assert config[f"{plugin}@aisdlc-local"] is True


class TestMergeSettings:
    """Test settings merging functionality."""

    def test_merge_into_empty(self, temp_target):
        """
        TC-SET-011: Merge into empty settings
        Validates: REQ-F-PLUGIN-001
        """
        setup = SettingsSetup(target=str(temp_target))
        marketplace = setup._build_marketplace_config()
        plugins = setup._build_plugins_config()

        result = setup._merge_settings({}, marketplace, plugins)

        assert "extraKnownMarketplaces" in result
        assert "enabledPlugins" in result
        assert "aisdlc" in result["extraKnownMarketplaces"]

    def test_preserve_existing_settings(self, temp_target):
        """
        TC-SET-012: Preserve existing non-AISDLC settings
        Validates: REQ-F-PLUGIN-001
        """
        setup = SettingsSetup(target=str(temp_target), force=True)
        existing = {
            "someSetting": "value",
            "enabledPlugins": {"other-plugin@other": True}
        }
        marketplace = setup._build_marketplace_config()
        plugins = setup._build_plugins_config()

        result = setup._merge_settings(existing, marketplace, plugins)

        assert result["someSetting"] == "value"
        assert result["enabledPlugins"]["other-plugin@other"] is True
        assert "aisdlc-core@aisdlc" in result["enabledPlugins"]


class TestWriteSettings:
    """Test settings file writing."""

    def test_create_new_settings_file(self, temp_target):
        """
        TC-SET-013: Create new settings.json
        Validates: REQ-F-PLUGIN-001
        """
        setup = SettingsSetup(target=str(temp_target), source_type="github")
        success = setup.run()

        assert success is True
        settings_file = temp_target / ".claude" / "settings.json"
        assert settings_file.exists()

        with open(settings_file) as f:
            settings = json.load(f)

        assert "extraKnownMarketplaces" in settings
        assert "aisdlc" in settings["extraKnownMarketplaces"]

    def test_dry_run_no_file_created(self, temp_target):
        """
        TC-SET-014: Dry run doesn't create file
        Validates: REQ-F-PLUGIN-001
        """
        setup = SettingsSetup(target=str(temp_target), dry_run=True)
        success = setup.run()

        assert success is True
        settings_file = temp_target / ".claude" / "settings.json"
        assert not settings_file.exists()

    def test_backup_existing_settings(self, temp_target_with_settings):
        """
        TC-SET-015: Backup created when overwriting
        Validates: REQ-F-PLUGIN-001
        """
        setup = SettingsSetup(target=str(temp_target_with_settings), force=True)
        success = setup.run()

        assert success is True
        backup_file = temp_target_with_settings / ".claude" / "settings.json.bak"
        assert backup_file.exists()

        # Verify backup contains original content
        with open(backup_file) as f:
            backup = json.load(f)
        assert backup["existingSetting"] is True


class TestPluginBundles:
    """Test plugin bundle functionality."""

    def test_startup_bundle_plugins(self, temp_target):
        """
        TC-SET-016: Startup bundle contains correct plugins
        Validates: REQ-F-PLUGIN-003
        """
        expected = ["aisdlc-core", "aisdlc-methodology", "principles-key"]
        assert PLUGIN_BUNDLES["startup"] == expected

    def test_enterprise_bundle_plugins(self, temp_target):
        """
        TC-SET-017: Enterprise bundle contains all plugins
        Validates: REQ-F-PLUGIN-003
        """
        enterprise = PLUGIN_BUNDLES["enterprise"]
        assert len(enterprise) == 8
        assert "aisdlc-core" in enterprise
        assert "aisdlc-methodology" in enterprise

    def test_all_bundles_defined(self):
        """
        TC-SET-018: All bundles are defined
        Validates: REQ-F-PLUGIN-003
        """
        expected_bundles = ["startup", "datascience", "qa", "enterprise"]
        for bundle in expected_bundles:
            assert bundle in PLUGIN_BUNDLES


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_json_handling(self, temp_target_with_invalid_json):
        """
        TC-SET-019: Handle invalid JSON in existing settings
        Validates: REQ-F-PLUGIN-001
        """
        setup = SettingsSetup(target=str(temp_target_with_invalid_json), force=True)
        # Should not raise, should treat as empty
        existing = setup._load_existing_settings()
        assert existing == {}

    def test_nonexistent_target_directory(self):
        """
        TC-SET-020: Handle nonexistent target directory
        Validates: REQ-F-PLUGIN-001
        """
        import tempfile
        import os

        # Create path that doesn't exist
        temp_base = tempfile.mkdtemp()
        nonexistent = Path(temp_base) / "does" / "not" / "exist"

        setup = SettingsSetup(target=str(nonexistent))
        success = setup.run()

        # Should succeed and create directory
        assert success is True
        assert nonexistent.exists()

        # Cleanup
        import shutil
        shutil.rmtree(temp_base, ignore_errors=True)

    def test_existing_aisdlc_without_force(self, temp_target_with_aisdlc_settings):
        """
        TC-SET-021: Existing AISDLC config without force flag
        Validates: REQ-F-PLUGIN-001
        """
        setup = SettingsSetup(target=str(temp_target_with_aisdlc_settings), force=False)
        setup.run()

        # Should add new config but keep old
        settings_file = temp_target_with_aisdlc_settings / ".claude" / "settings.json"
        with open(settings_file) as f:
            settings = json.load(f)

        # Both old and new should exist
        assert "aisdlc-old" in settings["extraKnownMarketplaces"]
        assert "aisdlc" in settings["extraKnownMarketplaces"]

    def test_existing_aisdlc_with_force(self, temp_target_with_aisdlc_settings):
        """
        TC-SET-022: Existing AISDLC config with force flag removes old
        Validates: REQ-F-PLUGIN-001
        """
        setup = SettingsSetup(target=str(temp_target_with_aisdlc_settings), force=True)
        setup.run()

        settings_file = temp_target_with_aisdlc_settings / ".claude" / "settings.json"
        with open(settings_file) as f:
            settings = json.load(f)

        # Old should be removed, only new
        assert "aisdlc-old" not in settings["extraKnownMarketplaces"]
        assert "aisdlc" in settings["extraKnownMarketplaces"]


class TestAllPlugins:
    """Test ALL_PLUGINS constant."""

    def test_all_plugins_count(self):
        """
        TC-SET-023: ALL_PLUGINS contains expected count
        Validates: REQ-F-PLUGIN-001
        """
        assert len(ALL_PLUGINS) == 8

    def test_all_plugins_content(self):
        """
        TC-SET-024: ALL_PLUGINS contains expected plugins
        Validates: REQ-F-PLUGIN-001
        """
        expected = [
            "aisdlc-core",
            "aisdlc-methodology",
            "principles-key",
            "code-skills",
            "testing-skills",
            "requirements-skills",
            "design-skills",
            "runtime-skills"
        ]
        for plugin in expected:
            assert plugin in ALL_PLUGINS
