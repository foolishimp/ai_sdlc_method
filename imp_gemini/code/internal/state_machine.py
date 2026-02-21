# Implements: REQ-F-BOOT-001
import os
import json
from enum import Enum
from pathlib import Path

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
        self.workspace_root = Path(workspace_root)
        self.events_file = self.workspace_root / "events" / "events.jsonl"
        self.features_dir = self.workspace_root / "features" / "active"

    def _get_events(self):
        if not self.events_file.exists():
            return []
        events = []
        with open(self.events_file, "r") as f:
            for line in f:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return events

    def get_current_state(self) -> ProjectState:
        if not self.workspace_root.exists():
            return ProjectState.UNINITIALISED

        intent_file = self.workspace_root / "spec" / "INTENT.md"
        if not intent_file.exists() or intent_file.stat().st_size == 0:
            return ProjectState.NEEDS_INTENT

        if not self.features_dir.exists() or not any(self.features_dir.iterdir()):
            return ProjectState.NO_FEATURES

        events = self._get_events()
        
        # Stuck detection: Check if last 3 iterations for any feature have same delta
        feature_deltas = {}
        for event in events:
            if event.get("event_type") == "iteration_completed":
                feat = event.get("feature")
                delta = event.get("delta")
                if feat not in feature_deltas:
                    feature_deltas[feat] = []
                feature_deltas[feat].append(delta)
        
        for feat, deltas in feature_deltas.items():
            if len(deltas) >= 3 and len(set(deltas[-3:])) == 1:
                return ProjectState.STUCK

        active_features = self.get_active_features()
        if active_features:
            all_converged = True
            for feat in active_features:
                if feat.get("status") != "converged":
                    all_converged = False
                    break
            if all_converged:
                return ProjectState.ALL_CONVERGED

        return ProjectState.IN_PROGRESS

    def get_active_features(self):
        if not self.features_dir.exists():
            return []
        import yaml
        features = []
        for feat_file in self.features_dir.glob("*.yml"):
            with open(feat_file, "r") as f:
                try:
                    # Skip the '---' if present
                    content = f.read()
                    if content.startswith("---"):
                        content = content[3:]
                    data = yaml.safe_load(content)
                    if data:
                        features.append(data)
                except Exception:
                    continue
        return features
