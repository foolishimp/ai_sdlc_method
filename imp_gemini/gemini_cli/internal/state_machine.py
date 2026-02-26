# Implements: REQ-UX-001, REQ-UX-002
"""
State Manager for Project Genesis.
Orchestrates high-level routing and state-driven prompts.
"""

from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
from .workspace_state import detect_workspace_state, get_active_features, select_next_feature, get_next_edge

class ProjectState(Enum):
    UNINITIALISED = "UNINITIALISED"
    NEEDS_CONSTRAINTS = "NEEDS_CONSTRAINTS"
    NEEDS_INTENT = "NEEDS_INTENT"
    NO_FEATURES = "NO_FEATURES"
    IN_PROGRESS = "IN_PROGRESS"
    ALL_CONVERGED = "ALL_CONVERGED"
    STUCK = "STUCK"
    ALL_BLOCKED = "ALL_BLOCKED"

class StateManager:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)

    def get_current_state(self) -> ProjectState:
        state_str = detect_workspace_state(self.workspace_root.parent)
        return ProjectState(state_str)

    def get_next_actionable_feature(self) -> Optional[Dict[str, Any]]:
        features = get_active_features(self.workspace_root)
        return select_next_feature(features)

    def get_next_edge(self, feature: Dict[str, Any]) -> Optional[str]:
        return get_next_edge(feature)
