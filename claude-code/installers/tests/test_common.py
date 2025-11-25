"""
Tests for installers/common.py

Validates: REQ-F-WORKSPACE-001, REQ-F-CMD-001, REQ-F-RESET-001, REQ-F-PLUGIN-004
Test Cases: TC-COM-001 through TC-COM-012
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add installers to path
# claude-code/installers/tests/test_*.py -> parent is installers directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import InstallerBase, get_ai_sdlc_version, get_latest_release_tag, print_banner


class TestInstallerBase:
    """Test suite for InstallerBase class."""

    # TC-COM-001: validate_target - Valid Directory
    def test_validate_target_existing_directory(self, temp_target):
        """
        TC-COM-001: validate_target with valid existing directory
        Validates: REQ-F-WORKSPACE-001
        """
        installer = InstallerBase(target=str(temp_target))
        result = installer.validate_target()

        assert result is True
        assert temp_target.exists()

    # TC-COM-002: validate_target - Non-existent Directory (auto-create)
    def test_validate_target_creates_directory(self, temp_dir):
        """
        TC-COM-002: validate_target creates non-existent directory
        Validates: REQ-F-WORKSPACE-001
        """
        new_dir = temp_dir / "new_project"
        assert not new_dir.exists()

        installer = InstallerBase(target=str(new_dir))
        result = installer.validate_target()

        assert result is True
        assert new_dir.exists()

    def test_validate_target_permission_error(self, temp_dir):
        """
        validate_target handles permission errors gracefully
        Validates: REQ-F-WORKSPACE-001
        """
        # Create a path that can't be created (invalid path)
        invalid_path = "/root/cannot_create_here/test" if os.name != 'nt' else "Z:\\invalid\\path"

        installer = InstallerBase(target=invalid_path)
        result = installer.validate_target()

        # Should return False or True depending on permissions
        # The point is it doesn't crash
        assert result in [True, False]

    # TC-COM-003: validate_templates - Valid Templates
    def test_validate_templates_valid(self, project_root):
        """
        TC-COM-003: validate_templates with valid templates directory
        Validates: REQ-F-WORKSPACE-001
        """
        installer = InstallerBase()
        # Point to actual templates
        installer.templates_root = project_root / "claude-code" / "project-template"
        result = installer.validate_templates()

        assert result is True

    def test_validate_templates_missing(self, temp_dir):
        """
        validate_templates returns False for missing templates
        Validates: REQ-F-WORKSPACE-001
        """
        installer = InstallerBase()
        installer.templates_root = temp_dir / "nonexistent"
        result = installer.validate_templates()

        assert result is False

    # TC-COM-004: copy_directory - Normal Copy
    def test_copy_directory_normal(self, temp_dir):
        """
        TC-COM-004: copy_directory performs normal copy
        Validates: REQ-F-WORKSPACE-001, REQ-F-CMD-001
        """
        # Create source with files
        source = temp_dir / "source"
        source.mkdir()
        (source / "file1.txt").write_text("content1")
        (source / "subdir").mkdir()
        (source / "subdir" / "file2.txt").write_text("content2")

        # Copy to destination
        dest = temp_dir / "destination"
        installer = InstallerBase(target=str(temp_dir))
        result = installer.copy_directory(source, dest, "test directory")

        assert result is True
        assert dest.exists()
        assert (dest / "file1.txt").exists()
        assert (dest / "file1.txt").read_text() == "content1"
        assert (dest / "subdir" / "file2.txt").exists()
        assert (dest / "subdir" / "file2.txt").read_text() == "content2"

    # TC-COM-005: copy_directory - Force Overwrite
    def test_copy_directory_force_overwrite(self, temp_dir):
        """
        TC-COM-005: copy_directory with force overwrites existing
        Validates: REQ-F-WORKSPACE-001
        """
        # Create source
        source = temp_dir / "source"
        source.mkdir()
        (source / "new_file.txt").write_text("new content")

        # Create existing destination
        dest = temp_dir / "destination"
        dest.mkdir()
        (dest / "old_file.txt").write_text("old content")

        installer = InstallerBase(target=str(temp_dir), force=True)
        result = installer.copy_directory(source, dest)

        assert result is True
        assert (dest / "new_file.txt").exists()
        assert not (dest / "old_file.txt").exists()

    # TC-COM-006: copy_directory - Skip Existing
    def test_copy_directory_skip_existing(self, temp_dir):
        """
        TC-COM-006: copy_directory without force skips existing
        Validates: REQ-F-WORKSPACE-001
        """
        # Create source and existing destination
        source = temp_dir / "source"
        source.mkdir()
        (source / "file.txt").write_text("new")

        dest = temp_dir / "destination"
        dest.mkdir()
        (dest / "existing.txt").write_text("existing")

        installer = InstallerBase(target=str(temp_dir), force=False)
        result = installer.copy_directory(source, dest)

        assert result is False
        # Original content preserved
        assert (dest / "existing.txt").exists()
        assert (dest / "existing.txt").read_text() == "existing"

    def test_copy_directory_source_not_found(self, temp_dir):
        """
        copy_directory returns False for missing source
        Validates: REQ-F-WORKSPACE-001
        """
        installer = InstallerBase(target=str(temp_dir))
        result = installer.copy_directory(
            temp_dir / "nonexistent",
            temp_dir / "dest"
        )

        assert result is False

    # TC-COM-007: update_gitignore - Add Entries
    def test_update_gitignore_add_entries(self, temp_target):
        """
        TC-COM-007: update_gitignore adds entries correctly
        Validates: REQ-F-WORKSPACE-001
        """
        installer = InstallerBase(target=str(temp_target))
        result = installer.update_gitignore(
            [".ai-workspace/session/", "*.bak"],
            section_name="AI SDLC"
        )

        assert result is True
        gitignore = temp_target / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "# AI SDLC" in content
        assert ".ai-workspace/session/" in content
        assert "*.bak" in content

    def test_update_gitignore_existing_file(self, mock_gitignore, temp_target):
        """
        update_gitignore appends to existing .gitignore
        Validates: REQ-F-WORKSPACE-001
        """
        installer = InstallerBase(target=str(temp_target))
        result = installer.update_gitignore(["new_entry/"], section_name="Test Section")

        assert result is True
        content = mock_gitignore.read_text()
        # Original content preserved
        assert "node_modules/" in content
        # New content added
        assert "# Test Section" in content
        assert "new_entry/" in content

    def test_update_gitignore_skip_duplicate_section(self, temp_target):
        """
        update_gitignore skips if section already exists
        Validates: REQ-F-WORKSPACE-001
        """
        # Create gitignore with existing section
        gitignore = temp_target / ".gitignore"
        gitignore.write_text("# AI SDLC\nexisting_entry/\n")

        installer = InstallerBase(target=str(temp_target))
        result = installer.update_gitignore(["new_entry/"], section_name="AI SDLC")

        assert result is True
        content = gitignore.read_text()
        # Should not add new entry if section exists
        assert content.count("# AI SDLC") == 1

    def test_update_gitignore_no_git_flag(self, temp_target):
        """
        update_gitignore respects no_git flag
        Validates: REQ-F-WORKSPACE-001
        """
        installer = InstallerBase(target=str(temp_target), no_git=True)
        result = installer.update_gitignore(["entry/"], section_name="Test")

        assert result is True
        # .gitignore should not be created
        assert not (temp_target / ".gitignore").exists()

    # TC-COM-008: backup_file - Creates Backup
    def test_backup_file_creates_backup(self, temp_target):
        """
        TC-COM-008: backup_file creates timestamped backup
        Validates: REQ-F-RESET-001
        """
        # Create file to backup
        original = temp_target / "config.yml"
        original.write_text("original content")

        installer = InstallerBase(target=str(temp_target))
        backup_path = installer.backup_file(original)

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "original content"
        assert ".backup." in backup_path.name
        # Original unchanged
        assert original.exists()
        assert original.read_text() == "original content"

    def test_backup_file_nonexistent(self, temp_target):
        """
        backup_file returns None for nonexistent file
        Validates: REQ-F-RESET-001
        """
        installer = InstallerBase(target=str(temp_target))
        result = installer.backup_file(temp_target / "nonexistent.txt")

        assert result is None

    def test_copy_file_normal(self, temp_dir):
        """
        copy_file copies single file correctly
        Validates: REQ-F-WORKSPACE-001
        """
        source = temp_dir / "source.txt"
        source.write_text("file content")
        dest = temp_dir / "subdir" / "dest.txt"

        installer = InstallerBase(target=str(temp_dir))
        result = installer.copy_file(source, dest)

        assert result is True
        assert dest.exists()
        assert dest.read_text() == "file content"

    def test_copy_file_skip_existing(self, temp_dir):
        """
        copy_file skips existing file without force
        Validates: REQ-F-WORKSPACE-001
        """
        source = temp_dir / "source.txt"
        source.write_text("new content")
        dest = temp_dir / "dest.txt"
        dest.write_text("existing content")

        installer = InstallerBase(target=str(temp_dir), force=False)
        result = installer.copy_file(source, dest)

        assert result is False
        assert dest.read_text() == "existing content"

    def test_create_file_from_template(self, temp_target):
        """
        create_file_from_template creates file with replacements
        Validates: REQ-F-WORKSPACE-001
        """
        installer = InstallerBase(target=str(temp_target))
        dest = temp_target / "generated.txt"

        result = installer.create_file_from_template(
            "Hello {{NAME}}, version {{VERSION}}",
            dest,
            replacements={"{{NAME}}": "World", "{{VERSION}}": "1.0.0"}
        )

        assert result is True
        assert dest.exists()
        assert dest.read_text() == "Hello World, version 1.0.0"

    def test_create_file_from_template_skip_existing(self, temp_target):
        """
        create_file_from_template skips existing without force
        Validates: REQ-F-WORKSPACE-001
        """
        dest = temp_target / "existing.txt"
        dest.write_text("original")

        installer = InstallerBase(target=str(temp_target), force=False)
        result = installer.create_file_from_template("new content", dest)

        assert result is False
        assert dest.read_text() == "original"

    def test_print_section(self, temp_target, capsys):
        """
        print_section outputs formatted header
        """
        installer = InstallerBase(target=str(temp_target))
        installer.print_section("Test Section")

        captured = capsys.readouterr()
        assert "Test Section" in captured.out
        assert "=" in captured.out

    def test_print_success(self, temp_target, capsys):
        """
        print_success outputs success message with checkmark
        """
        installer = InstallerBase(target=str(temp_target))
        installer.print_success("Success message")

        captured = capsys.readouterr()
        assert "Success message" in captured.out

    def test_print_error(self, temp_target, capsys):
        """
        print_error outputs error message with X
        """
        installer = InstallerBase(target=str(temp_target))
        installer.print_error("Error message")

        captured = capsys.readouterr()
        assert "Error message" in captured.out


class TestVersionUtilities:
    """Test suite for version utility functions."""

    # TC-COM-009: get_ai_sdlc_version - From Git
    def test_get_ai_sdlc_version_from_git(self):
        """
        TC-COM-009: get_ai_sdlc_version returns git tag
        Validates: REQ-F-PLUGIN-004
        """
        version = get_ai_sdlc_version()

        # Should return a version string or "unknown"
        assert isinstance(version, str)
        assert len(version) > 0
        # If in git repo with tags, should start with 'v' or be 'unknown'
        assert version == "unknown" or version[0] in "v0123456789"

    # TC-COM-010: get_ai_sdlc_version - No Git
    def test_get_ai_sdlc_version_no_git(self):
        """
        TC-COM-010: get_ai_sdlc_version returns 'unknown' without git
        Validates: REQ-F-PLUGIN-004
        """
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("git not found")
            version = get_ai_sdlc_version()

        assert version == "unknown"

    def test_get_ai_sdlc_version_git_error(self):
        """
        get_ai_sdlc_version handles git command failure
        Validates: REQ-F-PLUGIN-004
        """
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_run.return_value = mock_result
            version = get_ai_sdlc_version()

        assert version == "unknown"

    # TC-COM-011: get_latest_release_tag - From GitHub (mocked)
    def test_get_latest_release_tag_from_github(self):
        """
        TC-COM-011: get_latest_release_tag fetches from GitHub
        Validates: REQ-F-UPDATE-001, REQ-F-RESET-001
        """
        mock_output = """abc123\trefs/tags/v0.3.0
def456\trefs/tags/v0.2.0
ghi789\trefs/tags/v0.1.0
"""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = mock_output
            mock_run.return_value = mock_result

            tag = get_latest_release_tag("https://github.com/test/repo.git")

        assert tag == "v0.3.0"

    # TC-COM-012: get_latest_release_tag - Network Error
    def test_get_latest_release_tag_network_error(self):
        """
        TC-COM-012: get_latest_release_tag returns None on network error
        Validates: REQ-F-RESET-001
        """
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Network error")
            tag = get_latest_release_tag("https://github.com/test/repo.git")

        assert tag is None

    def test_get_latest_release_tag_local(self):
        """
        get_latest_release_tag from local repository
        Validates: REQ-F-RESET-001
        """
        # Test without URL (local mode)
        tag = get_latest_release_tag()

        # Should return a tag or None
        assert tag is None or isinstance(tag, str)

    def test_get_latest_release_tag_empty_result(self):
        """
        get_latest_release_tag handles empty results
        Validates: REQ-F-RESET-001
        """
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            tag = get_latest_release_tag("https://github.com/test/repo.git")

        assert tag is None

    def test_get_latest_release_tag_skips_dereferenced(self):
        """
        get_latest_release_tag skips ^{} dereferenced tags
        Validates: REQ-F-RESET-001
        """
        mock_output = """abc123\trefs/tags/v0.2.0^{}
def456\trefs/tags/v0.2.0
ghi789\trefs/tags/v0.1.0
"""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = mock_output
            mock_run.return_value = mock_result

            tag = get_latest_release_tag("https://github.com/test/repo.git")

        # Should skip v0.2.0^{} and return v0.2.0
        assert tag == "v0.2.0"


class TestPrintBanner:
    """Test suite for print_banner function."""

    def test_print_banner_output(self, capsys):
        """
        print_banner displays formatted banner with version
        """
        with patch('common.get_ai_sdlc_version', return_value="v1.0.0"):
            print_banner()

        captured = capsys.readouterr()
        assert "AI SDLC Method" in captured.out
        assert "v1.0.0" in captured.out


class TestInstallerBaseInitialization:
    """Test InstallerBase initialization."""

    def test_default_initialization(self):
        """
        InstallerBase initializes with defaults
        """
        installer = InstallerBase()

        assert installer.target == Path(".").resolve()
        assert installer.force is False
        assert installer.no_git is False

    def test_custom_initialization(self, temp_target):
        """
        InstallerBase accepts custom parameters
        """
        installer = InstallerBase(
            target=str(temp_target),
            force=True,
            no_git=True
        )

        # Use resolve() on both to handle symlinks (e.g., macOS /var -> /private/var)
        assert installer.target.resolve() == temp_target.resolve()
        assert installer.force is True
        assert installer.no_git is True

    def test_ai_sdlc_root_calculation(self):
        """
        InstallerBase correctly calculates ai_sdlc_root
        """
        installer = InstallerBase()

        # ai_sdlc_root should be parent of installers directory
        # Since installers are now in claude-code/installers/, ai_sdlc_root is claude-code
        assert installer.ai_sdlc_root.name == "claude-code"
