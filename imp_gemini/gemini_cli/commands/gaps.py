
# Implements: REQ-TOOL-005, REQ-LIFE-006, REQ-EVOL-003, REQ-F-EVOL-001
import re
from pathlib import Path
from typing import List, Set, Dict
from gemini_cli.engine.state import EventStore

class GapsCommand:
    """Scans for REQ keys lacking tests or implementation.
    Implements: REQ-EVOL-003 (Feature Proposal Emission).
    """
    
    def __init__(self, workspace_root: Path, impl_name: str = "gemini"):
        self.workspace_root = workspace_root
        if self.workspace_root.name == ".ai-workspace":
            self.project_root = self.workspace_root.parent
        else:
            self.project_root = self.workspace_root
            self.workspace_root = self.project_root / ".ai-workspace"
            
        self.impl_name = impl_name
        self.impl_dir = self.project_root / f"imp_{impl_name}"
        if not self.impl_dir.exists():
            self.impl_dir = self.project_root
            
        self.store = EventStore(self.workspace_root)

    def run(self):
        print(f"\nTraceability Gap Analysis (Tenant: {self.impl_name})")
        print("="*40)
        
        # 1. Load all REQ keys from Spec
        req_keys = self._load_req_keys()
        if not req_keys:
            print("No REQ keys found in specification.")
            return

        # 2. Scan Code and Tests
        impl_tags = self._scan_tags("Implements: ")
        test_tags = self._scan_tags("Validates: ")
        
        # 3. Report Gaps
        print(f"Total Requirements: {len(req_keys)}")
        print("-" * 20)
        
        gaps_found = 0
        missing_reqs = []
        for req in sorted(req_keys):
            has_impl = req in impl_tags
            has_test = req in test_tags
            
            if not has_impl or not has_test:
                gaps_found += 1
                status = []
                if not has_impl: status.append("MISSING_IMPL")
                if not has_test: status.append("MISSING_TEST")
                status_str = ", ".join(status)
                print(f"✗ {req:<20} {status_str}")
                missing_reqs.append({"req": req, "status": status_str})
        
        if gaps_found == 0:
            print("No gaps detected! Full traceability achieved. 🎉")
        else:
            print(f"\nTotal Gaps: {gaps_found}")
            
            # 4. Emit intent_raised (REQ-LIFE-006)
            raised_ev = self.store.emit(
                "intent_raised",
                project="imp_gemini",
                data={
                    "trigger": "gap_found",
                    "signal_source": "gap",
                    "affected_req_keys": [r["req"] for r in missing_reqs],
                    "description": f"Found {gaps_found} traceability gaps requiring implementation or testing."
                }
            )
            
            # 5. Emit feature_proposal (REQ-EVOL-003)
            # We propose a single 'T-COMPLY' feature to resolve the gap cluster
            self.store.emit(
                "feature_proposal",
                project="imp_gemini",
                data={
                    "proposal_id": f"PROP-{raised_ev['run']['runId'][:8]}",
                    "feature_id": f"REQ-F-COMPLY-{raised_ev['run']['runId'][:4]}",
                    "title": f"Traceability Compliance for {self.impl_name} Tenant",
                    "requirements": [r["req"] for r in missing_reqs],
                    "intent_id": raised_ev["run"]["runId"],
                    "rationale": f"Automated proposal to close {gaps_found} traceability gaps.",
                    "status": "draft"
                }
            )
            
            print(f"Emitted intent_raised and feature_proposal for {gaps_found} gaps.")

    def _load_req_keys(self) -> Set[str]:
        keys = set()
        
        # Recursively find all REQ keys in the project root
        # Focus on authoritative specification sources, skip illustrative docs
        skip_dirs = [".ai-workspace", "tests/e2e/runs", "specification/ux", "specification/verification", "specification/presentations"]
        
        for path in self.project_root.rglob("*.md"):
            if any(s in str(path) for s in skip_dirs):
                continue
            if path.is_file():
                content = path.read_text(errors="ignore")
                # Match REQ-F-GMON-001 or REQ-GRAPH-001
                keys.update(re.findall(r"(REQ-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d+)", content))
        
        active_features = self.workspace_root / "features" / "active"
        if active_features.exists():
            for path in active_features.glob("*.yml"):
                content = path.read_text(errors="ignore")
                keys.update(re.findall(r"(REQ-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d+)", content))
        return keys

    def _scan_tags(self, prefix: str) -> Set[str]:
        tags = set()
        search_dirs = [self.impl_dir if self.impl_dir.exists() else self.project_root]
        
        # Explicitly add tests/ if it exists within the impl_dir or project_root
        tests_dir = search_dirs[0] / "tests"
        if tests_dir.exists():
            search_dirs.append(tests_dir)
            
        for search_dir in search_dirs:
            for path in search_dir.rglob("*"):
                # Skip .ai-workspace and e2e test runs to avoid noise
                if ".ai-workspace" in str(path) or "tests/e2e/runs" in str(path):
                    continue
                    
                if path.is_file() and path.suffix in [".py", ".ts", ".js", ".go", ".rs", ".html", ".scala"]:
                    try:
                        content = path.read_text(errors="ignore")
                        for line in content.splitlines():
                            if prefix in line:
                                line_matches = re.findall(r"REQ-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d+", line)
                                tags.update(line_matches)
                    except:
                        continue
        return tags
