"""
Tests for gemini-setup.py installer.

# Validates: REQ-TOOL-011 (Installability)
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

INSTALLER = Path(__file__).parent.parent / "gemini-setup.py"

@pytest.fixture
def clean_target(tmp_path):
    """Empty directory for fresh install."""
    return tmp_path / "project"

class TestFreshInstall:
    """REQ-TOOL-011: Single-command installation."""

    def test_installer_exits_zero(self, clean_target):
        clean_target.mkdir()
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target), "--skip-skill"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_creates_workspace_structure(self, clean_target):
        clean_target.mkdir()
        subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target), "--skip-skill"],
            capture_output=True,
            text=True,
        )
        
        assert (clean_target / ".ai-workspace" / "events" / "events.jsonl").exists()
        assert (clean_target / ".ai-workspace" / "features" / "active").is_dir()
        assert (clean_target / ".ai-workspace" / "context" / "project_constraints.yml").exists()
        assert (clean_target / "specification" / "INTENT.md").exists()

    def test_emits_project_initialized_event(self, clean_target):
        clean_target.mkdir()
        subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target), "--skip-skill"],
            capture_output=True,
            text=True,
        )
        
        events = clean_target / ".ai-workspace" / "events" / "events.jsonl"
        lines = events.read_text().strip().splitlines()
        assert len(lines) > 0
        evt = json.loads(lines[0])
        assert evt["event_type"] == "project_initialized"

class TestDryRun:
    def test_dry_run_creates_nothing(self, clean_target):
        clean_target.mkdir()
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target), "--dry-run"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert not (clean_target / ".ai-workspace").exists()
