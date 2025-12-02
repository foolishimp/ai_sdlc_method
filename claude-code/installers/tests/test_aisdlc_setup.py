"""
Tests for aisdlc-setup.py installer

Validates: REQ-F-PLUGIN-001 (Plugin system with marketplace support)
           REQ-F-WORKSPACE-001 (Developer workspace structure)

Test Cases: TC-SETUP-001 through TC-SETUP-020
"""

import pytest
import json
import sys
from pathlib import Path
from io import StringIO

# Add installers directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module under test - need to handle the script format
import importlib.util
spec = importlib.util.spec_from_file_location(
    "aisdlc_setup",
    Path(__file__).parent.parent / "aisdlc-setup.py"
)
aisdlc_setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aisdlc_setup)


class TestSetupSettings:
    """Test settings.json creation."""

    def test_creates_settings_json(self, temp_target):
        """
        TC-SETUP-001: Creates .claude/settings.json
        Validates: REQ-F-PLUGIN-001
        """
        result = aisdlc_setup.setup_settings(temp_target, dry_run=False)

        assert result is True
        settings_file = temp_target / ".claude" / "settings.json"
        assert settings_file.exists()

    def test_settings_has_marketplace(self, temp_target):
        """
        TC-SETUP-002: Settings contains marketplace configuration
        Validates: REQ-F-PLUGIN-001
        """
        aisdlc_setup.setup_settings(temp_target, dry_run=False)

        settings_file = temp_target / ".claude" / "settings.json"
        with open(settings_file) as f:
            settings = json.load(f)

        assert "extraKnownMarketplaces" in settings
        assert "aisdlc" in settings["extraKnownMarketplaces"]
        assert settings["extraKnownMarketplaces"]["aisdlc"]["source"]["source"] == "github"
        assert settings["extraKnownMarketplaces"]["aisdlc"]["source"]["repo"] == "foolishimp/ai_sdlc_method"

    def test_settings_enables_plugin(self, temp_target):
        """
        TC-SETUP-003: Settings enables aisdlc-methodology plugin
        Validates: REQ-F-PLUGIN-001
        """
        aisdlc_setup.setup_settings(temp_target, dry_run=False)

        settings_file = temp_target / ".claude" / "settings.json"
        with open(settings_file) as f:
            settings = json.load(f)

        assert "enabledPlugins" in settings
        assert "aisdlc-methodology@aisdlc" in settings["enabledPlugins"]
        assert settings["enabledPlugins"]["aisdlc-methodology@aisdlc"] is True

    def test_preserves_existing_settings(self, temp_target_with_settings):
        """
        TC-SETUP-004: Preserves existing settings when merging
        Validates: REQ-F-PLUGIN-001
        """
        aisdlc_setup.setup_settings(temp_target_with_settings, dry_run=False)

        settings_file = temp_target_with_settings / ".claude" / "settings.json"
        with open(settings_file) as f:
            settings = json.load(f)

        # Original setting preserved
        assert settings["existingSetting"] is True
        # Original plugin preserved
        assert settings["enabledPlugins"]["other@other"] is True
        # New plugin added
        assert settings["enabledPlugins"]["aisdlc-methodology@aisdlc"] is True

    def test_dry_run_no_file(self, temp_target):
        """
        TC-SETUP-005: Dry run doesn't create file
        Validates: REQ-F-PLUGIN-001
        """
        result = aisdlc_setup.setup_settings(temp_target, dry_run=True)

        assert result is True
        settings_file = temp_target / ".claude" / "settings.json"
        assert not settings_file.exists()

    def test_handles_invalid_json(self, temp_target_with_invalid_json):
        """
        TC-SETUP-006: Handles invalid JSON gracefully
        Validates: REQ-F-PLUGIN-001
        """
        # Should not raise, should overwrite
        result = aisdlc_setup.setup_settings(temp_target_with_invalid_json, dry_run=False)

        assert result is True
        settings_file = temp_target_with_invalid_json / ".claude" / "settings.json"
        with open(settings_file) as f:
            settings = json.load(f)

        assert "aisdlc-methodology@aisdlc" in settings["enabledPlugins"]


class TestSetupWorkspace:
    """Test .ai-workspace creation."""

    def test_creates_workspace_structure(self, temp_target):
        """
        TC-SETUP-007: Creates .ai-workspace directory structure
        Validates: REQ-F-WORKSPACE-001
        """
        result = aisdlc_setup.setup_workspace(temp_target, dry_run=False)

        assert result is True
        assert (temp_target / ".ai-workspace" / "tasks" / "active").exists()
        assert (temp_target / ".ai-workspace" / "tasks" / "finished").exists()
        assert (temp_target / ".ai-workspace" / "templates").exists()
        assert (temp_target / ".ai-workspace" / "config").exists()

    def test_creates_active_tasks(self, temp_target):
        """
        TC-SETUP-008: Creates ACTIVE_TASKS.md
        Validates: REQ-F-WORKSPACE-001
        """
        aisdlc_setup.setup_workspace(temp_target, dry_run=False)

        active_tasks = temp_target / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
        assert active_tasks.exists()
        content = active_tasks.read_text()
        assert "# Active Tasks" in content
        assert "Total Active Tasks" in content

    def test_creates_task_template(self, temp_target):
        """
        TC-SETUP-009: Creates TASK_TEMPLATE.md
        Validates: REQ-F-WORKSPACE-001
        """
        aisdlc_setup.setup_workspace(temp_target, dry_run=False)

        template = temp_target / ".ai-workspace" / "templates" / "TASK_TEMPLATE.md"
        assert template.exists()
        content = template.read_text()
        assert "# Task #{ID}" in content
        assert "Acceptance Criteria" in content

    def test_creates_finished_template(self, temp_target):
        """
        TC-SETUP-010: Creates FINISHED_TASK_TEMPLATE.md
        Validates: REQ-F-WORKSPACE-001
        """
        aisdlc_setup.setup_workspace(temp_target, dry_run=False)

        template = temp_target / ".ai-workspace" / "templates" / "FINISHED_TASK_TEMPLATE.md"
        assert template.exists()
        content = template.read_text()
        assert "# Task: {TITLE}" in content
        assert "Lessons Learned" in content

    def test_creates_method_reference(self, temp_target):
        """
        TC-SETUP-011: Creates AISDLC_METHOD_REFERENCE.md
        Validates: REQ-F-WORKSPACE-001
        """
        aisdlc_setup.setup_workspace(temp_target, dry_run=False)

        reference = temp_target / ".ai-workspace" / "templates" / "AISDLC_METHOD_REFERENCE.md"
        assert reference.exists()
        content = reference.read_text()
        assert "AI SDLC Method" in content
        assert "7 Key Principles" in content

    def test_creates_workspace_config(self, temp_target):
        """
        TC-SETUP-012: Creates workspace_config.yml
        Validates: REQ-F-WORKSPACE-001
        """
        aisdlc_setup.setup_workspace(temp_target, dry_run=False)

        config = temp_target / ".ai-workspace" / "config" / "workspace_config.yml"
        assert config.exists()
        content = config.read_text()
        assert "task_tracking:" in content
        assert "tdd:" in content

    def test_preserves_existing_active_tasks(self, temp_target_with_workspace):
        """
        TC-SETUP-013: Preserves existing ACTIVE_TASKS.md
        Validates: REQ-F-WORKSPACE-001
        """
        aisdlc_setup.setup_workspace(temp_target_with_workspace, dry_run=False)

        active_tasks = temp_target_with_workspace / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
        content = active_tasks.read_text()

        # Original content preserved
        assert "My Existing Tasks" in content
        assert "Important work" in content

    def test_preserves_finished_tasks(self, temp_target_with_workspace):
        """
        TC-SETUP-014: Preserves existing finished tasks
        Validates: REQ-F-WORKSPACE-001
        """
        aisdlc_setup.setup_workspace(temp_target_with_workspace, dry_run=False)

        finished_task = temp_target_with_workspace / ".ai-workspace" / "tasks" / "finished" / "20251201_task.md"
        assert finished_task.exists()
        content = finished_task.read_text()
        assert "Completed Task" in content

    def test_dry_run_no_workspace(self, temp_target):
        """
        TC-SETUP-015: Dry run doesn't create workspace
        Validates: REQ-F-WORKSPACE-001
        """
        result = aisdlc_setup.setup_workspace(temp_target, dry_run=True)

        assert result is True
        assert not (temp_target / ".ai-workspace").exists()


class TestGetWorkspaceStructure:
    """Test workspace structure generation."""

    def test_returns_all_files(self):
        """
        TC-SETUP-016: Returns all expected files
        Validates: REQ-F-WORKSPACE-001
        """
        structure = aisdlc_setup.get_workspace_structure("2025-12-02 12:00")

        expected_files = [
            ".ai-workspace/tasks/active/ACTIVE_TASKS.md",
            ".ai-workspace/tasks/finished/.gitkeep",
            ".ai-workspace/templates/TASK_TEMPLATE.md",
            ".ai-workspace/templates/FINISHED_TASK_TEMPLATE.md",
            ".ai-workspace/templates/AISDLC_METHOD_REFERENCE.md",
            ".ai-workspace/config/workspace_config.yml",
        ]

        for expected in expected_files:
            assert expected in structure, f"Missing: {expected}"

    def test_active_tasks_has_date(self):
        """
        TC-SETUP-017: ACTIVE_TASKS.md includes date
        Validates: REQ-F-WORKSPACE-001
        """
        structure = aisdlc_setup.get_workspace_structure("2025-12-02 12:00")

        content = structure[".ai-workspace/tasks/active/ACTIVE_TASKS.md"]
        assert "2025-12-02 12:00" in content


class TestTemplateContent:
    """Test embedded template content."""

    def test_active_tasks_template_valid(self):
        """
        TC-SETUP-018: ACTIVE_TASKS_TEMPLATE is valid markdown
        Validates: REQ-F-WORKSPACE-001
        """
        template = aisdlc_setup.ACTIVE_TASKS_TEMPLATE
        assert "# Active Tasks" in template
        assert "{date}" in template  # Has placeholder
        assert "Recovery Commands" in template

    def test_task_template_has_tdd(self):
        """
        TC-SETUP-019: TASK_TEMPLATE includes TDD checklist
        Validates: REQ-F-WORKSPACE-001
        """
        template = aisdlc_setup.TASK_TEMPLATE
        assert "TDD Checklist" in template
        assert "RED:" in template
        assert "GREEN:" in template
        assert "REFACTOR:" in template

    def test_method_reference_has_principles(self):
        """
        TC-SETUP-020: METHOD_REFERENCE includes 7 principles
        Validates: REQ-F-WORKSPACE-001
        """
        reference = aisdlc_setup.METHOD_REFERENCE
        assert "Test Driven Development" in reference
        assert "Fail Fast" in reference
        assert "Modular" in reference
        assert "Reuse Before Build" in reference
        assert "Open Source First" in reference
        assert "No Legacy Baggage" in reference
        assert "Perfectionist Excellence" in reference


class TestMainFunction:
    """Test main function and CLI."""

    def test_main_returns_zero_on_success(self, temp_target, monkeypatch):
        """
        TC-SETUP-021: Main returns 0 on success
        Validates: REQ-F-PLUGIN-001
        """
        monkeypatch.setattr(sys, 'argv', ['aisdlc-setup.py', '--target', str(temp_target)])

        result = aisdlc_setup.main()

        assert result == 0

    def test_main_with_no_workspace_flag(self, temp_target, monkeypatch):
        """
        TC-SETUP-022: --no-workspace skips workspace creation
        Validates: REQ-F-PLUGIN-001
        """
        monkeypatch.setattr(sys, 'argv', ['aisdlc-setup.py', '--target', str(temp_target), '--no-workspace'])

        aisdlc_setup.main()

        # Settings created
        assert (temp_target / ".claude" / "settings.json").exists()
        # Workspace NOT created
        assert not (temp_target / ".ai-workspace").exists()

    def test_main_creates_both_by_default(self, temp_target, monkeypatch):
        """
        TC-SETUP-023: Default creates both settings and workspace
        Validates: REQ-F-PLUGIN-001, REQ-F-WORKSPACE-001
        """
        monkeypatch.setattr(sys, 'argv', ['aisdlc-setup.py', '--target', str(temp_target)])

        aisdlc_setup.main()

        # Both created
        assert (temp_target / ".claude" / "settings.json").exists()
        assert (temp_target / ".ai-workspace").exists()
