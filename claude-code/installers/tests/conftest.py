"""
Shared fixtures for Claude Code installer tests.

Validates: REQ-F-PLUGIN-001, REQ-F-PLUGIN-002
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
def temp_target_with_aisdlc_settings(temp_target):
    """Create a temp directory with existing AISDLC settings."""
    claude_dir = temp_target / ".claude"
    claude_dir.mkdir(parents=True)

    settings_file = claude_dir / "settings.json"
    settings_file.write_text('''{
  "extraKnownMarketplaces": {
    "aisdlc-old": {
      "source": {
        "source": "directory",
        "path": "/old/path"
      }
    }
  },
  "enabledPlugins": {
    "aisdlc-core@aisdlc-old": true
  }
}''')

    return temp_target


@pytest.fixture
def temp_target_with_invalid_json(temp_target):
    """Create a temp directory with invalid settings.json."""
    claude_dir = temp_target / ".claude"
    claude_dir.mkdir(parents=True)

    settings_file = claude_dir / "settings.json"
    settings_file.write_text('{ invalid json }')

    return temp_target
