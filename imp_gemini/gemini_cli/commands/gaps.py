
import re
from pathlib import Path
from typing import List, Set
from gemini_cli.engine.state import EventStore

class GapsCommand:
    """Scans for REQ keys lacking tests or implementation."""
    
    def __init__(self, project_root: Path, impl_name: str = "gemini"):
        self.project_root = project_root
        self.impl_name = impl_name
        self.impl_dir = self.project_root / f"imp_{impl_name}"
        # Support running against external workspaces
        ws_dir = self.project_root / ".ai-workspace"
        if not ws_dir.exists() and self.project_root.name == ".ai-workspace":
            ws_dir = self.project_root
        self.store = EventStore(ws_dir)

    def run(self):
        print(f"\nTraceability Gap Analysis (Tenant: {self.impl_name})")
        print("="*40)
        
        # 1. Load all REQ keys from Spec
        req_keys = self._load_req_keys()
        if not req_keys:
            print("No REQ keys found in specification.")
            return

        # 2. Scan Code and Tests (scoped to implementation directory)
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
            # Emit intent_raised for the gap cluster (REQ-LIFE-006)
            self.store.emit(
                "intent_raised",
                project="imp_gemini",
                data={
                    "trigger": "gap_found",
                    "signal_source": "gap",
                    "affected_req_keys": [r["req"] for r in missing_reqs],
                    "description": f"Found {gaps_found} traceability gaps requiring implementation or testing."
                }
            )
            print(f"Emitted intent_raised event for {gaps_found} gaps.")

    def _load_req_keys(self) -> Set[str]:
        keys = set()
        # Look in both REQUIREMENTS.md and active features
        # Search paths: 
        # 1. Project-specific specification/
        # 2. .ai-workspace/spec/
        # 3. Shared root specification/ (e.g., ai_sdlc_method/specification/)
        search_paths = [
            self.project_root / "specification",
            self.project_root / ".ai-workspace" / "spec",
            # If we are in an implementation directory, check the shared parent specification
            self.project_root.parent / "specification" if self.project_root.name.startswith("imp_") else None
        ]
        
        for spec_dir in search_paths:
            if spec_dir and spec_dir.exists():
                for path in spec_dir.glob("*.md"):
                    content = path.read_text(errors="ignore")
                    # Match REQ-F-GMON-001 or REQ-GRAPH-001
                    keys.update(re.findall(r"(REQ-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d+)", content))
        
        active_features = self.project_root / ".ai-workspace" / "features" / "active"
        if active_features.exists():
            for path in active_features.glob("*.yml"):
                content = path.read_text(errors="ignore")
                keys.update(re.findall(r"(REQ-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d+)", content))
        return keys

    def _scan_tags(self, prefix: str) -> Set[str]:
        tags = set()
        search_dir = self.impl_dir if self.impl_dir.exists() else self.project_root
        for path in search_dir.rglob("*"):
            if path.is_file() and path.suffix in [".py", ".ts", ".js", ".go", ".rs", ".html", ".scala"] and ".ai-workspace" not in str(path):
                try:
                    content = path.read_text(errors="ignore")
                    # Match REQ-F-GMON-001 or REQ-GRAPH-001 following the prefix
                    # We look for REQ- followed by the key, allowing for commas and spaces
                    # Examples: 
                    # "# Implements: REQ-ITER-003, REQ-EVAL-002"
                    # "# Implements: REQ-ITER-003 (Tracking)"
                    matches = re.findall(r"REQ-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d+", content)
                    # We filter matches that are preceded by the prefix in the same line
                    for line in content.splitlines():
                        if prefix in line:
                            line_matches = re.findall(r"REQ-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d+", line)
                            tags.update(line_matches)
                except:
                    continue
        return tags
