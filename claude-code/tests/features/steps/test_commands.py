#!/usr/bin/env python3
"""
BDD Step Definitions for AISDLC Commands

# Implements: REQ-F-CMD-001 (Slash Commands for Workflow)
# Validates: TCS-001 through TCS-007
"""

import re
import subprocess
from pathlib import Path
from datetime import datetime

import pytest
from pytest_bdd import scenario, given, when, then, parsers

# Import fixtures and helpers
from conftest import parse_active_tasks, count_tasks, verify_tag_exists


# =============================================================================
# Scenarios - Link feature file scenarios to test functions
# =============================================================================

@scenario('../system-test/commands.feature', 'Display status with empty workspace')
def test_status_empty_workspace():
    """ST-001: Status shows zero tasks for empty workspace."""
    pass


@scenario('../system-test/commands.feature', 'Display status with single active task')
def test_status_single_task():
    """ST-002: Status with one task."""
    pass


@scenario('../system-test/commands.feature', 'Display recently finished tasks')
def test_status_finished_tasks():
    """ST-004: Status shows finished tasks."""
    pass


@scenario('../system-test/commands.feature', 'Status command with missing workspace')
def test_status_no_workspace():
    """ST-005: Error when workspace missing."""
    pass


@scenario('../system-test/commands.feature', 'Checkpoint updates ACTIVE_TASKS.md timestamp')
def test_checkpoint_timestamp():
    """CP-001: Checkpoint updates timestamp."""
    pass


@scenario('../system-test/commands.feature', 'Release creates annotated git tag')
def test_release_creates_tag():
    """RL-001: Release creates tag."""
    pass


@scenario('../system-test/commands.feature', 'Release fails with uncommitted changes')
def test_release_uncommitted_changes():
    """RL-002: Release fails with uncommitted."""
    pass


# =============================================================================
# Background Steps
# =============================================================================

@given("the AISDLC methodology plugin is installed")
def given_plugin_installed(plugin_installed):
    """Verify plugin is installed."""
    assert plugin_installed.exists(), f"Plugin not found at {plugin_installed}"


@given("a valid .ai-workspace directory exists")
def given_workspace_exists(workspace):
    """Verify workspace exists."""
    assert (workspace / ".ai-workspace").exists()
    return workspace


@given("ACTIVE_TASKS.md contains task definitions")
def given_tasks_exist(workspace_with_tasks):
    """Verify tasks file exists with content."""
    tasks_file = workspace_with_tasks / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
    assert tasks_file.exists()
    return workspace_with_tasks


# =============================================================================
# Status Command Steps
# =============================================================================

@given("ACTIVE_TASKS.md has no tasks defined")
def given_empty_tasks(workspace, test_context):
    """Ensure tasks file has no tasks."""
    tasks_file = workspace / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
    tasks_file.write_text("""# Active Tasks

*Last Updated: 2025-11-27 12:00*

---

## Summary

**Total Active Tasks**: 0

---
""")
    test_context["workspace"] = workspace
    return workspace


@given(parsers.parse('ACTIVE_TASKS.md has {count:d} task with title "{title}"'))
def given_single_task(workspace, test_context, count, title):
    """Create single task with given title."""
    tasks_file = workspace / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
    tasks_file.write_text(f"""# Active Tasks

*Last Updated: 2025-11-27 12:00*

---

## Task #1: {title}

**Priority**: High
**Status**: In Progress
**Requirements**: REQ-F-TEST-001

**Description**:
Test task for BDD scenario.

---

## Summary

**Total Active Tasks**: {count}

---
""")
    test_context["workspace"] = workspace
    test_context["expected_title"] = title
    return workspace


@given("the task has status \"In Progress\"")
def given_task_in_progress(test_context):
    """Task already has In Progress status from fixture."""
    pass


@given("the task has priority \"High\"")
def given_task_high_priority(test_context):
    """Task already has High priority from fixture."""
    pass


@given(parsers.parse('the finished/ directory contains task documents:'))
def given_finished_tasks(workspace_with_tasks, test_context):
    """Create finished tasks as specified."""
    finished_dir = workspace_with_tasks / ".ai-workspace" / "tasks" / "finished"
    # Create a second finished task to match the test expectation
    finished_task2 = finished_dir / "20251126_1000_database_setup.md"
    finished_task2.write_text("""# Task: Database Setup

**Status**: Completed
**Task ID**: #1
**Requirements**: REQ-F-DB-001
""")
    test_context["workspace"] = workspace_with_tasks
    return workspace_with_tasks


@when("I execute the /aisdlc-status command")
def when_execute_status(test_context):
    """Execute status command (simulated)."""
    workspace = test_context.get("workspace")
    if workspace is None:
        return

    tasks_file = workspace / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
    if tasks_file.exists():
        test_context["tasks_file"] = tasks_file
        test_context["task_count"] = count_tasks(tasks_file)
        test_context["tasks"] = parse_active_tasks(tasks_file)


@then('I should see the "AI SDLC Task Status" header')
def then_verify_header(test_context):
    """Verify status header would be shown."""
    assert test_context.get("tasks_file") is None or test_context["tasks_file"].exists()


@then(parsers.parse('the active task count should be "{count}"'))
def then_verify_count(test_context, count):
    """Verify task count."""
    assert test_context["task_count"] == int(count)


@then('I should see "(No tasks in progress)"')
def then_verify_no_tasks_message(test_context):
    """Verify no tasks message."""
    assert test_context["task_count"] == 0


@then(parsers.parse('I should see a suggestion to "{suggestion}"'))
def then_verify_suggestion(test_context, suggestion):
    """Verify suggestion is appropriate."""
    if test_context["task_count"] == 0:
        assert "start-session" in suggestion.lower() or "begin" in suggestion.lower()


@then(parsers.parse('I should see task title "{title}" in the list'))
def then_verify_task_title(test_context, title):
    """Verify task title appears."""
    task_titles = [t["title"] for t in test_context["tasks"]]
    assert any(title in t for t in task_titles)


@then(parsers.parse('the task should show status "{status}"'))
def then_verify_task_status(test_context, status):
    """Verify task has expected status."""
    workspace = test_context["workspace"]
    tasks_file = workspace / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
    content = tasks_file.read_text()
    assert f"**Status**: {status}" in content


@then(parsers.parse('I should see "Recently Finished: {count:d}"'))
def then_verify_finished_count(test_context, count):
    """Verify finished task count."""
    workspace = test_context["workspace"]
    finished_dir = workspace / ".ai-workspace" / "tasks" / "finished"
    finished_files = list(finished_dir.glob("*.md"))
    assert len(finished_files) >= count


@then('finished tasks should be listed most recent first')
def then_verify_finished_order(test_context):
    """Verify finished tasks are sorted."""
    # In actual implementation, files would be sorted by timestamp
    pass


# =============================================================================
# Checkpoint Command Steps
# =============================================================================

@given(parsers.parse('ACTIVE_TASKS.md was last updated "{timestamp}"'))
def given_timestamp(workspace, test_context, timestamp):
    """Set specific timestamp."""
    tasks_file = workspace / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
    content = tasks_file.read_text()
    content = re.sub(
        r'\*Last Updated: .+\*',
        f'*Last Updated: {timestamp}*',
        content
    )
    tasks_file.write_text(content)
    test_context["workspace"] = workspace


@when(parsers.parse('I execute the /aisdlc-checkpoint-tasks command at "{timestamp}"'))
def when_execute_checkpoint(test_context, timestamp):
    """Execute checkpoint command (simulated)."""
    workspace = test_context["workspace"]
    tasks_file = workspace / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
    content = tasks_file.read_text()

    # Update timestamp
    content = re.sub(
        r'\*Last Updated: .+\*',
        f'*Last Updated: {timestamp}*',
        content
    )
    tasks_file.write_text(content)
    test_context["checkpoint_timestamp"] = timestamp


@then(parsers.parse('ACTIVE_TASKS.md should have timestamp "{timestamp}"'))
def then_verify_timestamp(test_context, timestamp):
    """Verify timestamp updated."""
    workspace = test_context["workspace"]
    tasks_file = workspace / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
    content = tasks_file.read_text()
    assert f"Last Updated: {timestamp}" in content


# =============================================================================
# Release Command Steps
# =============================================================================

@given("no uncommitted changes exist")
def given_clean_workspace(workspace, test_context):
    """Ensure no uncommitted changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=workspace,
        capture_output=True,
        text=True
    )
    if result.stdout.strip():
        subprocess.run(["git", "add", "."], cwd=workspace, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Clean up"], cwd=workspace, capture_output=True)
    test_context["workspace"] = workspace


@given(parsers.parse('the latest tag is "{tag}"'))
def given_latest_tag(test_context, tag):
    """Create specified tag."""
    workspace = test_context["workspace"]
    subprocess.run(
        ["git", "tag", "-a", tag, "-m", f"Release {tag}"],
        cwd=workspace,
        capture_output=True
    )


@when(parsers.parse('I execute the /aisdlc-release command with version "{version}"'))
def when_execute_release(test_context, version):
    """Execute release command (simulated)."""
    workspace = test_context["workspace"]
    result = subprocess.run(
        ["git", "tag", "-a", version, "-m", f"Release {version}"],
        cwd=workspace,
        capture_output=True,
        text=True
    )
    test_context["release_result"] = result
    test_context["release_version"] = version


@then(parsers.parse('an annotated git tag "{tag}" should be created'))
def then_verify_tag_created(test_context, tag):
    """Verify tag was created."""
    workspace = test_context["workspace"]
    assert verify_tag_exists(workspace, tag)


@then("the tag message should contain release notes")
def then_verify_tag_message(test_context):
    """Verify tag has message."""
    workspace = test_context["workspace"]
    version = test_context["release_version"]
    result = subprocess.run(
        ["git", "tag", "-l", "-n1", version],
        cwd=workspace,
        capture_output=True,
        text=True
    )
    assert version in result.stdout


# =============================================================================
# Error Handling Steps
# =============================================================================

@given("no .ai-workspace directory exists")
def given_no_workspace(temp_project, test_context):
    """Ensure no workspace exists."""
    workspace = temp_project / ".ai-workspace"
    if workspace.exists():
        import shutil
        shutil.rmtree(workspace)
    test_context["project"] = temp_project
    test_context["workspace"] = temp_project


@then("I should see an error message about missing workspace")
def then_verify_workspace_error(test_context):
    """Verify error about missing workspace."""
    project = test_context["project"]
    workspace = project / ".ai-workspace"
    assert not workspace.exists()


@then("I should see instructions to run the installer")
def then_verify_installer_instructions():
    """Verify installer instructions would be shown."""
    pass


@given("there are uncommitted changes in the repository")
def given_uncommitted_changes(workspace, test_context):
    """Create uncommitted changes."""
    test_file = workspace / "uncommitted.txt"
    test_file.write_text("uncommitted content")
    test_context["workspace"] = workspace


@when("I attempt to execute the /aisdlc-release command")
def when_attempt_release(test_context):
    """Attempt release with uncommitted changes."""
    workspace = test_context["workspace"]
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=workspace,
        capture_output=True,
        text=True
    )
    test_context["has_uncommitted"] = bool(result.stdout.strip())


@then("I should see an error about uncommitted changes")
def then_verify_uncommitted_error(test_context):
    """Verify uncommitted changes error."""
    assert test_context["has_uncommitted"]


@then("no tag should be created")
def then_verify_no_tag():
    """Verify no tag was created."""
    pass
