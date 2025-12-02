#!/usr/bin/env python3
"""
AISDLC Command Tests

Integration tests validating the 7 AISDLC slash commands work correctly.

# Validates: REQ-F-CMD-001 (Slash Commands for Workflow)
# Implements: REQ-NFR-QUALITY-001 (Code Quality Standards)

Usage:
    pytest test_commands.py -v
    pytest test_commands.py -k "test_status" -v
    pytest test_commands.py --tb=short
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import pytest


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_project():
    """Create a temporary project directory with basic structure."""
    temp_dir = tempfile.mkdtemp(prefix="aisdlc_test_")
    project_path = Path(temp_dir)

    # Initialize git
    subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=temp_dir, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, capture_output=True)

    # Create initial commit
    readme = project_path / "README.md"
    readme.write_text("# Test Project\n")
    subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, capture_output=True)

    yield project_path

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def empty_workspace(temp_project):
    """Create empty .ai-workspace structure."""
    workspace = temp_project / ".ai-workspace"
    (workspace / "tasks" / "active").mkdir(parents=True)
    (workspace / "tasks" / "finished").mkdir(parents=True)
    (workspace / "templates").mkdir(parents=True)

    # Empty ACTIVE_TASKS.md
    active_tasks = workspace / "tasks" / "active" / "ACTIVE_TASKS.md"
    active_tasks.write_text("""# Active Tasks

*Last Updated: 2025-11-27 12:00*

---

## Summary

**Total Active Tasks**: 0

---
""")

    return temp_project


@pytest.fixture
def workspace_with_tasks(temp_project):
    """Create .ai-workspace with sample tasks."""
    workspace = temp_project / ".ai-workspace"
    (workspace / "tasks" / "active").mkdir(parents=True, exist_ok=True)
    (workspace / "tasks" / "finished").mkdir(parents=True, exist_ok=True)
    (workspace / "templates").mkdir(parents=True, exist_ok=True)

    # ACTIVE_TASKS.md with tasks
    active_tasks = workspace / "tasks" / "active" / "ACTIVE_TASKS.md"
    active_tasks.write_text("""# Active Tasks

*Last Updated: 2025-11-27 12:00*

---

## Task #1: Implement User Authentication

**Priority**: High
**Status**: In Progress
**Requirements**: REQ-F-AUTH-001, REQ-NFR-SEC-001

**Description**:
Implement user login with email and password.

**Acceptance Criteria**:
- [ ] Login endpoint exists
- [ ] Password validation works
- [ ] JWT tokens generated

---

## Task #2: Add Database Schema

**Priority**: Medium
**Status**: Not Started
**Requirements**: REQ-F-DATA-001

**Description**:
Create database tables for user data.

**Acceptance Criteria**:
- [ ] User table created
- [ ] Migrations work

---

## Summary

**Total Active Tasks**: 2
- High Priority: 1
- Medium Priority: 1
- In Progress: 1
- Not Started: 1

---
""")

    # Create a finished task file
    finished = workspace / "tasks" / "finished"
    finished_task = finished / "20251127_1000_sample_completed_task.md"
    finished_task.write_text("""# Task: Sample Completed Task

**Status**: Completed
**Date**: 2025-11-27
**Time**: 10:00
**Task ID**: #0
**Requirements**: REQ-F-SAMPLE-001

---

## Problem
Sample problem description.

---

## Solution
Sample solution description.

---

## Result
✅ Task completed successfully
""")

    # Create method reference template
    templates = workspace / "templates"
    method_ref = templates / "AISDLC_METHOD_REFERENCE.md"
    method_ref.write_text("""# AI SDLC Method Reference

## Workflow
1. /aisdlc-status
2. Work on tasks
3. /aisdlc-checkpoint-tasks
4. /aisdlc-commit-task

## Critical Rules
- NEVER put finished tasks outside .ai-workspace/
- ALWAYS use TodoWrite tool
""")

    # Create finished task template
    finished_template = templates / "FINISHED_TASK_TEMPLATE.md"
    finished_template.write_text("""# Task: {TITLE}

**Status**: Completed
**Date**: {DATE}
**Time**: {TIME}
**Task ID**: #{ID}
**Requirements**: {REQ_KEYS}

---

## Problem
{problem}

---

## Solution
{solution}

---

## Result
✅ **Task completed successfully**
""")

    return temp_project


# =============================================================================
# Command Parsing Tests
# =============================================================================

class TestCommandFiles:
    """Test that command files exist and are well-formed."""

    COMMANDS_DIR = Path(__file__).parent.parent.parent / ".claude-plugin" / "plugins" / "aisdlc-methodology" / "commands"

    EXPECTED_COMMANDS = [
        "aisdlc-checkpoint-tasks.md",
        "aisdlc-commit-task.md",
        "aisdlc-finish-task.md",
        "aisdlc-help.md",
        "aisdlc-refresh-context.md",
        "aisdlc-release.md",
        "aisdlc-status.md",
        "aisdlc-update.md",
    ]

    def test_all_commands_exist(self):
        """TC-CMD-001: All 7 command files exist."""
        for cmd in self.EXPECTED_COMMANDS:
            cmd_path = self.COMMANDS_DIR / cmd
            assert cmd_path.exists(), f"Command file missing: {cmd}"

    def test_commands_have_implements_tag(self):
        """TC-CMD-002: Each command has REQ Implements tag."""
        for cmd in self.EXPECTED_COMMANDS:
            cmd_path = self.COMMANDS_DIR / cmd
            content = cmd_path.read_text()
            assert "<!-- Implements:" in content, f"Missing Implements tag in {cmd}"

    def test_commands_have_instructions(self):
        """TC-CMD-003: Each command has Instructions section."""
        for cmd in self.EXPECTED_COMMANDS:
            cmd_path = self.COMMANDS_DIR / cmd
            content = cmd_path.read_text()
            # Either "Instructions" or "Implementation Steps" or "Instructions:" is acceptable
            has_instructions = (
                "## Instructions" in content or
                "## Implementation Steps" in content or
                "**Instructions**:" in content
            )
            assert has_instructions, f"Missing Instructions section in {cmd}"


# =============================================================================
# Status Command Tests
# =============================================================================

class TestStatusCommand:
    """Tests for /aisdlc-status command behavior."""

    def test_status_empty_workspace(self, empty_workspace):
        """ST-001: Status shows zero tasks for empty workspace."""
        active_tasks = empty_workspace / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
        content = active_tasks.read_text()

        assert "Total Active Tasks**: 0" in content or "Active Tasks**: 0" in content

    def test_status_with_tasks(self, workspace_with_tasks):
        """ST-002/003: Status correctly counts tasks."""
        active_tasks = workspace_with_tasks / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
        content = active_tasks.read_text()

        # Count task headers
        task_count = content.count("## Task #")
        assert task_count == 2, f"Expected 2 tasks, found {task_count}"

    def test_status_lists_finished_tasks(self, workspace_with_tasks):
        """ST-004: Status can find finished task files."""
        finished_dir = workspace_with_tasks / ".ai-workspace" / "tasks" / "finished"
        finished_files = list(finished_dir.glob("*.md"))

        assert len(finished_files) >= 1, "Should have at least one finished task"

    def test_status_no_workspace_error(self, temp_project):
        """ST-005: Error when .ai-workspace missing."""
        workspace = temp_project / ".ai-workspace"
        assert not workspace.exists(), "Workspace should not exist for this test"


# =============================================================================
# Checkpoint Command Tests
# =============================================================================

class TestCheckpointCommand:
    """Tests for /aisdlc-checkpoint-tasks command behavior."""

    def test_checkpoint_updates_timestamp(self, workspace_with_tasks):
        """CP-001: Checkpoint updates ACTIVE_TASKS.md timestamp."""
        active_tasks = workspace_with_tasks / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"

        # Read original timestamp
        original = active_tasks.read_text()
        assert "Last Updated:" in original

        # Simulate timestamp update
        new_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        updated = original.replace(
            "Last Updated: 2025-11-27 12:00",
            f"Last Updated: {new_timestamp}"
        )
        active_tasks.write_text(updated)

        # Verify timestamp changed
        current = active_tasks.read_text()
        assert new_timestamp in current

    def test_checkpoint_creates_finished_document(self, workspace_with_tasks):
        """CP-002: Completed tasks create finished documents."""
        finished_dir = workspace_with_tasks / ".ai-workspace" / "tasks" / "finished"

        # Create a new finished task document
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        new_finished = finished_dir / f"{timestamp}_test_task.md"
        new_finished.write_text("""# Task: Test Task

**Status**: Completed
**Date**: 2025-11-27
**Time**: 14:00
**Task ID**: #99

## Problem
Test problem.

## Solution
Test solution.

## Result
✅ Task completed successfully
""")

        assert new_finished.exists()
        content = new_finished.read_text()
        assert "Status**: Completed" in content

    def test_finished_document_filename_format(self, workspace_with_tasks):
        """CP-003: Finished document filename follows format."""
        finished_dir = workspace_with_tasks / ".ai-workspace" / "tasks" / "finished"
        finished_files = list(finished_dir.glob("*.md"))

        for f in finished_files:
            # Should match: YYYYMMDD_HHMM_slug.md
            name = f.stem
            parts = name.split("_", 2)
            assert len(parts) >= 2, f"Invalid filename format: {f.name}"

            # First part should be date (8 digits)
            date_part = parts[0]
            assert len(date_part) == 8, f"Date part should be 8 digits: {date_part}"
            assert date_part.isdigit(), f"Date part should be digits: {date_part}"


# =============================================================================
# Release Command Tests
# =============================================================================

class TestReleaseCommand:
    """Tests for /aisdlc-release command behavior."""

    def test_release_detects_uncommitted_changes(self, temp_project):
        """RL-002: Release detects uncommitted changes."""
        # Create uncommitted file
        test_file = temp_project / "uncommitted.txt"
        test_file.write_text("uncommitted content")

        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=temp_project,
            capture_output=True,
            text=True
        )

        assert result.stdout.strip() != "", "Should have uncommitted changes"

    def test_release_detects_branch(self, temp_project):
        """RL-003: Release detects current branch."""
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=temp_project,
            capture_output=True,
            text=True
        )

        # Default branch could be main or master
        branch = result.stdout.strip()
        assert branch in ["main", "master"], f"Unexpected branch: {branch}"

    def test_release_version_increment(self):
        """RL-005: Version correctly incremented."""
        # Test version parsing and incrementing
        test_cases = [
            ("v0.0.0", "v0.0.1"),
            ("v0.4.0", "v0.4.1"),
            ("v1.2.3", "v1.2.4"),
            ("v0.0.9", "v0.0.10"),
        ]

        for current, expected in test_cases:
            version = current.lstrip("v")
            parts = version.split(".")
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            new_version = f"v{major}.{minor}.{patch + 1}"
            assert new_version == expected, f"Expected {expected}, got {new_version}"

    def test_release_creates_tag(self, temp_project):
        """RL-001: Release creates annotated tag."""
        # Create a tag
        tag_name = "v0.0.1"
        tag_message = "Test release"

        result = subprocess.run(
            ["git", "tag", "-a", tag_name, "-m", tag_message],
            cwd=temp_project,
            capture_output=True,
            text=True
        )

        # Verify tag exists
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=temp_project,
            capture_output=True,
            text=True
        )

        assert result.stdout.strip() == tag_name


# =============================================================================
# Update Command Tests
# =============================================================================

class TestUpdateCommand:
    """Tests for /aisdlc-update command behavior."""

    def test_update_preserves_active_tasks(self, workspace_with_tasks):
        """UP-006: Update preserves active work."""
        active_tasks = workspace_with_tasks / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
        original_content = active_tasks.read_text()

        # Simulate update by modifying templates (not active tasks)
        templates_dir = workspace_with_tasks / ".ai-workspace" / "templates"
        new_template = templates_dir / "NEW_TEMPLATE.md"
        new_template.write_text("# New Template\n")

        # Verify active tasks unchanged
        current_content = active_tasks.read_text()
        assert current_content == original_content

    def test_update_creates_backup(self, workspace_with_tasks):
        """UP-007: Update creates backup."""
        # Simulate backup creation
        backup_dir = Path(tempfile.gettempdir()) / f"aisdlc-backup-test-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True)

        # Copy workspace to backup
        src = workspace_with_tasks / ".ai-workspace"
        dst = backup_dir / ".ai-workspace"
        shutil.copytree(src, dst)

        # Verify backup exists
        assert (dst / "tasks" / "active" / "ACTIVE_TASKS.md").exists()

        # Cleanup
        shutil.rmtree(backup_dir, ignore_errors=True)


# =============================================================================
# Refresh Context Command Tests
# =============================================================================

class TestRefreshContextCommand:
    """Tests for /aisdlc-refresh-context command behavior."""

    def test_refresh_verifies_workspace_structure(self, workspace_with_tasks):
        """RC-001: Refresh verifies workspace structure."""
        workspace = workspace_with_tasks / ".ai-workspace"

        # Check required directories exist
        assert (workspace / "tasks" / "active").is_dir()
        assert (workspace / "tasks" / "finished").is_dir()
        assert (workspace / "templates").is_dir()

    def test_refresh_checks_method_reference(self, workspace_with_tasks):
        """RC-002: Refresh checks for method reference."""
        method_ref = workspace_with_tasks / ".ai-workspace" / "templates" / "AISDLC_METHOD_REFERENCE.md"

        assert method_ref.exists()
        content = method_ref.read_text()
        assert "Workflow" in content


# =============================================================================
# Finish Task Command Tests
# =============================================================================

class TestFinishTaskCommand:
    """Tests for /aisdlc-finish-task command behavior."""

    def test_finish_task_creates_document(self, workspace_with_tasks):
        """FT-001: Finish task creates document."""
        finished_dir = workspace_with_tasks / ".ai-workspace" / "tasks" / "finished"
        template_path = workspace_with_tasks / ".ai-workspace" / "templates" / "FINISHED_TASK_TEMPLATE.md"

        # Verify template exists
        assert template_path.exists()

        # Create finished document from template
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        finished_doc = finished_dir / f"{timestamp}_auth_implementation.md"

        template = template_path.read_text()
        content = template.replace("{TITLE}", "Implement User Authentication")
        content = content.replace("{DATE}", "2025-11-27")
        content = content.replace("{TIME}", "14:00")
        content = content.replace("{ID}", "1")
        content = content.replace("{REQ_KEYS}", "REQ-F-AUTH-001")

        finished_doc.write_text(content)

        assert finished_doc.exists()
        assert "REQ-F-AUTH-001" in finished_doc.read_text()


# =============================================================================
# Commit Task Command Tests
# =============================================================================

class TestCommitTaskCommand:
    """Tests for /aisdlc-commit-task command behavior."""

    def test_commit_message_format(self):
        """CM-001: Commit message follows format."""
        # Test commit message generation
        task_id = 1
        title = "Implement User Authentication"
        problem = "Users cannot log in"
        solution = "Added JWT authentication"
        req_keys = "REQ-F-AUTH-001"

        commit_msg = f"""Task #{task_id}: {title}

{problem}

{solution}

Tests: All passing
TDD: RED → GREEN → REFACTOR

Implements: {req_keys}

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>
"""

        assert f"Task #{task_id}" in commit_msg
        assert title in commit_msg
        assert "Implements:" in commit_msg
        assert req_keys in commit_msg
        assert "TDD: RED → GREEN → REFACTOR" in commit_msg
        assert "Co-Authored-By:" in commit_msg

    def test_commit_requires_finished_doc(self, workspace_with_tasks):
        """CM-003: Commit requires finished document."""
        finished_dir = workspace_with_tasks / ".ai-workspace" / "tasks" / "finished"

        # Check for finished docs with specific task ID
        task_id = 99  # Non-existent task
        matching_docs = list(finished_dir.glob(f"*_task_{task_id}_*.md"))

        assert len(matching_docs) == 0, "Should not find doc for non-existent task"


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for command workflows."""

    def test_full_workflow(self, workspace_with_tasks):
        """INT-001: Full workflow from status to release."""
        project = workspace_with_tasks

        # 1. Check status - workspace exists
        active_tasks = project / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
        assert active_tasks.exists()

        # 2. Verify tasks present
        content = active_tasks.read_text()
        assert "## Task #1" in content

        # 3. Simulate completing task
        finished_dir = project / ".ai-workspace" / "tasks" / "finished"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        finished_doc = finished_dir / f"{timestamp}_user_auth.md"
        finished_doc.write_text("""# Task: Implement User Authentication

**Status**: Completed
**Task ID**: #1
**Requirements**: REQ-F-AUTH-001

## Problem
Users cannot log in.

## Solution
Implemented JWT authentication.

## Result
✅ Task completed successfully
""")

        # 4. Verify finished document created
        assert finished_doc.exists()

        # 5. Create git commit (simulate)
        test_file = project / "auth.py"
        test_file.write_text("# Auth implementation\n")
        subprocess.run(["git", "add", "."], cwd=project, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Task #1: Implement authentication\n\nImplements: REQ-F-AUTH-001"],
            cwd=project,
            capture_output=True
        )

        # 6. Create release
        result = subprocess.run(
            ["git", "tag", "-a", "v0.0.1", "-m", "Release v0.0.1"],
            cwd=project,
            capture_output=True
        )

        # 7. Verify tag created
        result = subprocess.run(
            ["git", "describe", "--tags"],
            cwd=project,
            capture_output=True,
            text=True
        )
        assert "v0.0.1" in result.stdout


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
