#!/usr/bin/env python3
"""
BDD Test Configuration and Fixtures

# Implements: REQ-NFR-QUALITY-001 (Code Quality Standards)
"""

import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

import pytest


# =============================================================================
# Path Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
PLUGINS_DIR = PROJECT_ROOT / "claude-code" / "plugins"
METHODOLOGY_PLUGIN = PLUGINS_DIR / "aisdlc-methodology"


# =============================================================================
# Test Context Fixture
# =============================================================================

@pytest.fixture
def test_context():
    """Shared context dictionary for passing data between steps."""
    return {}


# =============================================================================
# Project Fixtures
# =============================================================================

@pytest.fixture
def temp_project():
    """Create a temporary project directory with basic git structure."""
    temp_dir = tempfile.mkdtemp(prefix="aisdlc_bdd_test_")
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
def workspace(temp_project):
    """Create a complete .ai-workspace structure."""
    workspace_dir = temp_project / ".ai-workspace"

    # Create directory structure
    (workspace_dir / "tasks" / "active").mkdir(parents=True)
    (workspace_dir / "tasks" / "finished").mkdir(parents=True)
    (workspace_dir / "templates").mkdir(parents=True)

    # Create ACTIVE_TASKS.md
    active_tasks = workspace_dir / "tasks" / "active" / "ACTIVE_TASKS.md"
    active_tasks.write_text(f"""# Active Tasks

*Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}*

---

## Summary

**Total Active Tasks**: 0

---
""")

    # Create method reference
    method_ref = workspace_dir / "templates" / "AISDLC_METHOD_REFERENCE.md"
    method_ref.write_text("""# AI SDLC Method Reference

## The 7 Stages
1. Requirements
2. Design
3. Tasks
4. Code
5. System Test
6. UAT
7. Runtime Feedback
""")

    return temp_project


@pytest.fixture
def workspace_with_tasks(workspace):
    """Create workspace with sample tasks."""
    active_tasks = workspace / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
    active_tasks.write_text(f"""# Active Tasks

*Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}*

---

## Task #1: Implement User Authentication

**Priority**: High
**Status**: In Progress
**Requirements**: REQ-F-AUTH-001, REQ-NFR-SEC-001

**Description**:
Implement user login with email and password.

---

## Task #2: Add Database Schema

**Priority**: Medium
**Status**: Not Started
**Requirements**: REQ-F-DATA-001

**Description**:
Create database tables for user data.

---

## Summary

**Total Active Tasks**: 2

---
""")

    # Add a finished task
    finished_dir = workspace / ".ai-workspace" / "tasks" / "finished"
    finished_task = finished_dir / "20251127_1000_sample_task.md"
    finished_task.write_text("""# Task: Sample Completed Task

**Status**: Completed
**Task ID**: #0
**Requirements**: REQ-F-SAMPLE-001
""")

    return workspace


@pytest.fixture
def plugin_installed():
    """Verify the AISDLC methodology plugin is available."""
    return METHODOLOGY_PLUGIN


# =============================================================================
# Helper Functions
# =============================================================================

def parse_active_tasks(file_path: Path) -> list:
    """Parse ACTIVE_TASKS.md and return list of tasks."""
    content = file_path.read_text()
    tasks = []

    for line in content.split("\n"):
        if line.startswith("## Task #"):
            task_header = line.replace("## Task #", "").strip()
            parts = task_header.split(":", 1)
            task_id = parts[0].strip()
            title = parts[1].strip() if len(parts) > 1 else ""
            tasks.append({"id": task_id, "title": title})

    return tasks


def count_tasks(file_path: Path) -> int:
    """Count tasks in ACTIVE_TASKS.md."""
    return len(parse_active_tasks(file_path))


def verify_tag_exists(repo_path: Path, tag_name: str) -> bool:
    """Verify a git tag exists."""
    result = subprocess.run(
        ["git", "tag", "-l", tag_name],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    return tag_name in result.stdout
