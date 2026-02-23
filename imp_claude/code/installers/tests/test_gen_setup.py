"""
Tests for gen-setup.py installer.

# Validates: REQ-TOOL-011 (Installability)
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

INSTALLER = Path(__file__).parent.parent / "gen-setup.py"


@pytest.fixture
def clean_target(tmp_path):
    """Empty directory for fresh install."""
    return tmp_path / "project"


@pytest.fixture
def installed_target(clean_target):
    """Directory with completed install."""
    target = clean_target
    target.mkdir()
    result = subprocess.run(
        [sys.executable, str(INSTALLER), "--target", str(target)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Install failed: {result.stderr}"
    return target


class TestFreshInstall:
    """REQ-TOOL-011: Single-command installation."""

    def test_installer_exits_zero(self, clean_target):
        clean_target.mkdir()
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_creates_settings_json(self, installed_target):
        settings = installed_target / ".claude" / "settings.json"
        assert settings.exists()
        data = json.loads(settings.read_text())
        assert "aisdlc" in data["extraKnownMarketplaces"]
        assert data["enabledPlugins"]["gen-methodology-v2@aisdlc"] is True

    def test_creates_events_jsonl(self, installed_target):
        events = installed_target / ".ai-workspace" / "events" / "events.jsonl"
        assert events.exists()
        assert events.stat().st_size > 0

    def test_emits_project_initialized_event(self, installed_target):
        events = installed_target / ".ai-workspace" / "events" / "events.jsonl"
        first_line = events.read_text().strip().splitlines()[0]
        evt = json.loads(first_line)
        assert evt["event_type"] == "project_initialized"
        assert "timestamp" in evt
        assert "project" in evt

    def test_creates_feature_dirs(self, installed_target):
        assert (installed_target / ".ai-workspace" / "features" / "active").is_dir()
        assert (installed_target / ".ai-workspace" / "features" / "completed").is_dir()

    def test_creates_project_constraints(self, installed_target):
        constraints = installed_target / ".ai-workspace" / "context" / "project_constraints.yml"
        assert constraints.exists()
        content = constraints.read_text()
        assert "ecosystem_compatibility" in content
        assert "deployment_target" in content

    def test_creates_intent_template(self, installed_target):
        intent = installed_target / "specification" / "INTENT.md"
        assert intent.exists()
        assert "Intent" in intent.read_text()

    def test_creates_tasks_dir(self, installed_target):
        tasks = installed_target / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md"
        assert tasks.exists()


class TestIdempotency:
    """REQ-TOOL-011: Installation is idempotent."""

    def test_rerun_preserves_events(self, installed_target):
        events = installed_target / ".ai-workspace" / "events" / "events.jsonl"
        original = events.read_text()

        # Re-run installer
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(installed_target)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert events.read_text() == original, "events.jsonl should not change on re-run"

    def test_rerun_preserves_existing_files(self, installed_target):
        # Write user content to INTENT.md
        intent = installed_target / "specification" / "INTENT.md"
        intent.write_text("My custom intent")

        # Re-run installer
        subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(installed_target)],
            capture_output=True,
            text=True,
        )
        assert intent.read_text() == "My custom intent"


class TestDryRun:
    """REQ-TOOL-011: Preview changes without writing."""

    def test_dry_run_creates_nothing(self, clean_target):
        clean_target.mkdir()
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target), "--dry-run"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert not (clean_target / ".claude").exists()
        assert not (clean_target / ".ai-workspace").exists()


class TestNoWorkspace:
    """REQ-TOOL-011: Plugin-only mode."""

    def test_no_workspace_skips_ai_workspace(self, clean_target):
        clean_target.mkdir()
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target), "--no-workspace"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (clean_target / ".claude" / "settings.json").exists()
        assert not (clean_target / ".ai-workspace").exists()


class TestVerify:
    """REQ-TOOL-011: Verify existing installation."""

    def test_verify_passes_on_valid_install(self, installed_target):
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "verify", "--target", str(installed_target)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "10 passed, 0 failed" in result.stdout

    def test_verify_passes_on_no_workspace_install(self, clean_target):
        clean_target.mkdir()
        # Install plugin-only
        subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target), "--no-workspace"],
            capture_output=True,
            text=True,
        )
        # Verify should pass with plugin-only checks (3 checks: settings file, marketplace, plugin)
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "verify", "--target", str(clean_target)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Verify failed on --no-workspace install: {result.stdout}"
        assert "plugin-only" in result.stdout.lower()
        assert "3 passed, 0 failed" in result.stdout

    def test_verify_fails_on_empty_dir(self, clean_target):
        clean_target.mkdir()
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "verify", "--target", str(clean_target)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1


class TestProjectDetection:
    """Auto-detect project name from directory/config files."""

    def test_detects_from_directory_name(self, clean_target):
        clean_target.mkdir()
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        events = clean_target / ".ai-workspace" / "events" / "events.jsonl"
        evt = json.loads(events.read_text().strip().splitlines()[0])
        assert evt["project"] == clean_target.name

    def test_detects_from_package_json(self, clean_target):
        clean_target.mkdir()
        (clean_target / "package.json").write_text(json.dumps({"name": "my-app"}))
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        events = clean_target / ".ai-workspace" / "events" / "events.jsonl"
        evt = json.loads(events.read_text().strip().splitlines()[0])
        assert evt["project"] == "my-app"
