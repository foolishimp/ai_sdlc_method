# Validates: REQ-TOOL-011, REQ-TOOL-015
"""E2E installation sandbox tests \u2014 verifies gemini-setup.py in an isolated directory."""

import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

# \u2500\u2500 Repo layout \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / "gemini_cli" / "installers" / "gemini-setup.py"
GEMINI_SRC = REPO_ROOT

# \u2500\u2500 Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _gemini_env(project_dir: Path) -> dict[str, str]:
    """PYTHONPATH pointing at the target GEMINI_SRC."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(GEMINI_SRC)
    return env

def _run_gemini(project_dir: Path, *args: str) -> subprocess.CompletedProcess:
    """Run `python -m gemini_cli.cli <args>` inside project_dir."""
    return subprocess.run(
        [sys.executable, "-m", "gemini_cli.cli", "--workspace", str(project_dir / ".ai-workspace"), *args],
        env=_gemini_env(project_dir),
        capture_output=True,
        text=True,
        cwd=str(project_dir),
        timeout=60,
    )

def _read_events(project_dir: Path) -> list[dict]:
    events_path = project_dir / ".ai-workspace" / "events" / "events.jsonl"
    if not events_path.exists():
        return []
    return [
        json.loads(line)
        for line in events_path.read_text().splitlines()
        if line.strip()
    ]

# \u2500\u2500 Fixtures \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@pytest.fixture(scope="module")
def sandbox_project(tmp_path_factory):
    """Install Gemini via gemini-setup.py into a fresh directory."""
    project_dir = tmp_path_factory.mktemp("install_sandbox")

    # Minimal project scaffold
    (project_dir / "pyproject.toml").write_text(
        textwrap.dedent("""\
            [project]
            name = "sandbox-test"
            version = "0.1.0"
        """)
    )
    (project_dir / "specification").mkdir()
    (project_dir / "specification" / "INTENT.md").write_text(
        "# Intent\nBuild a sandbox test.\n"
    )

    result = subprocess.run(
        [
            sys.executable, str(INSTALLER),
            "--target", str(project_dir),
        ],
        capture_output=True,
        text=True,
        cwd=str(project_dir),
        timeout=60,
    )

    assert result.returncode == 0, f"Install failed: {result.stderr}"
    return project_dir

# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# INSTALLATION CHECKS
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

class TestSandboxInstallation:
    """Verifies the installer correctly scaffolds the isolated workspace."""

    def test_workspace_structure(self, sandbox_project):
        """All critical directories must exist."""
        ws = sandbox_project / ".ai-workspace"
        assert ws.is_dir()
        for sub in ("events", "features/active", "graph", "context"):
            assert (ws / sub).exists(), f"Missing: {sub}"

    def test_project_initialized_event(self, sandbox_project):
        """events.jsonl must contain project_initialized."""
        events = _read_events(sandbox_project)
        assert any(e.get("event_type") == "project_initialized" for e in events)

    def test_gemini_cli_invocable(self, sandbox_project):
        """gemini-cli commands should run in the sandbox."""
        result = _run_gemini(sandbox_project, "status")
        assert result.returncode == 0
        assert "AI SDLC" in result.stdout

    def test_project_constraints_created(self, sandbox_project):
        """Default constraints should be installed."""
        constraints = sandbox_project / ".ai-workspace" / "context" / "project_constraints.yml"
        # The installer might put it in gemini/ instead of context/ in some versions
        if not constraints.exists():
            constraints = sandbox_project / ".ai-workspace" / "gemini" / "project_constraints.yml"
            
        assert constraints.exists()
        data = yaml.safe_load(constraints.read_text())
        assert "project" in data

    def test_graph_topology_installed(self, sandbox_project):
        """Topology must be present."""
        topo = sandbox_project / ".ai-workspace" / "graph" / "graph_topology.yml"
        if not topo.exists():
            topo = sandbox_project / ".ai-workspace" / "gemini" / "graph_topology.yml"
        assert topo.exists()
        data = yaml.safe_load(topo.read_text())
        assert "transitions" in data

# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# FUNCTIONAL CHECKS
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

class TestSandboxFunctional:
    """Verifies key Gemini features work in the installed sandbox."""

    def test_spawn_and_status(self, sandbox_project):
        """/gen-spawn creates a vector and status reflects it."""
        result = _run_gemini(sandbox_project, "spawn", "--id", "REQ-F-SANDBOX-001", "--intent", "Test sandbox")
        assert result.returncode == 0
        
        result = _run_gemini(sandbox_project, "status")
        assert "REQ-F-SANDBOX-001" in result.stdout

    def test_start_command_auto_selection(self, sandbox_project):
        """/gen-start identifies the next step."""
        result = _run_gemini(sandbox_project, "start")
        assert result.returncode == 0
        assert "Detected State" in result.stdout
        assert "Next Logical Step" in result.stdout or "Action" in result.stdout
