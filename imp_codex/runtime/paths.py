"""Filesystem layout helpers for the Codex runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

import yaml


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = PACKAGE_ROOT / "code"
CONFIG_ROOT = PLUGIN_ROOT / "config"


def _load_yaml(path: Path) -> dict:
    with open(path) as handle:
        documents = [doc for doc in yaml.safe_load_all(handle) if doc is not None]
    merged: dict = {}
    for document in documents:
        merged.update(document)
    return merged


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def detect_workspace_scope(project_root: Path) -> dict:
    """Classify whether the requested workspace root is project- or tenant-scoped."""

    resolved = project_root.resolve()
    for candidate in (resolved, *resolved.parents):
        if not candidate.name.startswith("imp_"):
            continue
        repo_root = candidate.parent
        if not repo_root.exists():
            continue
        try:
            has_impl_tenants = any(
                child.is_dir() and child.name.startswith("imp_")
                for child in repo_root.iterdir()
            )
        except OSError:
            has_impl_tenants = False
        if not (repo_root / "specification").exists() and not has_impl_tenants:
            continue
        return {
            "scope": "tenant",
            "tenant_root": candidate,
            "recommended_project_root": repo_root,
            "warning": (
                "Warning: running from inside an implementation tenant - "
                "workspace will be scoped to this tenant only. "
                "Run from the project root to span all tenants."
            ),
        }
    return {
        "scope": "project",
        "tenant_root": None,
        "recommended_project_root": resolved,
        "warning": None,
    }


@dataclass(frozen=True)
class RuntimePaths:
    """Computed repository and workspace paths."""

    project_root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_root", self.project_root.resolve())

    @property
    def workspace_root(self) -> Path:
        return self.project_root / ".ai-workspace"

    @property
    def events_file(self) -> Path:
        return self.workspace_root / "events" / "events.jsonl"

    @property
    def status_file(self) -> Path:
        return self.workspace_root / "STATUS.md"

    @property
    def tasks_root(self) -> Path:
        return self.workspace_root / "tasks"

    @property
    def active_tasks_dir(self) -> Path:
        return self.tasks_root / "active"

    @property
    def active_tasks_file(self) -> Path:
        return self.active_tasks_dir / "ACTIVE_TASKS.md"

    @property
    def finished_tasks_dir(self) -> Path:
        return self.tasks_root / "finished"

    @property
    def features_root(self) -> Path:
        return self.workspace_root / "features"

    @property
    def feature_index_path(self) -> Path:
        return self.features_root / "feature_index.yml"

    @property
    def active_features_dir(self) -> Path:
        return self.features_root / "active"

    @property
    def completed_features_dir(self) -> Path:
        return self.features_root / "completed"

    @property
    def feature_template_path(self) -> Path:
        return self.features_root / "feature_vector_template.yml"

    @property
    def graph_dir(self) -> Path:
        return self.workspace_root / "graph"

    @property
    def graph_topology_path(self) -> Path:
        return self.graph_dir / "graph_topology.yml"

    @property
    def evaluator_defaults_path(self) -> Path:
        return self.graph_dir / "evaluator_defaults.yml"

    @property
    def named_compositions_path(self) -> Path:
        return self.graph_dir / "named_compositions.yml"

    @property
    def edges_dir(self) -> Path:
        return self.graph_dir / "edges"

    @property
    def profiles_dir(self) -> Path:
        return self.workspace_root / "profiles"

    @property
    def codex_context_dir(self) -> Path:
        return self.workspace_root / "codex" / "context"

    @property
    def context_manifest_path(self) -> Path:
        return self.codex_context_dir / "context_manifest.yml"

    @property
    def project_constraints_path(self) -> Path:
        return self.codex_context_dir / "project_constraints.yml"

    @property
    def specification_dir(self) -> Path:
        return self.project_root / "specification"

    @property
    def intent_path(self) -> Path:
        return self.specification_dir / "INTENT.md"

    @property
    def intents_dir(self) -> Path:
        return self.workspace_root / "intents"

    @property
    def snapshots_dir(self) -> Path:
        return self.workspace_root / "snapshots"

    def ensure_workspace_dirs(self) -> None:
        for directory in (
            self.workspace_root,
            self.events_file.parent,
            self.active_features_dir,
            self.completed_features_dir,
            self.tasks_root,
            self.active_tasks_dir,
            self.finished_tasks_dir,
            self.graph_dir,
            self.edges_dir,
            self.profiles_dir,
            self.codex_context_dir,
            self.intents_dir,
            self.snapshots_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        for directory in ("adrs", "data_models", "templates", "policy", "standards"):
            (self.codex_context_dir / directory).mkdir(parents=True, exist_ok=True)


def bootstrap_workspace(
    project_root: Path,
    *,
    project_name: str | None = None,
    default_profile: str = "standard",
) -> RuntimePaths:
    """Scaffold the minimal workspace files needed by the executable runtime."""

    paths = RuntimePaths(project_root)
    paths.ensure_workspace_dirs()

    if not paths.graph_topology_path.exists():
        shutil.copy2(CONFIG_ROOT / "graph_topology.yml", paths.graph_topology_path)
    if not paths.evaluator_defaults_path.exists():
        shutil.copy2(CONFIG_ROOT / "evaluator_defaults.yml", paths.evaluator_defaults_path)
    if not paths.named_compositions_path.exists():
        shutil.copy2(CONFIG_ROOT / "named_compositions.yml", paths.named_compositions_path)

    for edge_config in sorted((CONFIG_ROOT / "edge_params").glob("*.yml")):
        destination = paths.edges_dir / edge_config.name
        if not destination.exists():
            shutil.copy2(edge_config, destination)

    for profile_config in sorted((CONFIG_ROOT / "profiles").glob("*.yml")):
        destination = paths.profiles_dir / profile_config.name
        if not destination.exists():
            shutil.copy2(profile_config, destination)

    if not paths.feature_template_path.exists():
        shutil.copy2(CONFIG_ROOT / "feature_vector_template.yml", paths.feature_template_path)

    if not paths.project_constraints_path.exists():
        constraints = _load_yaml(CONFIG_ROOT / "project_constraints_template.yml")
        constraints.setdefault("project", {})
        constraints["project"]["name"] = project_name or paths.project_root.name
        constraints["project"]["default_profile"] = default_profile
        _write_yaml(paths.project_constraints_path, constraints)

    return paths


__all__ = [
    "CONFIG_ROOT",
    "PACKAGE_ROOT",
    "PLUGIN_ROOT",
    "RuntimePaths",
    "bootstrap_workspace",
    "detect_workspace_scope",
]
