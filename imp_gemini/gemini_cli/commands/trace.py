
import re
from pathlib import Path
from typing import Dict, List, Set

class TraceCommand:
    """Projects the traceability matrix for a REQ key."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def run(self, req_key: str):
        print(f"\nTraceability View: {req_key}")
        print("="*40)
        
        # 1. Search in Source Code
        code_files = self._find_tags("Implements: " + req_key)
        code_str = ", ".join(code_files) if code_files else "None"
        print(f"Code Implementation:  {code_str}")
        
        # 2. Search in Tests
        test_files = self._find_tags("Validates: " + req_key)
        test_str = ", ".join(test_files) if test_files else "None"
        print(f"Test Validation:      {test_str}")
        
        # 3. Search in Design
        design_files = self._find_tags(req_key, include_md=True)
        # Filter for design docs specifically if needed
        design_str = ", ".join(design_files) if design_files else "None"
        print(f"Design References:    {design_str}")

    def _find_tags(self, pattern: str, include_md: bool = False) -> List[str]:
        found = []
        extensions = [".py", ".ts", ".js", ".go", ".rs"]
        if include_md:
            extensions.append(".md")
            
        for path in self.project_root.rglob("*"):
            if path.suffix in extensions and ".ai-workspace" not in str(path):
                try:
                    content = path.read_text(errors="ignore")
                    if pattern in content:
                        found.append(str(path.relative_to(self.project_root)))
                except:
                    continue
        return found
