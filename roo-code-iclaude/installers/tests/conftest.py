"""
Shared fixtures for Roo Code installer tests.
Validates: REQ-F-TESTING-001, REQ-F-WORKSPACE-001, REQ-F-PLUGIN-001

Mirrors claude-code/installers/tests/conftest.py but adapted for Roo Code's
.roo/ directory structure (modes, rules, memory-bank) instead of .claude/
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path


# Get the project root directory
# roo-code-iclaude/installers/tests/conftest.py -> go up 3 levels to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
# Installers are in the parent directory (roo-code-iclaude/installers/)
INSTALLERS_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "roo-code-iclaude" / "project-template"
ROO_CODE_ROOT = PROJECT_ROOT / "roo-code-iclaude"


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def installers_dir():
    """Return the installers directory."""
    return INSTALLERS_DIR


@pytest.fixture
def templates_dir():
    """Return the templates directory."""
    return TEMPLATES_DIR


@pytest.fixture
def roo_code_root():
    """Return the roo-code-iclaude directory."""
    return ROO_CODE_ROOT


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp = tempfile.mkdtemp(prefix="aisdlc_roo_test_")
    # Resolve to handle macOS /var -> /private/var symlink
    yield Path(temp).resolve()
    # Cleanup
    if os.path.exists(temp):
        shutil.rmtree(temp)


@pytest.fixture
def temp_target(temp_dir):
    """Create a temporary target directory for installation tests."""
    target = temp_dir / "target_project"
    target.mkdir(parents=True, exist_ok=True)
    return target


@pytest.fixture
def temp_source(temp_dir):
    """Create a temporary source directory simulating project-template for Roo Code.

    Note: ResetInstaller._install_fresh() expects the source directory to have:
    - roo/modes/           (installed to .roo/modes/)
    - roo/rules/           (installed to .roo/rules/)
    - .ai-workspace/templates/
    - .ai-workspace/config/
    - ROOCODE.md

    So we create the source as if it were the project-template directory itself.
    """
    source = temp_dir / "source"
    source.mkdir(parents=True, exist_ok=True)

    # roo/modes - Custom modes (JSON files) - note: without leading dot
    # This matches setup_reset.py: modes_src = self.source / "roo" / "modes"
    modes_dir = source / "roo" / "modes"
    modes_dir.mkdir(parents=True, exist_ok=True)
    (modes_dir / "aisdlc-code.json").write_text('{"slug": "aisdlc-code", "name": "Code Agent"}')
    (modes_dir / "aisdlc-design.json").write_text('{"slug": "aisdlc-design", "name": "Design Agent"}')

    # roo/rules - Methodology rules (Markdown files)
    rules_dir = source / "roo" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / "tdd-workflow.md").write_text("# TDD Workflow\nRED → GREEN → REFACTOR")
    (rules_dir / "key-principles.md").write_text("# Key Principles\nExcellence or nothing")

    # roo/memory-bank - Project context templates
    memory_bank_dir = source / "roo" / "memory-bank"
    memory_bank_dir.mkdir(parents=True, exist_ok=True)
    (memory_bank_dir / "projectbrief.md").write_text("# Project Brief\n")
    (memory_bank_dir / "techstack.md").write_text("# Tech Stack\n")

    # .ai-workspace structure (shared with Claude/Codex/Gemini)
    workspace_dir = source / ".ai-workspace"
    (workspace_dir / "tasks" / "active").mkdir(parents=True, exist_ok=True)
    (workspace_dir / "tasks" / "finished").mkdir(parents=True, exist_ok=True)
    (workspace_dir / "tasks" / "archive").mkdir(parents=True, exist_ok=True)
    (workspace_dir / "session").mkdir(parents=True, exist_ok=True)
    (workspace_dir / "templates").mkdir(parents=True, exist_ok=True)
    (workspace_dir / "config").mkdir(parents=True, exist_ok=True)

    # Create template files
    (workspace_dir / "tasks" / "active" / "ACTIVE_TASKS.md").write_text("# Active Tasks\n")
    (workspace_dir / "templates" / "TASK_TEMPLATE.md").write_text("# Task Template\n")
    (workspace_dir / "config" / "workspace_config.yml").write_text("version: 1.0\n")

    # ROOCODE.md guidance file
    (source / "ROOCODE.md").write_text("# ROOCODE.md\nProject guidance for Roo Code\n")

    return source


@pytest.fixture
def existing_installation(temp_target):
    """Create a target directory with an existing Roo Code installation."""
    # Create .roo structure
    modes_dir = temp_target / ".roo" / "modes"
    modes_dir.mkdir(parents=True, exist_ok=True)
    (modes_dir / "old-mode.json").write_text('{"slug": "old-mode"}')
    (modes_dir / "another-old.json").write_text('{"slug": "another-old"}')

    rules_dir = temp_target / ".roo" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / "old-rule.md").write_text("# Old Rule\n")

    memory_bank_dir = temp_target / ".roo" / "memory-bank"
    memory_bank_dir.mkdir(parents=True, exist_ok=True)
    (memory_bank_dir / "projectbrief.md").write_text("# My Project Brief\nImportant context\n")
    (memory_bank_dir / "techstack.md").write_text("# My Tech Stack\nPython, FastAPI\n")

    # Create .ai-workspace structure with user data
    workspace_dir = temp_target / ".ai-workspace"

    # Tasks - these should be preserved
    active_dir = workspace_dir / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / "ACTIVE_TASKS.md").write_text("# My Active Tasks\n- Task 1\n- Task 2\n")

    finished_dir = workspace_dir / "tasks" / "finished"
    finished_dir.mkdir(parents=True, exist_ok=True)
    (finished_dir / "finished_task_001.md").write_text("# Finished Task 1\nCompleted work\n")
    (finished_dir / "finished_task_002.md").write_text("# Finished Task 2\nMore completed work\n")

    # Templates and config - these should be replaced
    templates_dir = workspace_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    (templates_dir / "OLD_TEMPLATE.md").write_text("# Old Template\n")

    config_dir = workspace_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "old_config.yml").write_text("old: config\n")

    # Session directory
    session_dir = workspace_dir / "session"
    session_dir.mkdir(parents=True, exist_ok=True)

    # ROOCODE.md
    (temp_target / "ROOCODE.md").write_text("# ROOCODE.md\nOld guidance\n")

    return temp_target


@pytest.fixture
def sample_mode(temp_dir):
    """Create a sample mode JSON file for testing."""
    mode_file = temp_dir / "sample-mode.json"
    mode_file.write_text('''{
  "slug": "sample-mode",
  "name": "Sample Mode",
  "roleDefinition": "A sample mode for testing",
  "customInstructions": "Test instructions"
}''')
    return mode_file


@pytest.fixture
def sample_rule(temp_dir):
    """Create a sample rule markdown file for testing."""
    rule_file = temp_dir / "sample-rule.md"
    rule_file.write_text("""# Sample Rule

## Purpose
A sample rule for testing.

## Guidelines
1. Follow TDD
2. Write clean code
""")
    return rule_file


@pytest.fixture
def mock_gitignore(temp_target):
    """Create a .gitignore file in target."""
    gitignore = temp_target / ".gitignore"
    gitignore.write_text("# Existing gitignore\nnode_modules/\n*.pyc\n")
    return gitignore


@pytest.fixture
def add_installers_to_path():
    """Add installers directory to Python path."""
    import sys
    installers_path = str(INSTALLERS_DIR)
    if installers_path not in sys.path:
        sys.path.insert(0, installers_path)
    yield
    if installers_path in sys.path:
        sys.path.remove(installers_path)


# Helper functions available to tests
def count_files(directory: Path, pattern: str = "*") -> int:
    """Count files matching pattern in directory."""
    return len(list(directory.rglob(pattern)))


def read_file_content(file_path: Path) -> str:
    """Read and return file content."""
    return file_path.read_text() if file_path.exists() else ""


def directory_structure(directory: Path) -> list:
    """Return list of all files/directories relative to directory."""
    if not directory.exists():
        return []
    return sorted([str(p.relative_to(directory)) for p in directory.rglob("*")])
