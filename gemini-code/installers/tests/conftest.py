"""
Shared fixtures for installer tests.
Validates: REQ-F-TESTING-001, REQ-F-WORKSPACE-001, REQ-F-CMD-001
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path


# Get the project root directory
# gemini-code/installers/tests/conftest.py -> go up 3 levels to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
# Installers are in the parent directory (gemini-code/installers/)
INSTALLERS_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "gemini-code" / "project-template"
PLUGINS_DIR = PROJECT_ROOT / "gemini-code" / "plugins"


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
def plugins_dir():
    """Return the plugins directory."""
    return PLUGINS_DIR


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp = tempfile.mkdtemp(prefix="aisdlc_test_")
    yield Path(temp)
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
    """Create a temporary source directory simulating ai_sdlc_method."""
    source = temp_dir / "source"
    source.mkdir(parents=True, exist_ok=True)

    # Create minimal template structure
    template_root = source / "gemini-code" / "project-template"

    # .gemini/commands
    commands_dir = template_root / ".gemini" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    (commands_dir / "test-command.md").write_text("# Test Command\nTest content")

    # .gemini/agents
    agents_dir = template_root / ".gemini" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "test-agent.md").write_text("# Test Agent\nTest content")

    # .ai-workspace structure
    workspace_dir = template_root / ".ai-workspace"
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

    return source


@pytest.fixture
def existing_installation(temp_target):
    """Create a target directory with an existing installation."""
    # Create .gemini structure
    commands_dir = temp_target / ".gemini" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    (commands_dir / "old-command.md").write_text("# Old Command\n")
    (commands_dir / "another-old.md").write_text("# Another Old\n")

    agents_dir = temp_target / ".gemini" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "old-agent.md").write_text("# Old Agent\n")

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

    return temp_target


@pytest.fixture
def sample_plugin(temp_dir):
    """Create a sample plugin for testing."""
    plugin_dir = temp_dir / "sample-plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Create plugin metadata
    meta_dir = plugin_dir / ".claude-plugin"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "plugin.json").write_text('''{
  "name": "sample-plugin",
  "version": "1.0.0",
  "description": "A sample plugin for testing",
  "author": "Test"
}''')

    # Create plugin content
    (plugin_dir / "README.md").write_text("# Sample Plugin\n")
    (plugin_dir / "config.yml").write_text("plugin:\n  name: sample\n")

    return plugin_dir


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
