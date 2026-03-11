# Validates: REQ-TOOL-016, REQ-ITER-001, REQ-LIFE-003
"""Codex-native workspace_state analysis derived from workspace artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from .events import utc_now
from .paths import CONFIG_ROOT, RuntimePaths
from .projections import compute_spec_workspace_join, iter_features, load_yaml


EVAL_SPEC_ALIGNED = "spec_aligned"
EVAL_NO_ORPHANS = "no_orphans"
EVAL_NO_STALE = "no_stale"
EVAL_LOG_COMPLETE = "log_complete"


@dataclass(frozen=True)
class WorkspaceGradient:
    spec_count: int
    workspace_count: int
    active: list[str] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    orphan: list[str] = field(default_factory=list)

    @property
    def is_at_rest(self) -> bool:
        return not self.pending and not self.orphan


@dataclass(frozen=True)
class WorkspaceAsset:
    snapshot_at: str
    gradient: WorkspaceGradient
    feature_count: int
    active_count: int
    converged_count: int
    event_count: int
    incomplete_features: list[str] = field(default_factory=list)
    active_features: list[str] = field(default_factory=list)
    completed_features: list[str] = field(default_factory=list)
    duplicate_features: list[str] = field(default_factory=list)

    def is_at_rest(self) -> bool:
        return self.gradient.is_at_rest and not self.incomplete_features and not self.duplicate_features

    def summary(self) -> str:
        return (
            "workspace_asset("
            f"features={self.feature_count}, "
            f"active={self.active_count}, "
            f"converged={self.converged_count}, "
            f"events={self.event_count})"
        )


@dataclass(frozen=True)
class EvaluatorResult:
    name: str
    passed: bool
    details: list[str] = field(default_factory=list)
    delta_count: int = 0
    required: bool = True


@dataclass(frozen=True)
class WorkspaceAnalysisResult:
    project: str
    asset: WorkspaceAsset
    evaluator_results: list[EvaluatorResult]
    intent_proposals: list[dict]
    total_delta: int
    is_converged: bool

    @property
    def total_count(self) -> int:
        return len(self.evaluator_results)

    @property
    def passed_count(self) -> int:
        return sum(1 for item in self.evaluator_results if item.passed)

    def summary(self) -> str:
        status = "converged" if self.is_converged else "delta"
        return (
            "workspace_analysis("
            f"project={self.project}, "
            f"status={status}, "
            f"delta={self.total_delta}, "
            f"checks={self.passed_count}/{self.total_count})"
        )


def _workspace_analysis_config_path(project_root: Path) -> Path:
    paths = RuntimePaths(project_root)
    workspace_path = paths.edges_dir / "workspace_analysis.yml"
    if workspace_path.exists():
        return workspace_path
    return CONFIG_ROOT / "edge_params" / "workspace_analysis.yml"


def load_workspace_analysis_config(project_root: Path) -> dict:
    path = _workspace_analysis_config_path(project_root)
    if not path.exists():
        return {}
    return load_yaml(path)


def _event_features(events_file: Path) -> tuple[int, set[str]]:
    count = 0
    features: set[str] = set()
    if not events_file.exists():
        return count, features
    with open(events_file) as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            count += 1
            feature = (
                raw.get("run", {}).get("facets", {}).get("sdlc:payload", {}).get("feature")
                or raw.get("feature")
                or raw.get("data", {}).get("feature")
            )
            if feature:
                features.add(str(feature))
    return count, features


def build_workspace_asset(workspace: Path, spec_features_path: Path | None = None) -> WorkspaceAsset:
    """Build Asset<workspace_state> entirely from workspace artifacts."""

    paths = RuntimePaths(workspace)
    join = compute_spec_workspace_join(workspace, spec_features_path=spec_features_path)
    feature_docs = list(iter_features(paths))
    active_features = sorted(
        feature_doc.get("feature")
        for feature_doc, path in feature_docs
        if feature_doc.get("feature")
        and path.parent == paths.active_features_dir
        and feature_doc.get("status") != "converged"
    )
    completed_features = sorted(
        feature_doc.get("feature")
        for feature_doc, path in feature_docs
        if feature_doc.get("feature")
        and (path.parent == paths.completed_features_dir or feature_doc.get("status") == "converged")
    )
    duplicate_features = sorted(set(active_features) & set(completed_features))
    event_count, event_features = _event_features(paths.events_file)
    incomplete = sorted(feature_id for feature_id in active_features if feature_id not in event_features)
    gradient = WorkspaceGradient(
        spec_count=int(join["spec_count"]),
        workspace_count=int(join["workspace_count"]),
        active=list(join["active"]),
        completed=list(join["completed"]),
        pending=list(join["pending"]),
        orphan=list(join["orphan"]),
    )
    return WorkspaceAsset(
        snapshot_at=utc_now(),
        gradient=gradient,
        feature_count=len(set(active_features) | set(completed_features)),
        active_count=len(active_features),
        converged_count=len(completed_features),
        event_count=event_count,
        incomplete_features=incomplete,
        active_features=active_features,
        completed_features=completed_features,
        duplicate_features=duplicate_features,
    )


def _evaluate_spec_aligned(asset: WorkspaceAsset, *, required: bool) -> EvaluatorResult:
    details = list(asset.gradient.pending)
    return EvaluatorResult(
        name=EVAL_SPEC_ALIGNED,
        passed=not details,
        details=details,
        delta_count=len(details),
        required=required,
    )


def _evaluate_no_orphans(asset: WorkspaceAsset, *, required: bool) -> EvaluatorResult:
    active_orphans = sorted(set(asset.active_features) & set(asset.gradient.orphan))
    return EvaluatorResult(
        name=EVAL_NO_ORPHANS,
        passed=not active_orphans,
        details=active_orphans,
        delta_count=len(active_orphans),
        required=required,
    )


def _evaluate_no_stale(asset: WorkspaceAsset, *, required: bool) -> EvaluatorResult:
    return EvaluatorResult(
        name=EVAL_NO_STALE,
        passed=not asset.duplicate_features,
        details=list(asset.duplicate_features),
        delta_count=len(asset.duplicate_features),
        required=required,
    )


def _evaluate_log_complete(asset: WorkspaceAsset, *, required: bool) -> EvaluatorResult:
    return EvaluatorResult(
        name=EVAL_LOG_COMPLETE,
        passed=not asset.incomplete_features,
        details=list(asset.incomplete_features),
        delta_count=len(asset.incomplete_features),
        required=required,
    )


EVALUATOR_REGISTRY = {
    EVAL_SPEC_ALIGNED: _evaluate_spec_aligned,
    EVAL_NO_ORPHANS: _evaluate_no_orphans,
    EVAL_NO_STALE: _evaluate_no_stale,
    EVAL_LOG_COMPLETE: _evaluate_log_complete,
}


def _intent_token(evaluator_name: str) -> str:
    return evaluator_name.upper()


def generate_analysis_intents(
    asset: WorkspaceAsset,
    evaluator_results: list[EvaluatorResult],
    *,
    project: str,
) -> list[dict]:
    """Translate workspace deltas into typed intent proposals."""

    proposals: list[dict] = []
    for result in evaluator_results:
        if result.delta_count <= 0:
            continue
        for detail in result.details or [result.name]:
            feature_id = detail if str(detail).startswith("REQ-F-") else None
            proposals.append(
                {
                    "event_type": "intent_raised",
                    "project": project,
                    "data": {
                        "intent_id": f"INT-WORKSPACE-{_intent_token(result.name)}-{detail}".replace(" ", "-"),
                        "signal_source": "workspace_analysis",
                        "trigger": f"{result.name} detected workspace delta",
                        "delta": result.delta_count,
                        "affected_features": [feature_id] if feature_id else list(asset.active_features),
                        "affected_req_keys": [feature_id] if feature_id else [],
                        "evaluator": result.name,
                        "detail": detail,
                    },
                }
            )
    return proposals


def run_workspace_analysis(
    workspace: Path,
    *,
    project: str,
    spec_features_path: Path | None = None,
) -> WorkspaceAnalysisResult:
    """Run the configured workspace_state evaluator set."""

    asset = build_workspace_asset(workspace, spec_features_path=spec_features_path)
    config = load_workspace_analysis_config(workspace)
    configured = list(config.get("evaluators", []))
    required_checks = set(config.get("convergence", {}).get("required_checks", []))
    evaluator_results: list[EvaluatorResult] = []
    for item in configured:
        name = item.get("name")
        if name not in EVALUATOR_REGISTRY:
            continue
        required = bool(item.get("required", name in required_checks))
        evaluator_results.append(EVALUATOR_REGISTRY[name](asset, required=required))

    total_delta = sum(result.delta_count for result in evaluator_results)
    is_converged = all(
        result.passed
        for result in evaluator_results
        if result.name in required_checks
    )
    intent_proposals = [] if is_converged else generate_analysis_intents(asset, evaluator_results, project=project)
    return WorkspaceAnalysisResult(
        project=project,
        asset=asset,
        evaluator_results=evaluator_results,
        intent_proposals=intent_proposals,
        total_delta=total_delta,
        is_converged=is_converged,
    )


__all__ = [
    "EVAL_LOG_COMPLETE",
    "EVAL_NO_ORPHANS",
    "EVAL_NO_STALE",
    "EVAL_SPEC_ALIGNED",
    "EvaluatorResult",
    "WorkspaceAnalysisResult",
    "WorkspaceAsset",
    "WorkspaceGradient",
    "build_workspace_asset",
    "generate_analysis_intents",
    "load_workspace_analysis_config",
    "run_workspace_analysis",
]
