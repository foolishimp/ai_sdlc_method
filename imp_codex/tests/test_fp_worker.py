# Validates: REQ-F-ENGINE-001, REQ-F-LIFE-001
"""Focused tests for the Codex-native F_P worker."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from imp_codex.runtime.edge_runner import DispatchTarget
from imp_codex.runtime.fp_supervisor import load_fp_manifest, write_fp_manifest
from imp_codex.runtime.fp_worker import run_fp_work
from imp_codex.runtime.paths import RuntimePaths, bootstrap_workspace


def _configure_agent_invocation(paths: RuntimePaths) -> Path:
    constraints = yaml.safe_load(paths.project_constraints_path.read_text())
    constraints["agent_invocation"] = {
        "mode": "file",
        "fallback": "fail",
        "file": ".ai-workspace/codex/context/agent_evaluations.json",
    }
    paths.project_constraints_path.write_text(yaml.safe_dump(constraints, sort_keys=False))
    return paths.codex_context_dir / "agent_evaluations.json"


def _write_feature(paths: RuntimePaths, feature_id: str) -> None:
    feature_doc = yaml.safe_load(paths.feature_template_path.read_text())
    feature_doc["feature"] = feature_id
    feature_doc["title"] = feature_id
    feature_doc["profile"] = "minimal"
    feature_doc["status"] = "in_progress"
    (paths.active_features_dir / f"{feature_id}.yml").write_text(yaml.safe_dump(feature_doc, sort_keys=False))


def test_run_fp_work_file_contract_writes_artifact_and_marks_manifest_completed(tmp_path):
    project_root = tmp_path / "demo"
    paths = bootstrap_workspace(project_root, project_name="demo")
    invocation_file = _configure_agent_invocation(paths)
    _write_feature(paths, "REQ-F-FP-001")

    target = DispatchTarget(
        intent_id="INT-FP-001",
        feature_id="REQ-F-FP-001",
        edge="design→code",
        feature_vector={"feature": "REQ-F-FP-001", "profile": "minimal", "trajectory": {}},
    )
    manifest_path = write_fp_manifest(paths, target, "run-fp-001", 1, 1.0, ["code_missing"])
    invocation_file.write_text(
        json.dumps(
            {
                "fp_results": [
                    {
                        "run_id": "run-fp-001",
                        "status": "completed",
                        "message": "Generated code artifact",
                        "converged": False,
                        "delta": 1,
                        "cost_usd": 0.12,
                        "artifacts": [
                            {
                                "path": "src/generated.py",
                                "content": "\n".join(
                                    [
                                        "# Implements: REQ-F-FP-001",
                                        "",
                                        "def generated() -> bool:",
                                        "    return True",
                                    ]
                                )
                                + "\n",
                            }
                        ],
                    }
                ]
            },
            indent=2,
        )
    )

    result = run_fp_work(project_root, run_id="run-fp-001")

    assert result.status == "completed"
    assert result.provider == "file"
    assert result.delta == 1
    assert (project_root / "src" / "generated.py").exists()
    manifest = load_fp_manifest(manifest_path)
    assert manifest["status"] == "completed"
    assert manifest["result_run_status"] == "completed"
    persisted = json.loads(Path(result.result_path).read_text())
    assert persisted["artifacts"][0]["path"] == "src/generated.py"


def test_run_fp_work_marks_missing_file_contract_as_pending_failure(tmp_path):
    project_root = tmp_path / "demo"
    paths = bootstrap_workspace(project_root, project_name="demo")
    _configure_agent_invocation(paths)
    _write_feature(paths, "REQ-F-FP-002")

    target = DispatchTarget(
        intent_id="INT-FP-002",
        feature_id="REQ-F-FP-002",
        edge="design→code",
        feature_vector={"feature": "REQ-F-FP-002", "profile": "minimal", "trajectory": {}},
    )
    manifest_path = write_fp_manifest(paths, target, "run-fp-002", 1, 1.0, ["code_missing"])

    result = run_fp_work(project_root, run_id="run-fp-002")

    assert result.status == "error"
    assert result.provider == "file_missing"
    manifest = load_fp_manifest(manifest_path)
    assert manifest["status"] == "pending"
    assert manifest["result_run_status"] == "error"
