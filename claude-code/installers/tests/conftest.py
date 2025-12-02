"""
Shared fixtures for AISDLC installer tests.

Validates: REQ-F-PLUGIN-001, REQ-F-WORKSPACE-001
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_target():
    """Create a temporary directory for installation target."""
    temp_dir = tempfile.mkdtemp(prefix="aisdlc-test-")
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_target_with_settings(temp_target):
    """Create a temp directory with existing settings.json."""
    claude_dir = temp_target / ".claude"
    claude_dir.mkdir(parents=True)

    settings_file = claude_dir / "settings.json"
    settings_file.write_text('{"existingSetting": true, "enabledPlugins": {"other@other": true}}')

    return temp_target


@pytest.fixture
def temp_target_with_workspace(temp_target):
    """Create a temp directory with existing .ai-workspace."""
    workspace_dir = temp_target / ".ai-workspace" / "tasks" / "active"
    workspace_dir.mkdir(parents=True)

    active_tasks = workspace_dir / "ACTIVE_TASKS.md"
    active_tasks.write_text("# My Existing Tasks\n\nTask #1: Important work")

    finished_dir = temp_target / ".ai-workspace" / "tasks" / "finished"
    finished_dir.mkdir(parents=True)

    finished_task = finished_dir / "20251201_task.md"
    finished_task.write_text("# Completed Task\n\nDone!")

    return temp_target


@pytest.fixture
def temp_target_with_invalid_json(temp_target):
    """Create a temp directory with invalid settings.json."""
    claude_dir = temp_target / ".claude"
    claude_dir.mkdir(parents=True)

    settings_file = claude_dir / "settings.json"
    settings_file.write_text('{ invalid json }')

    return temp_target
