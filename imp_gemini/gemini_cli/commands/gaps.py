
import re
from pathlib import Path
from typing import List, Set

class GapsCommand:
    """Scans for REQ keys lacking tests or implementation."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def run(self):
        print(f"\nTraceability Gap Analysis")
        print("="*40)
        
        # 1. Load all REQ keys from Spec
        req_keys = self._load_req_keys()
        if not req_keys:
            print("No REQ keys found in specification.")
            return

        # 2. Scan Code and Tests
        impl_tags = self._scan_tags("Implements: REQ-")
        test_tags = self._scan_tags("Validates: REQ-")
        
        # 3. Report Gaps
        print(f"Total Requirements: {len(req_keys)}")
        print("-" * 20)
        
        gaps_found = 0
        for req in sorted(req_keys):
            has_impl = req in impl_tags
            has_test = req in test_tags
            
            if not has_impl or not has_test:
                gaps_found += 1
                status = []
                if not has_impl: status.append("MISSING_IMPL")
                if not has_test: status.append("MISSING_TEST")
                status_str = ", ".join(status)
                print(f"✗ {req:<15} {status_str}")
        
        if gaps_found == 0:
            print("No gaps detected! Full traceability achieved. 🎉")
        else:
            print(f"\nTotal Gaps: {gaps_found}")

    def _load_req_keys(self) -> Set[str]:
        keys = set()
        spec_file = self.project_root / "specification" / "REQUIREMENTS.md"
        if spec_file.exists():
            content = spec_file.read_text()
            keys.update(re.findall(r"(REQ-F-[A-Z]+-\d+)", content))
        return keys

    def _scan_tags(self, prefix: str) -> Set[str]:
        tags = set()
        for path in self.project_root.rglob("*"):
            if path.suffix in [".py", ".ts", ".js", ".go", ".rs"] and ".ai-workspace" not in str(path):
                try:
                    content = path.read_text(errors="ignore")
                    tags.update(re.findall(prefix + r"([A-Z]+-[A-Z]+-\d+)", content))
                except:
                    continue
        return tags
