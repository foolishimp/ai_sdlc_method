# Implements: REQ-UX-001, REQ-UX-003, REQ-UX-004
"""Firestore-backed workspace state detection for Gemini Cloud.

Mirroring the logic of imp_gemini but targeting Firestore documents
instead of local filesystem YAMLs.
"""

from typing import Any, List, Optional, Dict
from dataclasses import dataclass
import enum

# Placeholder for google-cloud-firestore
# In a real environment, this would be: from google.cloud import firestore

class ProjectState(enum.Enum):
    UNINITIALISED = "UNINITIALISED"
    NEEDS_CONSTRAINTS = "NEEDS_CONSTRAINTS"
    NEEDS_INTENT = "NEEDS_INTENT"
    NO_FEATURES = "NO_FEATURES"
    IN_PROGRESS = "IN_PROGRESS"
    ALL_CONVERGED = "ALL_CONVERGED"
    STUCK = "STUCK"
    ALL_BLOCKED = "ALL_BLOCKED"

@dataclass
class WorkspaceState:
    tenant_id: str
    project_id: str
    db: Any  # firestore.Client

    def get_collection_path(self, collection: str) -> str:
        return f"tenants/{self.tenant_id}/projects/{self.project_id}/{collection}"

    def load_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Load events from Firestore ordered by timestamp."""
        # Mock logic for Firestore query
        # events_ref = self.db.collection(self.get_collection_path("events"))
        # docs = events_ref.order_by("timestamp", direction="DESCENDING").limit(limit).stream()
        # return [doc.to_dict() for doc in docs]
        return []

    def get_active_features(self) -> List[Dict[str, Any]]:
        """Load all feature vectors from Firestore."""
        # features_ref = self.db.collection(self.get_collection_path("features"))
        # docs = features_ref.stream()
        # return [doc.to_dict() for doc in docs]
        return []

    def detect_state(self) -> ProjectState:
        """Detect project state from Firestore data."""
        # 1. Check if 'events' collection exists/has data
        events = self.load_events(limit=1)
        if not events:
            # Check for project document
            return ProjectState.UNINITIALISED

        # 2. Check for constraints (stored in a 'config' document)
        # 3. Check for intent (stored in a 'spec' document)
        
        features = self.get_active_features()
        if not features:
            return ProjectState.NO_FEATURES

        all_converged = True
        for fv in features:
            if fv.get("status") != "converged":
                all_converged = False
                break
        
        if all_converged:
            return ProjectState.ALL_CONVERGED

        return ProjectState.IN_PROGRESS

    def get_you_are_here(self, feature: Dict[str, Any]) -> str:
        """Generate the ✓ → ● → ○ string for a feature."""
        traj = feature.get("trajectory", {})
        phases = ["requirements", "design", "code", "unit_tests", "uat_tests"]
        
        markers = []
        for p in phases:
            status = traj.get(p, {}).get("status", "pending")
            if status == "converged": markers.append("✓")
            elif status == "iterating": markers.append("●")
            else: markers.append("○")
            
        return " → ".join(markers)
