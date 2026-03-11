# Validates: REQ-F-ENGINE-001, REQ-F-LIFE-001
"""CLI e2e for pending F_P retry, recovery scan, and escalation."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from imp_codex.runtime.events import append_run_event


REPO_ROOT = Path(__file__).resolve().parents[3]
FEATURE_ID = "REQ-F-FP-001"


def _run_runtime(project_root: Path, *args: str) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        ["python", "-m", "imp_codex.runtime", *args, "--project-root", str(project_root)],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    return json.loads(result.stdout)


def test_cli_fp_supervisor_retry_then_escalation(tmp_path):
    project_root = tmp_path / "fp-supervisor-demo"
    spec_dir = project_root / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "INTENT.md").write_text("# Intent\n\nCLI supervisor demo.\n")

    _run_runtime(project_root, "init")
    _run_runtime(
        project_root,
        "iterate",
        "--feature",
        FEATURE_ID,
        "--edge",
        "intent→requirements",
        "--profile",
        "minimal",
        "--delta",
        "0",
        "--converged",
    )
    append_run_event(
        project_root / ".ai-workspace" / "events" / "events.jsonl",
        project_name=project_root.name,
        semantic_type="intent_raised",
        actor="pytest",
        feature=FEATURE_ID,
        edge="design→code",
        payload={
            "intent_id": "INT-001",
            "trigger": "Seed F_P supervisor flow",
            "delta": "Retry failing code edge",
            "signal_source": "test_failure",
            "vector_type": "feature",
            "severity": "high",
            "requires_spec_change": False,
            "affected_features": [FEATURE_ID],
            "affected_req_keys": [FEATURE_ID],
        },
    )

    dispatched = _run_runtime(project_root, "intent-observer", "--once")
    assert dispatched["dispatched_count"] == 1
    manifest_dir = project_root / ".ai-workspace" / "agents"
    manifests = sorted(manifest_dir.glob("fp_intent_*.json"))
    assert len(manifests) == 1

    manifest = json.loads(manifests[0].read_text())
    manifest["created_at"] = "2026-03-10T00:00:00Z"
    manifest["last_progress_at"] = "2026-03-10T00:00:00Z"
    manifests[0].write_text(json.dumps(manifest, indent=2, sort_keys=True))

    first_start = _run_runtime(project_root, "start")
    assert first_start["recovery"]["retries_scheduled"] == 1
    retry_manifest = Path(first_start["recovery"]["manifests"][0]["retry_manifest_path"])
    assert retry_manifest.exists()

    retry_data = json.loads(retry_manifest.read_text())
    retry_data["created_at"] = "2026-03-10T00:00:00Z"
    retry_data["last_progress_at"] = "2026-03-10T00:00:00Z"
    retry_data["retry_count"] = retry_data["max_retries"]
    retry_manifest.write_text(json.dumps(retry_data, indent=2, sort_keys=True))

    feature_file = project_root / ".ai-workspace" / "features" / "active" / f"{FEATURE_ID}.yml"
    feature_file.write_text(feature_file.read_text() + "\n# drifted\n")

    second_start = _run_runtime(project_root, "start")
    assert second_start["recovery"]["gap_events"] == 1
    assert second_start["recovery"]["escalations"] == 1

    events_file = project_root / ".ai-workspace" / "events" / "events.jsonl"
    semantic_types = [
        json.loads(line)["run"]["facets"]["sdlc:event_type"]["type"]
        for line in events_file.read_text().splitlines()
        if line.strip()
    ]
    assert "edge_started" in semantic_types
    assert "IterationFailed" in semantic_types
    assert "gap_detected" in semantic_types
    assert "IterationAbandoned" in semantic_types
    assert "intent_raised" in semantic_types
