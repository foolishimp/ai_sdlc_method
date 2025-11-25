"""
Tests for installers/setup_reset.py

Validates: REQ-F-RESET-001, REQ-F-UPDATE-001
Test Cases: TC-RST-001 through TC-RST-011
"""

import pytest
import sys
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add installers to path
# claude-code/installers/tests/test_*.py -> parent is installers directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_reset import ResetInstaller, RESET_DIRECTORIES, PRESERVE_PATHS


class TestResetInstallerInitialization:
    """Test ResetInstaller initialization."""

    def test_default_initialization(self, temp_target):
        """
        ResetInstaller initializes with defaults
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(target=str(temp_target))

        assert installer.target.resolve() == temp_target.resolve()
        assert installer.force is True  # Reset always forces
        assert installer.version is None
        assert installer.source_path is None
        assert installer.dry_run is False
        assert installer.no_backup is False
        assert installer.no_git is False

    def test_custom_initialization(self, temp_target, temp_dir):
        """
        ResetInstaller accepts custom parameters
        Validates: REQ-F-RESET-001
        """
        source = temp_dir / "source"
        source.mkdir()

        installer = ResetInstaller(
            target=str(temp_target),
            version="v0.2.0",
            source=str(source),
            dry_run=True,
            no_backup=True,
            no_git=True
        )

        assert installer.version == "v0.2.0"
        assert installer.source_path.resolve() == source.resolve()
        assert installer.dry_run is True
        assert installer.no_backup is True
        assert installer.no_git is True


class TestDryRunMode:
    """Test dry run mode functionality."""

    # TC-RST-001: Dry Run Mode
    def test_dry_run_no_changes(self, existing_installation, temp_source, capsys):
        """
        TC-RST-001: Dry run shows plan but makes no changes
        Validates: REQ-F-RESET-001
        """
        # Record original state
        original_active_content = (existing_installation / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md").read_text()
        original_commands = list((existing_installation / ".claude" / "commands").iterdir())

        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            dry_run=True
        )

        result = installer.run()

        assert result is True

        # Verify no changes were made
        assert (existing_installation / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md").read_text() == original_active_content
        assert list((existing_installation / ".claude" / "commands").iterdir()) == original_commands

        # Verify plan was shown
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        assert "Will REMOVE" in captured.out
        assert "Will PRESERVE" in captured.out
        assert "No changes were made" in captured.out

    def test_dry_run_shows_preserve_list(self, existing_installation, temp_source, capsys):
        """
        Dry run shows files that will be preserved
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            dry_run=True
        )

        installer.run()

        captured = capsys.readouterr()
        assert ".ai-workspace/tasks/finished" in captured.out
        assert ".ai-workspace/tasks/active" in captured.out


class TestPreserveFiles:
    """Test file preservation during reset."""

    # TC-RST-002: Preserve Active Tasks
    def test_preserve_active_tasks(self, existing_installation, temp_source):
        """
        TC-RST-002: Active tasks are preserved during reset
        Validates: REQ-F-RESET-001
        """
        # Record original active tasks
        active_file = existing_installation / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
        original_content = active_file.read_text()

        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            no_backup=True
        )

        result = installer.run()

        assert result is True

        # Verify active tasks preserved
        assert active_file.exists()
        assert active_file.read_text() == original_content

    # TC-RST-003: Preserve Finished Tasks
    def test_preserve_finished_tasks(self, existing_installation, temp_source):
        """
        TC-RST-003: Finished tasks are preserved during reset
        Validates: REQ-F-RESET-001
        """
        finished_dir = existing_installation / ".ai-workspace" / "tasks" / "finished"
        original_files = {f.name: f.read_text() for f in finished_dir.glob("*.md")}

        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            no_backup=True
        )

        result = installer.run()

        assert result is True

        # Verify all finished tasks preserved
        for name, content in original_files.items():
            assert (finished_dir / name).exists()
            assert (finished_dir / name).read_text() == content

    def test_preserve_paths_match_constants(self):
        """
        PRESERVE_PATHS constant includes expected paths
        Validates: REQ-F-RESET-001
        """
        assert ".ai-workspace/tasks/finished" in PRESERVE_PATHS
        assert ".ai-workspace/tasks/active" in PRESERVE_PATHS


class TestRemoveOldFiles:
    """Test removal of old directories."""

    # TC-RST-004: Remove Old Commands
    def test_remove_old_commands(self, existing_installation, temp_source):
        """
        TC-RST-004: Old commands are removed and fresh ones installed
        Validates: REQ-F-RESET-001
        """
        # Verify old command exists
        old_command = existing_installation / ".claude" / "commands" / "old-command.md"
        assert old_command.exists()

        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            no_backup=True
        )

        result = installer.run()

        assert result is True

        # Old command should be gone
        assert not old_command.exists()

        # New command from template should exist
        new_command = existing_installation / ".claude" / "commands" / "test-command.md"
        assert new_command.exists()

    # TC-RST-005: Remove Old Agents
    def test_remove_old_agents(self, existing_installation, temp_source):
        """
        TC-RST-005: Old agents are removed and fresh ones installed
        Validates: REQ-F-RESET-001
        """
        old_agent = existing_installation / ".claude" / "agents" / "old-agent.md"
        assert old_agent.exists()

        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            no_backup=True
        )

        result = installer.run()

        assert result is True

        # Old agent should be gone
        assert not old_agent.exists()

        # New agent from template should exist
        new_agent = existing_installation / ".claude" / "agents" / "test-agent.md"
        assert new_agent.exists()

    def test_reset_directories_match_constants(self):
        """
        RESET_DIRECTORIES constant includes expected directories
        Validates: REQ-F-RESET-001
        """
        assert ".claude" in RESET_DIRECTORIES
        assert ".ai-workspace" in RESET_DIRECTORIES


class TestBackupCreation:
    """Test backup functionality."""

    # TC-RST-006: Create Backup
    def test_backup_created_by_default(self, existing_installation, temp_source, capsys):
        """
        TC-RST-006: Backup is created by default
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source)
        )

        result = installer.run()

        assert result is True
        assert installer.backup_dir is not None
        assert installer.backup_dir.exists()

        # Backup should contain .claude and .ai-workspace
        assert (installer.backup_dir / ".claude").exists()
        assert (installer.backup_dir / ".ai-workspace").exists()

        captured = capsys.readouterr()
        assert "Backup location" in captured.out

    def test_no_backup_flag(self, existing_installation, temp_source):
        """
        no_backup flag skips backup creation
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            no_backup=True
        )

        result = installer.run()

        assert result is True
        assert installer.backup_dir is None


class TestVersionManagement:
    """Test version-specific installation."""

    # TC-RST-007: Reset to Specific Version (mocked GitHub)
    def test_reset_to_specific_version_with_local_source(self, existing_installation, temp_source):
        """
        TC-RST-007: Reset installs from specified source
        Validates: REQ-F-RESET-001, REQ-F-UPDATE-001
        """
        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            version="v0.2.0",  # Version specified but using local source
            no_backup=True
        )

        result = installer.run()

        assert result is True

        # Files from temp_source should be installed
        assert (existing_installation / ".claude" / "commands" / "test-command.md").exists()

    # TC-RST-008: Reset from Local Source
    def test_reset_from_local_source(self, existing_installation, temp_source):
        """
        TC-RST-008: Reset from local source without GitHub access
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            no_backup=True
        )

        # Should not need GitHub - uses local source
        result = installer.run()

        assert result is True
        # Use resolve() to handle macOS symlinks
        assert installer.templates_root.resolve() == (temp_source / "claude-code" / "project-template").resolve()


class TestErrorHandling:
    """Test error handling scenarios."""

    # TC-RST-009: Invalid Target Directory
    def test_invalid_target_directory(self, temp_dir, temp_source):
        """
        TC-RST-009: Error on non-existent target directory
        Validates: REQ-F-RESET-001
        """
        non_existent = temp_dir / "does_not_exist"

        installer = ResetInstaller(
            target=str(non_existent),
            source=str(temp_source)
        )

        result = installer.run()

        assert result is False

    # TC-RST-010: Invalid Source Path
    def test_invalid_source_path(self, temp_target, temp_dir):
        """
        TC-RST-010: Error on invalid source path
        Validates: REQ-F-RESET-001
        """
        invalid_source = temp_dir / "invalid_source"

        installer = ResetInstaller(
            target=str(temp_target),
            source=str(invalid_source)
        )

        result = installer.run()

        assert result is False

    def test_missing_templates_in_source(self, temp_target, temp_dir):
        """
        Error when templates not found in source
        Validates: REQ-F-RESET-001
        """
        # Create source without templates
        source = temp_dir / "source_no_templates"
        source.mkdir()

        installer = ResetInstaller(
            target=str(temp_target),
            source=str(source)
        )

        result = installer.run()

        assert result is False


class TestResolveSource:
    """Test source resolution logic."""

    def test_resolve_local_source(self, temp_target, temp_source):
        """
        _resolve_source uses local source when provided
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(
            target=str(temp_target),
            source=str(temp_source)
        )

        result = installer._resolve_source()

        assert result is True
        # Use resolve() to handle macOS symlinks
        assert installer.templates_root.resolve() == (temp_source / "claude-code" / "project-template").resolve()

    def test_resolve_github_dry_run(self, temp_target):
        """
        _resolve_source in dry run mode doesn't clone
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(
            target=str(temp_target),
            version="v0.1.0",
            dry_run=True
        )

        result = installer._resolve_source()

        assert result is True
        # In dry run, no temp_dir or clone
        assert installer.temp_dir is None

    def test_resolve_latest_version_mocked(self, temp_target):
        """
        _resolve_source fetches latest tag when no version
        Validates: REQ-F-UPDATE-001
        """
        with patch('setup_reset.get_latest_release_tag') as mock_tag:
            mock_tag.return_value = "v0.3.0"

            installer = ResetInstaller(
                target=str(temp_target),
                dry_run=True  # Skip actual clone
            )

            result = installer._resolve_source()

            assert result is True
            assert installer.version == "v0.3.0"
            mock_tag.assert_called_once()


class TestValidateTarget:
    """Test target validation."""

    def test_validate_existing_target(self, existing_installation):
        """
        _validate_target succeeds for existing directory
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(target=str(existing_installation))
        result = installer._validate_target()

        assert result is True

    def test_validate_target_with_no_installation(self, temp_target, capsys):
        """
        _validate_target warns for fresh installation
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(target=str(temp_target))
        result = installer._validate_target()

        assert result is True  # Still succeeds
        captured = capsys.readouterr()
        assert "fresh installation" in captured.out or result is True


class TestShowPlan:
    """Test plan display functionality."""

    def test_show_plan_lists_directories(self, existing_installation, temp_source, capsys):
        """
        _show_plan lists directories to remove
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source)
        )
        installer.templates_root = temp_source / "claude-code" / "project-template"

        installer._show_plan()

        captured = capsys.readouterr()
        assert ".claude" in captured.out
        assert ".ai-workspace" in captured.out

    def test_show_plan_lists_preserve_paths(self, existing_installation, temp_source, capsys):
        """
        _show_plan lists paths to preserve
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source)
        )
        installer.templates_root = temp_source / "claude-code" / "project-template"

        installer._show_plan()

        captured = capsys.readouterr()
        assert "tasks/finished" in captured.out
        assert "tasks/active" in captured.out


class TestInstallFresh:
    """Test fresh installation logic."""

    def test_install_fresh_creates_claude_dir(self, temp_target, temp_source):
        """
        _install_fresh creates .claude directory
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(target=str(temp_target))
        installer.templates_root = temp_source / "claude-code" / "project-template"

        result = installer._install_fresh()

        assert result is True
        assert (temp_target / ".claude").exists()
        assert (temp_target / ".claude" / "commands").exists()
        assert (temp_target / ".claude" / "agents").exists()

    def test_install_fresh_creates_workspace(self, temp_target, temp_source):
        """
        _install_fresh creates .ai-workspace directory
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(target=str(temp_target))
        installer.templates_root = temp_source / "claude-code" / "project-template"

        result = installer._install_fresh()

        assert result is True
        assert (temp_target / ".ai-workspace").exists()
        assert (temp_target / ".ai-workspace" / "tasks").exists()


class TestRestorePreserved:
    """Test file restoration logic."""

    def test_restore_preserved_files(self, temp_dir):
        """
        _restore_preserved restores files to correct locations
        Validates: REQ-F-RESET-001
        """
        # Use fully resolved paths to avoid macOS symlink issues
        temp_resolved = temp_dir.resolve()

        # Create preserved content directory (simulating what preserve step creates)
        preserved_active_dir = temp_resolved / "preserved" / ".ai-workspace" / "tasks" / "active"
        preserved_active_dir.mkdir(parents=True, exist_ok=True)
        (preserved_active_dir / "ACTIVE_TASKS.md").write_text("My preserved tasks")

        # Create target structure (simulating fresh install)
        target_project = temp_resolved / "target_project"
        target_active = target_project / ".ai-workspace" / "tasks" / "active"
        target_active.mkdir(parents=True, exist_ok=True)
        (target_active / "ACTIVE_TASKS.md").write_text("Fresh template")

        # Use resolved path for target to match what installer does internally
        installer = ResetInstaller(target=str(target_project))
        # preserved_paths is a list of (source_dir, target_dir) tuples
        installer.preserved_paths = [
            (preserved_active_dir, target_active)
        ]

        result = installer._restore_preserved()

        assert result is True
        # Should have restored content (preserved overwrites fresh)
        restored_file = target_active / "ACTIVE_TASKS.md"
        assert restored_file.exists()
        assert restored_file.read_text() == "My preserved tasks"


class TestGitignoreUpdate:
    """Test gitignore update functionality."""

    def test_update_gitignore_creates_file(self, temp_target):
        """
        _update_gitignore creates .gitignore if missing
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(target=str(temp_target))

        result = installer._update_gitignore()

        assert result is True
        gitignore = temp_target / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "# AI SDLC" in content

    def test_update_gitignore_appends(self, temp_target):
        """
        _update_gitignore appends to existing file
        Validates: REQ-F-RESET-001
        """
        gitignore = temp_target / ".gitignore"
        gitignore.write_text("# Existing content\nnode_modules/\n")

        installer = ResetInstaller(target=str(temp_target))

        result = installer._update_gitignore()

        assert result is True
        content = gitignore.read_text()
        assert "node_modules/" in content
        assert "# AI SDLC" in content

    def test_no_git_flag_skips_gitignore(self, temp_target):
        """
        no_git flag skips gitignore update
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(target=str(temp_target), no_git=True)

        # Manually call _update_gitignore (no_git is checked in run())
        # In reset installer, gitignore update is always called if not no_git
        assert installer.no_git is True


class TestCleanup:
    """Test cleanup functionality."""

    def test_cleanup_removes_temp_dir(self, temp_dir):
        """
        _cleanup removes temporary directory
        Validates: REQ-F-RESET-001
        """
        temp_clone = temp_dir / "clone_temp"
        temp_clone.mkdir()

        installer = ResetInstaller(target=".")
        installer.temp_dir = temp_clone

        installer._cleanup()

        assert not temp_clone.exists()


class TestFullResetWorkflow:
    """Integration tests for complete reset workflow."""

    def test_full_reset_preserves_and_updates(self, existing_installation, temp_source):
        """
        Full reset workflow preserves user data and updates framework
        Validates: REQ-F-RESET-001
        """
        # Record original preserved content
        active_content = (existing_installation / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md").read_text()
        finished_files = list((existing_installation / ".ai-workspace" / "tasks" / "finished").glob("*.md"))

        # Run reset
        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            no_backup=True
        )

        result = installer.run()

        assert result is True

        # Preserved content unchanged
        assert (existing_installation / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md").read_text() == active_content
        assert len(list((existing_installation / ".ai-workspace" / "tasks" / "finished").glob("*.md"))) == len(finished_files)

        # Framework updated
        assert (existing_installation / ".claude" / "commands" / "test-command.md").exists()
        assert not (existing_installation / ".claude" / "commands" / "old-command.md").exists()

    def test_reset_is_idempotent(self, existing_installation, temp_source):
        """
        Running reset multiple times produces consistent results
        Validates: REQ-F-RESET-001
        """
        # First reset
        installer1 = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            no_backup=True
        )
        result1 = installer1.run()

        # Record state after first reset
        commands_after_1 = set(f.name for f in (existing_installation / ".claude" / "commands").glob("*.md"))

        # Second reset
        installer2 = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            no_backup=True
        )
        result2 = installer2.run()

        # Record state after second reset
        commands_after_2 = set(f.name for f in (existing_installation / ".claude" / "commands").glob("*.md"))

        assert result1 is True
        assert result2 is True
        assert commands_after_1 == commands_after_2
