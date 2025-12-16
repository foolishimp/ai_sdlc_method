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
PLUGINS_DIR = PROJECT_ROOT / "claude-code" / ".claude-plugin" / "plugins"
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


def create_snapshot_template(template_dir: Path) -> Path:
    """Create a snapshot template file with all variables."""
    template_file = template_dir / "CONTEXT_SNAPSHOT_TEMPLATE.md"
    template_content = """# Context Snapshot - {TIMESTAMP}

**Created**: {YYYY-MM-DD} {HH:MM:SS}
**Snapshot ID**: snapshot-{YYYY-MM-DD}-{HH-MM-SS}
**Project**: {PROJECT_NAME}
**Branch**: {GIT_BRANCH}

---

## 🎯 Active Tasks Summary

**Total Active**: {TOTAL_ACTIVE_COUNT}
- In Progress: {IN_PROGRESS_COUNT}
- Pending: {PENDING_COUNT}
- Blocked: {BLOCKED_COUNT}

### Tasks In Progress

{IN_PROGRESS_TASKS_TABLE}

### Tasks Pending

{PENDING_TASKS_TABLE}

### Tasks Blocked

{BLOCKED_TASKS_TABLE}

---

## 📁 File Changes

**Modified Files** (uncommitted):
{MODIFIED_FILES_LIST}

**Staged Files**:
{STAGED_FILES_LIST}

**Untracked Files**:
{UNTRACKED_FILES_LIST}

**Git Status**:
```
{GIT_STATUS_OUTPUT}
```

---

## 🔄 Recovery Guidance

### How to Restore This Context

1. **Review This Snapshot**:
   - Read all sections above

2. **Restore Active Tasks**:
   ```bash
   cat .ai-workspace/tasks/active/ACTIVE_TASKS.md
   ```

3. **Check Git State**:
   ```bash
   git status
   git log --oneline -n 10
   ```

---

## 📊 Metadata

**Snapshot Version**: 1.0
**Related Snapshots**:
- Previous: {PREVIOUS_SNAPSHOT_ID}
- Next: {NEXT_SNAPSHOT_ID}

**Statistics**:
- Files modified: {FILES_MODIFIED_COUNT}

---

## 🔗 Related Files

**Recent Finished Tasks**:
{RECENT_FINISHED_TASKS_LIST}

---

**END OF SNAPSHOT**
"""
    template_file.write_text(template_content)
    return template_file


def parse_snapshot_file(snapshot_path: Path) -> dict:
    """Parse a snapshot file and extract key information."""
    content = snapshot_path.read_text()

    # Extract basic metadata
    snapshot_data = {
        "content": content,
        "path": snapshot_path,
        "filename": snapshot_path.name
    }

    # Extract snapshot ID
    import re
    id_match = re.search(r'\*\*Snapshot ID\*\*: (.+)', content)
    if id_match:
        snapshot_data["id"] = id_match.group(1).strip()

    # Extract task counts
    total_match = re.search(r'\*\*Total Active\*\*: (\d+)', content)
    if total_match:
        snapshot_data["total_tasks"] = int(total_match.group(1))

    in_progress_match = re.search(r'In Progress: (\d+)', content)
    if in_progress_match:
        snapshot_data["in_progress"] = int(in_progress_match.group(1))

    pending_match = re.search(r'Pending: (\d+)', content)
    if pending_match:
        snapshot_data["pending"] = int(pending_match.group(1))

    blocked_match = re.search(r'Blocked: (\d+)', content)
    if blocked_match:
        snapshot_data["blocked"] = int(blocked_match.group(1))

    # Extract git branch
    branch_match = re.search(r'\*\*Branch\*\*: (.+)', content)
    if branch_match:
        snapshot_data["branch"] = branch_match.group(1).strip()

    # Extract project name
    project_match = re.search(r'\*\*Project\*\*: (.+)', content)
    if project_match:
        snapshot_data["project"] = project_match.group(1).strip()

    return snapshot_data


def count_snapshot_files(snapshots_dir: Path) -> int:
    """Count the number of snapshot files in a directory."""
    if not snapshots_dir.exists():
        return 0
    return len(list(snapshots_dir.glob("snapshot-*.md")))
