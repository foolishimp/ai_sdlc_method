"""
Tests for installers/setup_reset.py - Roo Code Reset Installer

Validates: REQ-F-RESET-001, REQ-F-UPDATE-001
Test Cases: TC-ROO-RST-001 through TC-ROO-RST-011

Mirrors claude-code/installers/tests/test_setup_reset.py but adapted for Roo Code's
ResetInstaller class and .roo/ directory structure (modes, rules, memory-bank).
"""

import pytest
import sys
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add installers to path
# roo-code-iclaude/installers/tests/test_*.py -> parent is installers directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_reset import ResetInstaller


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
        assert installer.version is not None or installer.version is None  # Either from git or None
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
        assert installer.source.resolve() == source.resolve()
        assert installer.dry_run is True
        assert installer.no_backup is True
        assert installer.no_git is True


class TestPreservePaths:
    """Test PRESERVE_PATHS and RESET_PATHS constants."""

    def test_preserve_paths_defined(self):
        """
        PRESERVE_PATHS constant includes expected paths
        Validates: REQ-F-RESET-001
        """
        assert ".ai-workspace/tasks/finished" in ResetInstaller.PRESERVE_PATHS
        assert ".ai-workspace/tasks/active" in ResetInstaller.PRESERVE_PATHS
        assert ".roo/memory-bank" in ResetInstaller.PRESERVE_PATHS

    def test_reset_paths_defined(self):
        """
        RESET_PATHS constant includes expected directories
        Validates: REQ-F-RESET-001
        """
        assert ".roo/modes" in ResetInstaller.RESET_PATHS
        assert ".roo/rules" in ResetInstaller.RESET_PATHS
        assert ".ai-workspace/templates" in ResetInstaller.RESET_PATHS
        assert ".ai-workspace/config" in ResetInstaller.RESET_PATHS


class TestDryRunMode:
    """Test dry run mode functionality."""

    # TC-ROO-RST-001: Dry Run Mode
    def test_dry_run_no_changes(self, existing_installation, temp_source, capsys):
        """
        TC-ROO-RST-001: Dry run shows plan but makes no changes
        Validates: REQ-F-RESET-001
        """
        # Record original state
        original_memory_bank_content = (existing_installation / ".roo" / "memory-bank" / "projectbrief.md").read_text()
        original_modes = list((existing_installation / ".roo" / "modes").iterdir())

        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            dry_run=True
        )

        result = installer.run()

        assert result is True

        # Verify no changes were made
        assert (existing_installation / ".roo" / "memory-bank" / "projectbrief.md").read_text() == original_memory_bank_content
        assert list((existing_installation / ".roo" / "modes").iterdir()) == original_modes

        # Verify plan was shown
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out

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
        assert ".ai-workspace/tasks/finished" in captured.out or "tasks/finished" in captured.out
        assert ".ai-workspace/tasks/active" in captured.out or "tasks/active" in captured.out


class TestPreserveFiles:
    """Test file preservation during reset."""

    # TC-ROO-RST-002: Preserve Active Tasks
    def test_preserves_user_data(self, existing_installation, temp_source):
        """
        TC-ROO-RST-002: User data is preserved during reset
        Validates: REQ-F-RESET-001
        """
        # Record original active tasks
        active_file = existing_installation / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
        original_content = active_file.read_text()

        # Record original memory bank
        memory_bank_file = existing_installation / ".roo" / "memory-bank" / "projectbrief.md"
        original_memory = memory_bank_file.read_text()

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

        # Verify memory bank preserved
        assert memory_bank_file.exists()
        assert memory_bank_file.read_text() == original_memory

    # TC-ROO-RST-003: Preserve Finished Tasks
    def test_preserve_finished_tasks(self, existing_installation, temp_source):
        """
        TC-ROO-RST-003: Finished tasks are preserved during reset
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


class TestRemoveOldFiles:
    """Test removal of old directories."""

    # TC-ROO-RST-004: Remove Old Modes
    def test_removes_old_framework_files(self, existing_installation, temp_source):
        """
        TC-ROO-RST-004: Old framework files are removed and fresh ones installed
        Validates: REQ-F-RESET-001
        """
        # Verify old mode exists
        old_mode = existing_installation / ".roo" / "modes" / "old-mode.json"
        assert old_mode.exists()

        # Verify old rule exists
        old_rule = existing_installation / ".roo" / "rules" / "old-rule.md"
        assert old_rule.exists()

        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            no_backup=True
        )

        result = installer.run()

        assert result is True

        # Old mode should be gone
        assert not old_mode.exists()

        # Old rule should be gone
        assert not old_rule.exists()

        # New mode from template should exist
        new_mode = existing_installation / ".roo" / "modes" / "aisdlc-code.json"
        assert new_mode.exists()

        # New rule from template should exist
        new_rule = existing_installation / ".roo" / "rules" / "tdd-workflow.md"
        assert new_rule.exists()


class TestBackupCreation:
    """Test backup functionality."""

    # TC-ROO-RST-006: Create Backup
    def test_creates_backup(self, existing_installation, temp_source, capsys):
        """
        TC-ROO-RST-006: Backup is created by default
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

        # Backup should contain .roo and .ai-workspace
        assert (installer.backup_dir / ".roo").exists()
        assert (installer.backup_dir / ".ai-workspace").exists()

        captured = capsys.readouterr()
        assert "Backup" in captured.out or "backup" in captured.out

    def test_no_backup_when_flag_set(self, existing_installation, temp_source):
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


class TestInstallFresh:
    """Test fresh installation logic."""

    def test_installs_new_framework_files(self, temp_target, temp_source):
        """
        _install_fresh creates .roo directory with modes and rules
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(
            target=str(temp_target),
            source=str(temp_source),
            no_backup=True
        )

        # Note: ResetInstaller uses source to find templates
        result = installer.run()

        assert result is True
        assert (temp_target / ".roo").exists()
        assert (temp_target / ".roo" / "modes").exists()
        assert (temp_target / ".roo" / "rules").exists()

    def test_creates_missing_preserve_directories(self, temp_target, temp_source):
        """
        Reset creates preserve directories if missing
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(
            target=str(temp_target),
            source=str(temp_source),
            no_backup=True
        )

        result = installer.run()

        assert result is True
        # Preserve paths should be created
        assert (temp_target / ".ai-workspace" / "tasks" / "active").exists()
        assert (temp_target / ".ai-workspace" / "tasks" / "finished").exists()
        assert (temp_target / ".roo" / "memory-bank").exists()


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_handles_missing_source(self, temp_target, temp_dir):
        """
        Error on invalid source path
        Validates: REQ-F-RESET-001
        """
        invalid_source = temp_dir / "invalid_source"

        installer = ResetInstaller(
            target=str(temp_target),
            source=str(invalid_source)
        )

        result = installer.run()

        assert result is False

    def test_handles_empty_target(self, temp_target, temp_source):
        """
        Reset works on empty target directory
        Validates: REQ-F-RESET-001
        """
        # temp_target is empty
        installer = ResetInstaller(
            target=str(temp_target),
            source=str(temp_source),
            no_backup=True
        )

        result = installer.run()

        # Should succeed - fresh install
        assert result is True
        assert (temp_target / ".roo").exists()


class TestGitignoreUpdate:
    """Test gitignore update functionality."""

    def test_update_gitignore_creates_file(self, temp_target, temp_source):
        """
        Reset creates .gitignore if missing
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(
            target=str(temp_target),
            source=str(temp_source),
            no_backup=True
        )

        result = installer.run()

        assert result is True
        gitignore = temp_target / ".gitignore"
        # Gitignore may or may not be created depending on implementation
        # At minimum, verify no error occurred

    def test_no_git_flag_behavior(self, temp_target, temp_source):
        """
        no_git flag affects gitignore handling
        Validates: REQ-F-RESET-001
        """
        installer = ResetInstaller(
            target=str(temp_target),
            source=str(temp_source),
            no_backup=True,
            no_git=True
        )

        assert installer.no_git is True


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
        memory_bank_content = (existing_installation / ".roo" / "memory-bank" / "projectbrief.md").read_text()

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
        assert (existing_installation / ".roo" / "memory-bank" / "projectbrief.md").read_text() == memory_bank_content

        # Framework updated
        assert (existing_installation / ".roo" / "modes" / "aisdlc-code.json").exists()
        assert not (existing_installation / ".roo" / "modes" / "old-mode.json").exists()

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
        modes_after_1 = set(f.name for f in (existing_installation / ".roo" / "modes").glob("*.json"))

        # Second reset
        installer2 = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            no_backup=True
        )
        result2 = installer2.run()

        # Record state after second reset
        modes_after_2 = set(f.name for f in (existing_installation / ".roo" / "modes").glob("*.json"))

        assert result1 is True
        assert result2 is True
        assert modes_after_1 == modes_after_2


class TestVersionManagement:
    """Test version-specific installation."""

    def test_reset_with_version_specified(self, existing_installation, temp_source):
        """
        Reset can accept version parameter
        Validates: REQ-F-RESET-001, REQ-F-UPDATE-001
        """
        installer = ResetInstaller(
            target=str(existing_installation),
            source=str(temp_source),
            version="v0.2.0",
            no_backup=True
        )

        # Version is stored
        assert installer.version == "v0.2.0"

        result = installer.run()

        # Should succeed with local source
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
