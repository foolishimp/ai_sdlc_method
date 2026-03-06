# Validates: REQ-EVOL-004 (spec_modified event on specification/ changes)
"""Tests for post-commit-spec-watch.sh — git hook that emits spec_modified events."""

import json
import os
import subprocess
from pathlib import Path

import pytest


HOOK_SCRIPT = (
    Path(__file__).parent.parent
    / "code"
    / ".claude-plugin"
    / "plugins"
    / "genesis"
    / "hooks"
    / "post-commit-spec-watch.sh"
)


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo with .ai-workspace and a specification/ directory."""
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        check=True, capture_output=True, cwd=str(repo),
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        check=True, capture_output=True, cwd=str(repo),
    )

    # Set up workspace and events dir
    (repo / ".ai-workspace" / "events").mkdir(parents=True)

    # Set up specification dir
    (repo / "specification" / "features").mkdir(parents=True)

    # Initial commit (empty README so HEAD^1 is valid)
    readme = repo / "README.md"
    readme.write_text("# Test\n")
    subprocess.run(["git", "add", "README.md"], check=True, capture_output=True, cwd=str(repo))
    subprocess.run(
        ["git", "commit", "-m", "init"],
        check=True, capture_output=True, cwd=str(repo),
    )

    return repo


def _commit_spec_file(repo: Path, filename: str, content: str, msg: str = "update spec") -> None:
    """Write a spec file, stage, and commit it."""
    path = repo / "specification" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    subprocess.run(["git", "add", str(path)], check=True, capture_output=True, cwd=str(repo))
    subprocess.run(
        ["git", "commit", "-m", msg],
        check=True, capture_output=True, cwd=str(repo),
    )


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    """Run the hook script in the context of the git repo."""
    env = dict(os.environ)
    env["GIT_DIR"] = str(repo / ".git")
    return subprocess.run(
        ["bash", str(HOOK_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(repo),
        env=env,
    )


def _read_events(repo: Path) -> list[dict]:
    events_file = repo / ".ai-workspace" / "events" / "events.jsonl"
    if not events_file.exists():
        return []
    events = []
    for line in events_file.read_text().splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


class TestHookScriptExists:
    def test_hook_script_file_exists(self) -> None:
        assert HOOK_SCRIPT.exists(), f"Hook script not found: {HOOK_SCRIPT}"

    def test_hook_script_is_executable(self) -> None:
        assert os.access(HOOK_SCRIPT, os.X_OK), "Hook script is not executable"


class TestSpecModifiedHook:
    def test_emits_spec_modified_event_on_spec_change(self, git_repo: Path) -> None:
        _commit_spec_file(git_repo, "features/FEATURE_VECTORS.md", "# REQ-F-TEST-001\n")
        result = _run_hook(git_repo)
        assert result.returncode == 0

        events = _read_events(git_repo)
        spec_events = [e for e in events if e.get("event_type") == "spec_modified"]
        assert len(spec_events) == 1

        ev = spec_events[0]
        assert ev["file"] == "specification/features/FEATURE_VECTORS.md"
        assert "sha256:" in ev["previous_hash"]
        assert "sha256:" in ev["new_hash"]
        assert ev["trigger_type"] == "manual"
        assert ev["trigger_event_id"] == "manual"

    def test_does_not_emit_event_for_non_spec_changes(self, git_repo: Path) -> None:
        # Commit a non-spec file
        f = git_repo / "src" / "main.py"
        f.parent.mkdir(exist_ok=True)
        f.write_text("# code\n")
        subprocess.run(["git", "add", str(f)], check=True, capture_output=True, cwd=str(git_repo))
        subprocess.run(
            ["git", "commit", "-m", "add code"],
            check=True, capture_output=True, cwd=str(git_repo),
        )

        result = _run_hook(git_repo)
        assert result.returncode == 0

        events = _read_events(git_repo)
        spec_events = [e for e in events if e.get("event_type") == "spec_modified"]
        assert len(spec_events) == 0

    def test_emits_event_for_each_changed_spec_file(self, git_repo: Path) -> None:
        # Commit two spec files at once
        for name in ("features/FEATURE_VECTORS.md", "requirements/REQUIREMENTS.md"):
            path = git_repo / "specification" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {name}\n")
            subprocess.run(["git", "add", str(path)], check=True, capture_output=True, cwd=str(git_repo))
        subprocess.run(
            ["git", "commit", "-m", "add two spec files"],
            check=True, capture_output=True, cwd=str(git_repo),
        )

        result = _run_hook(git_repo)
        assert result.returncode == 0

        events = _read_events(git_repo)
        spec_events = [e for e in events if e.get("event_type") == "spec_modified"]
        assert len(spec_events) == 2
        files = {e["file"] for e in spec_events}
        assert "specification/features/FEATURE_VECTORS.md" in files
        assert "specification/requirements/REQUIREMENTS.md" in files

    def test_exits_silently_when_no_workspace(self, tmp_path: Path) -> None:
        """Hook must not fail when .ai-workspace is absent."""
        repo = tmp_path / "bare_repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "t@t.com"],
            check=True, capture_output=True, cwd=str(repo),
        )
        subprocess.run(
            ["git", "config", "user.name", "T"],
            check=True, capture_output=True, cwd=str(repo),
        )

        env = dict(os.environ)
        env["GIT_DIR"] = str(repo / ".git")
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True, text=True, cwd=str(repo), env=env,
        )
        assert result.returncode == 0
        # No crash, no output expected

    def test_event_schema_fields_present(self, git_repo: Path) -> None:
        _commit_spec_file(git_repo, "core/AI_SDLC_ASSET_GRAPH_MODEL.md", "# Model v3\n")
        _run_hook(git_repo)

        events = _read_events(git_repo)
        ev = next(e for e in events if e.get("event_type") == "spec_modified")

        required_fields = {
            "event_type", "timestamp", "project",
            "file", "what_changed",
            "previous_hash", "new_hash",
            "trigger_event_id", "trigger_type",
        }
        for field in required_fields:
            assert field in ev, f"Missing field: {field}"

    def test_new_hash_differs_from_prev_hash_on_edit(self, git_repo: Path) -> None:
        # First commit to establish content
        _commit_spec_file(git_repo, "INTENT.md", "# Original intent\n")
        _run_hook(git_repo)

        # Clear events
        (git_repo / ".ai-workspace" / "events" / "events.jsonl").write_text("")

        # Second commit modifying the same file
        _commit_spec_file(git_repo, "INTENT.md", "# Updated intent — v2\n", msg="update intent")
        _run_hook(git_repo)

        events = _read_events(git_repo)
        ev = next((e for e in events if e.get("event_type") == "spec_modified"), None)
        assert ev is not None
        assert ev["previous_hash"] != ev["new_hash"]
