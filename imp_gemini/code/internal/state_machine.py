# Implements: REQ-F-BOOT-001
import os
import json
import yaml
from enum import Enum
from pathlib import Path
from . import workspace_state

class ProjectState(Enum):
    UNINITIALISED = "UNINITIALISED"
    NEEDS_CONSTRAINTS = "NEEDS_CONSTRAINTS"
    NEEDS_INTENT = "NEEDS_INTENT"
    NO_FEATURES = "NO_FEATURES"
    STUCK = "STUCK"
    ALL_BLOCKED = "ALL_BLOCKED"
    IN_PROGRESS = "IN_PROGRESS"
    ALL_CONVERGED = "ALL_CONVERGED"

class StateManager:
    def __init__(self, workspace_root: str = ".ai-workspace"):
        # workspace_root here is actually the .ai-workspace dir
        self.workspace_root = Path(workspace_root)
        # project_root is the parent
        self.project_root = self.workspace_root.parent if self.workspace_root.name == ".ai-workspace" else self.workspace_root

    def get_current_state(self) -> ProjectState:
        state_str = workspace_state.detect_workspace_state(self.project_root)
        return ProjectState(state_str)

    def get_active_features(self):
        return workspace_state.get_active_features(self.workspace_root)

    def get_next_actionable_feature(self):
        features = self.get_active_features()
        return workspace_state.select_next_feature(features)

    def get_next_edge(self, feature):
        # Need to load topology
        topology_path = Path(__file__).parent.parent / "config" / "graph_topology.yml"
        with open(topology_path, "r") as f:
            topology = yaml.safe_load(f)
        return workspace_state.get_next_edge(feature, topology)
