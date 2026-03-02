# Implements: REQ-LIFE-009, REQ-UX-003, ADR-011
import re
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Set, Optional
from gemini_cli.engine.state import EventStore, Projector

class SpecReviewCommand:
    """Stateless review of workspace against spec (REQ-LIFE-009)."""
    
    def __init__(self, workspace_root: Path, design_name: str = "gemini_genesis"):
        self.workspace_root = workspace_root
        self.design_name = design_name
        self.store = EventStore(workspace_root)
        self.project_root = workspace_root.parent

    def run(self):
        print("\nSpec Review: Workspace Gradient Analysis")
        print("="*40)
        
        # 1. Load Spec Requirements
        requirements = self._load_requirements()
        print(f"Loaded {len(requirements)} requirements from specification.")

        # 2. Load Workspace State (Features & Events)
        features = self._load_active_features()
        events = self.store.load_all()
        
        # 3. Compute Delta (The Gradient)
        intents_raised = 0
        
        # Check 1: Orphaned Requirements (Spec exists, no Feature Vector)
        req_keys_in_spec = set(requirements.keys())
        req_keys_in_features = set()
        for f in features:
            req_keys_in_features.update(f.get("req_keys", []) or [])
            
        orphans = req_keys_in_spec - req_keys_in_features
        if orphans:
            print(f"\n[GRADIENT] {len(orphans)} Orphaned Requirements Detected:")
            for req in sorted(orphans):
                print(f"  ! {req}: No active feature vector found.")
                self._raise_intent(
                    trigger="spec_orphan",
                    signal_source="gap",
                    affected_req_keys=[req],
                    description=f"Requirement {req} exists in spec but has no active feature vector."
                )
                intents_raised += 1

        # Check 2: Stalled Features (In progress for too long or no recent events)
        for f in features:
            fid = f.get("feature")
            last_activity = self._get_last_activity(events, fid)
            if last_activity:
                delta_days = (datetime.now(timezone.utc) - last_activity).days
                if delta_days > 7:
                    print(f"\n[GRADIENT] Stalled Feature Detected: {fid} ({delta_days} days since last event)")
                    self._raise_intent(
                        trigger="stalled_feature",
                        signal_source="process_gap",
                        affected_req_keys=f.get("req_keys", []) or [],
                        description=f"Feature {fid} has been stalled for {delta_days} days. Possible blocked trajectory."
                    )
                    intents_raised += 1

        # Check 3: Traceability Gaps (Impl/Test missing)
        from .gaps import GapsCommand
        gaps_cmd = GapsCommand(self.project_root, impl_name=self.design_name.replace("_genesis", ""))
        # GapsCommand already emits intents for gaps.
        # Here we just trigger it for the report.
        gaps_cmd.run()

        print("\n" + "="*40)
        if intents_raised == 0:
            print("Workspace is homeostatic with specification. No new work detected.")
        else:
            print(f"Review complete. {intents_raised} new intents raised to close the gradient.")

    def _load_requirements(self) -> Dict[str, str]:
        requirements = {}
        spec_dir = self.workspace_root / "spec"
        if not spec_dir.exists():
            spec_dir = self.project_root / "specification"
            
        if spec_dir.exists():
            for path in spec_dir.glob("*.md"):
                content = path.read_text(errors="ignore")
                # Simple REQ extraction
                matches = re.findall(r"(REQ-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d+):?\s*(.*)", content)
                for key, desc in matches:
                    requirements[key] = desc.strip()
        return requirements

    def _load_active_features(self) -> List[Dict]:
        features = []
        feature_dir = self.workspace_root / "features" / "active"
        if feature_dir.exists():
            for path in feature_dir.glob("*.yml"):
                with open(path, "r") as f:
                    data = yaml.safe_load(f)
                    if data:
                        features.append(data)
        return features

    def _get_last_activity(self, events: List[Dict], feature_id: str) -> Optional[datetime]:
        last_ts = None
        for ev in events:
            facets = ev.get("run", {}).get("facets", {})
            req_facet = facets.get("sdlc_req_keys", {})
            if req_facet.get("feature_id") == feature_id:
                ts_str = ev.get("eventTime")
                if ts_str:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if not last_ts or ts > last_ts:
                        last_ts = ts
        return last_ts

    def _raise_intent(self, trigger: str, signal_source: str, affected_req_keys: List[str], description: str):
        self.store.emit(
            "intent_raised",
            project=self.design_name.replace("_genesis", ""),
            data={
                "trigger": trigger,
                "signal_source": signal_source,
                "affected_req_keys": affected_req_keys,
                "description": description,
                "severity": "warning"
            }
        )
