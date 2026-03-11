# Validates: REQ-F-ENGINE-001, REQ-F-LIFE-001
"""CLI e2e for worker-backed intent dispatch."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import yaml

from imp_codex.runtime.events import append_run_event
from imp_codex.runtime.paths import RuntimePaths


REPO_ROOT = Path(__file__).resolve().parents[3]
FEATURE_ID = "REQ-F-AUTH-001"


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


def _configure_project(paths: RuntimePaths) -> None:
    constraints = yaml.safe_load(paths.project_constraints_path.read_text())
    for tool_name in ("syntax_checker", "linter", "type_checker", "test_runner", "coverage", "formatter"):
        constraints["tools"][tool_name]["command"] = "python"
        constraints["tools"][tool_name]["args"] = "-c \"print('ok')\""
    constraints["agent_invocation"] = {
        "mode": "file",
        "fallback": "fail",
        "file": ".ai-workspace/codex/context/agent_evaluations.json",
    }
    paths.project_constraints_path.write_text(yaml.safe_dump(constraints, sort_keys=False))


def _write_design(project_root: Path) -> None:
    design_dir = project_root / "imp_codex" / "design"
    design_dir.mkdir(parents=True, exist_ok=True)
    (design_dir / "auth_design.md").write_text(
        "\n".join(
            [
                "# Auth Design",
                "",
                "Implements: REQ-F-AUTH-001",
                "Interfaces",
                "Dependencies",
            ]
        )
        + "\n"
    )


def test_cli_intent_observer_run_agent_executes_fp_worker_and_converges(tmp_path):
    project_root = tmp_path / "fp-worker-demo"
    spec_dir = project_root / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "INTENT.md").write_text("# Intent\n\nBuild auth.\n")
    (spec_dir / "requirements.md").write_text("# Requirements\n\n- REQ-F-AUTH-001\n")

    _run_runtime(project_root, "init")
    paths = RuntimePaths(project_root)
    _configure_project(paths)
    _write_design(project_root)
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

    invocation_file = paths.codex_context_dir / "agent_evaluations.json"
    invocation_file.write_text(
        json.dumps(
            {
                "evaluations": [
                    {
                        "feature": FEATURE_ID,
                        "edge": "design→code",
                        "name": "code_matches_design",
                        "result": "pass",
                    },
                    {
                        "feature": FEATURE_ID,
                        "edge": "design→code",
                        "name": "req_tags_present",
                        "result": "pass",
                    },
                    {
                        "feature": FEATURE_ID,
                        "edge": "design→code",
                        "name": "follows_coding_standards",
                        "result": "pass",
                    },
                ],
                "fp_results": [
                    {
                        "feature": FEATURE_ID,
                        "edge": "design→code",
                        "status": "completed",
                        "message": "Generated auth implementation",
                        "converged": False,
                        "delta": 1,
                        "cost_usd": 0.15,
                        "artifacts": [
                            {
                                "path": "src/auth.py",
                                "content": "\n".join(
                                    [
                                        "# Implements: REQ-F-AUTH-001",
                                        "",
                                        "def login() -> bool:",
                                        "    return True",
                                    ]
                                )
                                + "\n",
                            }
                        ],
                    }
                ],
            },
            indent=2,
        )
    )

    append_run_event(
        project_root / ".ai-workspace" / "events" / "events.jsonl",
        project_name=project_root.name,
        semantic_type="intent_raised",
        actor="pytest",
        feature=FEATURE_ID,
        edge="design→code",
        payload={
            "intent_id": "INT-FP-WORKER-001",
            "trigger": "Seed worker-backed dispatch",
            "delta": "Code artifact missing",
            "signal_source": "test_failure",
            "vector_type": "feature",
            "severity": "high",
            "requires_spec_change": False,
            "affected_features": [FEATURE_ID],
            "affected_req_keys": [FEATURE_ID],
        },
    )

    dispatched = _run_runtime(project_root, "intent-observer", "--once", "--run-agent")

    assert dispatched["dispatched_count"] == 1
    assert dispatched["dispatches"][0]["feature"] == FEATURE_ID
    assert dispatched["dispatches"][0]["edge"] == "design→code"
    assert dispatched["dispatches"][0]["status"] == "converged"

    run_id = dispatched["dispatches"][0]["edge_started_run_id"]
    assert (project_root / "src" / "auth.py").exists()
    assert (project_root / ".ai-workspace" / "agents" / f"fp_result_{run_id}.json").exists()

    events_file = project_root / ".ai-workspace" / "events" / "events.jsonl"
    semantic_types = [
        json.loads(line)["run"]["facets"]["sdlc:event_type"]["type"]
        for line in events_file.read_text().splitlines()
        if line.strip()
    ]
    assert "edge_started" in semantic_types
    assert "iteration_completed" in semantic_types
    assert "edge_converged" in semantic_types
