"""Named reusable runtime behaviors for command/skill execution."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Iterable

from .evaluators import run_agent_checks, run_deterministic_checks
from .paths import RuntimePaths


BEHAVIOR_REGISTRY = {
    "construct": "candidate_artifact_refs_v1",
    "evaluate": "edge_evaluator_mix_v1",
    "review": "human_gate_closeout_v1",
}


def get_behavior_registry() -> dict[str, str]:
    return dict(BEHAVIOR_REGISTRY)


def resolve_candidate_artifact_behavior(project_root: Path, artifact_paths: Iterable[str] | None) -> dict:
    project_root = project_root.resolve()
    refs: list[dict] = []
    for raw_path in artifact_paths or []:
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = (project_root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        if not candidate.exists() or not candidate.is_file():
            raise FileNotFoundError(f"Candidate artifact not found: {raw_path}")
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        try:
            display_path = str(candidate.relative_to(project_root))
        except ValueError:
            display_path = str(candidate)
        refs.append(
            {
                "path": display_path,
                "sha256": f"sha256:{digest}",
                "bytes": candidate.stat().st_size,
            }
        )
    return {
        "behavior": BEHAVIOR_REGISTRY["construct"],
        "artifact_refs": refs,
        "artifact_count": len(refs),
    }


def resolve_iteration_evaluation_behavior(
    paths: RuntimePaths,
    *,
    feature: str,
    edge: str,
    required_evaluator_types: Iterable[str],
    evaluators: Iterable[dict] | None = None,
    delta: int | None = None,
    converged: bool | None = None,
    run_agent: bool = False,
    run_deterministic: bool = False,
) -> dict:
    required_types = list(required_evaluator_types)
    human_required = "human" in required_types
    auto_infer_evaluators = (
        evaluators is None
        and delta is None
        and converged is None
        and not run_agent
        and not run_deterministic
    )
    evaluator_details = list(evaluators or [])

    if evaluators is None and (run_agent or run_deterministic or auto_infer_evaluators):
        if run_agent or (auto_infer_evaluators and "agent" in required_types):
            evaluator_details.extend(run_agent_checks(paths, edge, feature=feature))
        if run_deterministic or (auto_infer_evaluators and "deterministic" in required_types):
            evaluator_details.extend(run_deterministic_checks(paths, edge))
        if evaluator_details:
            delta = sum(
                1 for item in evaluator_details
                if item.get("required") and item.get("result") == "fail"
            )
            if converged is None:
                converged = delta == 0

    if converged is None:
        converged = delta == 0 if delta is not None else False
    if delta is None:
        delta = 0 if converged else 1

    if human_required and delta == 0 and not any(item.get("type") == "human" for item in evaluator_details):
        evaluator_details.append(
            {
                "name": "human_review",
                "type": "human",
                "result": "pending",
                "required": True,
            }
        )
        converged = False

    status = "pending_review" if human_required and delta == 0 else ("converged" if converged else "iterating")
    return {
        "behavior": BEHAVIOR_REGISTRY["evaluate"],
        "required_evaluator_types": required_types,
        "human_required": human_required,
        "auto_inferred": auto_infer_evaluators,
        "evaluator_details": evaluator_details,
        "delta": delta,
        "converged": converged,
        "status": status,
    }


def apply_review_behavior(
    feature_doc: dict,
    *,
    review_edge: str,
    decision: str,
    feedback: str,
    iteration: int,
    latest_delta: int,
    timestamp: str,
) -> dict:
    updated_feature = deepcopy(feature_doc)
    updated_feature.setdefault("trajectory", {})
    all_pass = latest_delta == 0 and decision == "approved"

    for asset in review_edge.replace("↔", "→").split("→"):
        asset = asset.strip()
        trajectory = dict(updated_feature.get("trajectory", {}).get(asset, {}))
        trajectory["human_review"] = {
            "decision": decision,
            "feedback": feedback,
            "timestamp": timestamp,
        }
        if decision == "approved" and all_pass:
            trajectory["status"] = "converged"
            trajectory["converged_at"] = timestamp
        elif decision == "rejected":
            trajectory["status"] = "iterating"
        elif decision == "refined":
            trajectory["status"] = "pending_review"
        updated_feature["trajectory"][asset] = trajectory

    return {
        "behavior": BEHAVIOR_REGISTRY["review"],
        "feature_doc": updated_feature,
        "iteration": iteration,
        "decision": decision,
        "all_evaluators_pass": all_pass,
        "converged": decision == "approved" and all_pass,
    }
