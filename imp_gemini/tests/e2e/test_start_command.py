import pytest
import subprocess
from pathlib import Path

def run_gemini(workspace, cmd, *args):
    ws_path = workspace / ".ai-workspace"
    full_cmd = ["python3", "-m", "gemini_cli.cli", "--workspace", str(ws_path), cmd] + list(args)
    # Ensure PYTHONPATH includes the current directory and parent so genesis_core is found
    env = {"PYTHONPATH": f"{Path.cwd()}:{Path.cwd().parent}"}
    return subprocess.run(full_cmd, capture_output=True, text=True, env=env)

def test_start_uninitialised(tmp_path):
    # No .ai-workspace
    res = run_gemini(tmp_path, "start")
    assert "Project not initialized" in res.stdout

def test_start_needs_intent(tmp_path):
    # .ai-workspace exists, but no INTENT.md
    (tmp_path / ".ai-workspace").mkdir()
    (tmp_path / ".ai-workspace" / "gemini_genesis").mkdir()
    (tmp_path / ".ai-workspace" / "gemini_genesis" / "project_constraints.yml").write_text("project:\n  name: test")
    res = run_gemini(tmp_path, "start")
    assert "Action Required: Define project intent" in res.stdout

def test_start_in_progress(tmp_path):
    # Setup a state where a feature is in progress
    ws = tmp_path / ".ai-workspace"
    ws.mkdir()
    (ws / "gemini_genesis").mkdir()
    (ws / "gemini_genesis" / "project_constraints.yml").write_text("project:\n  name: test")
    (tmp_path / "specification").mkdir()
    (tmp_path / "specification" / "INTENT.md").write_text("Intent content")
    (ws / "features").mkdir()
    (ws / "features" / "active").mkdir()
    (ws / "features" / "active" / "REQ-F-1.yml").write_text("feature: REQ-F-1\ntrajectory:\n  requirements:\n    status: pending")
    
    res = run_gemini(tmp_path, "start")
    assert "Next Logical Step" in res.stdout
    assert "REQ-F-1" in res.stdout
    assert "Intent → Requirements" in res.stdout or "intent→requirements" in res.stdout
