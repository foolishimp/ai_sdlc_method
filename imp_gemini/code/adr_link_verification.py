# Implements: REQ-F-ADR-LINK-001
import re
from pathlib import Path
from typing import List, Set

def verify_adr_links(project_root: Path) -> List[str]:
    """Scans features for linked ADRs and verifies the ADR exists."""
    features_dir = project_root / ".ai-workspace" / "features" / "active"
    adrs_dir = project_root / "design" / "adrs"
    
    if not features_dir.exists() or not adrs_dir.exists():
        return []
        
    known_adrs = {p.stem for p in adrs_dir.glob("*.md")}
    issues = []
    
    for feature_file in features_dir.glob("*.yml"):
        content = feature_file.read_text(errors="ignore")
        # Simple extraction of ADR- references
        linked_adrs = re.findall(r"(ADR(?:-[A-Z]+)?-\d{3}[A-Za-z0-9-]*)", content)
        for adr in linked_adrs:
            # Check if this exact ADR exists, or if there's an ADR starting with this ID
            found = False
            for known in known_adrs:
                if known.startswith(adr):
                    found = True
                    break
            if not found:
                issues.append(f"{feature_file.name}: Broken link to {adr}")
                
    return issues
