# Validates: REQ-TOOL-011 (Installability)
# Validates: REQ-TOOL-015 (Workspace Placement at Project Root)
# Validates: REQ-LIFE-002 (Installer emits genesis_installed event)
# Validates: REQ-SUPV-003 (Event stream observability — installer footprint)
"""
Tests for gen-setup.py installer.
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
        assert "genesis" in data["extraKnownMarketplaces"]
        assert data["enabledPlugins"]["genesis@genesis"] is True

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

class TestLegacyMigration:
    """Installer removes pre-genesis keys (aisdlc / gen-methodology-v2)."""

    def test_removes_legacy_marketplace_and_plugin(self, clean_target):
        clean_target.mkdir()
        settings_dir = clean_target / ".claude"
        settings_dir.mkdir()
        (settings_dir / "settings.json").write_text(json.dumps({
            "extraKnownMarketplaces": {
                "aisdlc": {"source": {"source": "github", "repo": "foolishimp/ai_sdlc_method"}}
            },
            "enabledPlugins": {"gen-methodology-v2@aisdlc": True},
        }))
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads((settings_dir / "settings.json").read_text())
        assert "aisdlc" not in data["extraKnownMarketplaces"]
        assert "gen-methodology-v2@aisdlc" not in data["enabledPlugins"]
        assert "genesis" in data["extraKnownMarketplaces"]
        assert data["enabledPlugins"]["genesis@genesis"] is True


class TestIdempotency:
    """REQ-TOOL-011: Installation is idempotent."""

    def test_rerun_preserves_events(self, installed_target):
        events = installed_target / ".ai-workspace" / "events" / "events.jsonl"
        original_lines = events.read_text().strip().splitlines()

        # Re-run installer
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(installed_target)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        new_lines = events.read_text().strip().splitlines()
        # Original events must be preserved (append-only log)
        assert new_lines[:len(original_lines)] == original_lines, (
            "Re-run must not modify existing events — append-only log"
        )
        # Re-install appends a genesis_installed event (deployment history)
        new_types = [json.loads(l)["event_type"] for l in new_lines[len(original_lines):]]
        assert "genesis_installed" in new_types

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
        assert "0 failed" in result.stdout
        assert "Installation verified OK" in result.stdout

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
        assert "0 failed" in result.stdout
        assert "Installation verified OK" in result.stdout

    def test_verify_fails_on_empty_dir(self, clean_target):
        clean_target.mkdir()
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "verify", "--target", str(clean_target)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1


class TestWorkspacePlacement:
    """REQ-TOOL-015: workspace must be at project root, not inside imp_* tenant."""

    def test_installer_places_workspace_in_target(self, clean_target):
        """REQ-TOOL-015 AC-1: .ai-workspace created directly in the target dir."""
        clean_target.mkdir()
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert (clean_target / ".ai-workspace").is_dir()

    def test_no_workspace_inside_imp_tenant(self, tmp_path):
        """REQ-TOOL-015 AC-3: the structural check CAN detect the wrong layout.

        This demonstrates the check that would have caught genesis_monitor's
        workspace being placed at imp_fastapi/.ai-workspace/ instead of
        genesis_monitor/.ai-workspace/.
        """
        # Simulate the WRONG layout
        project_root = tmp_path / "my_project"
        (project_root / "specification").mkdir(parents=True)
        (project_root / "imp_fastapi" / ".ai-workspace").mkdir(parents=True)  # wrong

        # The check should detect the violation
        violations = [
            str(d) for d in project_root.glob("imp_*/.ai-workspace")
            if d.is_dir()
        ]
        assert violations != [], (
            "Expected the structural check to find the misplaced workspace inside imp_*/"
        )

    def test_correct_layout_passes(self, tmp_path):
        """REQ-TOOL-015: project-root workspace is the valid layout."""
        project_root = tmp_path / "my_project"
        (project_root / "specification").mkdir(parents=True)
        (project_root / "imp_fastapi").mkdir(parents=True)
        (project_root / ".ai-workspace").mkdir(parents=True)  # correct

        violations = [
            str(d) for d in project_root.glob("imp_*/.ai-workspace")
            if d.is_dir()
        ]
        assert violations == []

    def test_installer_warns_when_run_from_imp_tenant(self, tmp_path):
        """REQ-TOOL-015 AC-2: installer warns when target path contains imp_*."""
        imp_dir = tmp_path / "imp_fastapi"
        imp_dir.mkdir()
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(imp_dir)],
            capture_output=True, text=True,
        )
        # Installer should warn (exit 0 still — not a hard failure)
        combined = result.stdout + result.stderr
        assert "WARNING" in combined or "warning" in combined.lower() or \
               "imp_" in combined, (
            "Expected a warning when installing into an imp_* directory. "
            "Installer output:\n" + combined
        )


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


class TestInstallEvent:
    """REQ-LIFE-002, REQ-SUPV-003: installer emits genesis_installed event to event stream."""

    def _get_events(self, target: Path) -> list:
        events_file = target / ".ai-workspace" / "events" / "events.jsonl"
        return [json.loads(line) for line in events_file.read_text().strip().splitlines()]

    def test_install_emits_genesis_installed_event(self, installed_target):
        """genesis_installed event appears in the event stream after install."""
        events = self._get_events(installed_target)
        types = [e["event_type"] for e in events]
        assert "genesis_installed" in types

    def test_genesis_installed_event_has_required_fields(self, installed_target):
        """genesis_installed carries version, source, timestamp, project."""
        events = self._get_events(installed_target)
        evt = next(e for e in events if e["event_type"] == "genesis_installed")
        assert "timestamp" in evt
        assert "project" in evt
        assert "data" in evt
        data = evt["data"]
        assert "version" in data
        assert "source" in data
        assert "engine_files" in data
        assert "commands" in data

    def test_genesis_installed_event_version_matches(self, installed_target):
        """genesis_installed data.version matches the installer VERSION constant."""
        events = self._get_events(installed_target)
        evt = next(e for e in events if e["event_type"] == "genesis_installed")
        # Version should be a non-empty string like "3.0.11"
        assert evt["data"]["version"]
        assert "." in evt["data"]["version"]

    def test_genesis_installed_event_reports_engine_file_count(self, installed_target):
        """engine_files count is a non-negative integer."""
        events = self._get_events(installed_target)
        evt = next(e for e in events if e["event_type"] == "genesis_installed")
        assert isinstance(evt["data"]["engine_files"], int)
        assert evt["data"]["engine_files"] >= 0

    def test_genesis_installed_event_workspace_created_true(self, installed_target):
        """workspace_created is True for a standard install (no --no-workspace)."""
        events = self._get_events(installed_target)
        evt = next(e for e in events if e["event_type"] == "genesis_installed")
        assert evt["data"].get("workspace_created") is True

    def test_no_workspace_install_does_not_emit_install_event(self, clean_target):
        """Plugin-only install skips genesis_installed (no events.jsonl to write to)."""
        clean_target.mkdir()
        subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(clean_target), "--no-workspace"],
            capture_output=True, text=True,
        )
        events_file = clean_target / ".ai-workspace" / "events" / "events.jsonl"
        assert not events_file.exists()

    def test_verify_emits_genesis_verified_event(self, installed_target):
        """verify subcommand appends genesis_verified event after passing checks."""
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "verify", "--target", str(installed_target)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        events = self._get_events(installed_target)
        types = [e["event_type"] for e in events]
        assert "genesis_verified" in types

    def test_genesis_verified_event_has_checks_passed(self, installed_target):
        """genesis_verified carries checks_passed and checks_failed counts."""
        subprocess.run(
            [sys.executable, str(INSTALLER), "verify", "--target", str(installed_target)],
            capture_output=True, text=True,
        )
        events = self._get_events(installed_target)
        evt = next(e for e in events if e["event_type"] == "genesis_verified")
        assert "checks_passed" in evt["data"]
        assert "checks_failed" in evt["data"]
        assert evt["data"]["checks_passed"] > 0
        assert evt["data"]["checks_failed"] == 0

    def test_install_event_is_valid_json(self, installed_target):
        """All lines in events.jsonl are valid JSON (install does not corrupt the log)."""
        events_file = installed_target / ".ai-workspace" / "events" / "events.jsonl"
        for line in events_file.read_text().strip().splitlines():
            json.loads(line)  # raises if invalid
