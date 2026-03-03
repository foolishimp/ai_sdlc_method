from enum import Enum
from typing import List, Dict, Any, Optional

class ProjectState(Enum):
    UNINITIALISED = "uninitialised"
    INITIALISING = "initialising"
    ACTIVE = "active"
    STUCK = "stuck"
    ALL_CONVERGED = "all_converged"

class WorkspaceState:
    def __init__(self, tenant_id: str, project_id: str, db: Any = None, mock_data: Dict = None):
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.db = db
        self.mock_data = mock_data or {}

    def get_events(self) -> List[Dict]:
        return self.mock_data.get("events", [])

    def get_features(self) -> List[Dict]:
        return self.mock_data.get("features", [])

    def detect_state(self) -> ProjectState:
        events = self.get_events()
        features = self.get_features()

        if not events and not features:
            return ProjectState.UNINITIALISED

        # Check for convergence
        if any(e.get("event_type") == "edge_converged" for e in events) or \
           any(f.get("status") == "converged" for f in features):
            return ProjectState.ALL_CONVERGED

        # Check for stuck state (last 3 iterations have same delta > 0)
        iter_events = [e for e in events if e.get("event_type") == "iteration_completed"]
        if len(iter_events) >= 3:
            last_three = iter_events[-3:]
            deltas = [e.get("delta") for e in last_three]
            if all(d == deltas[0] and d > 0 for d in deltas):
                return ProjectState.STUCK

        return ProjectState.ACTIVE
