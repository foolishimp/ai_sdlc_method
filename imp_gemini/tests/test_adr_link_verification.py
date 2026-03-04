# Validates: REQ-F-ADR-LINK-001
import pytest
from pathlib import Path
from code.adr_link_verification import verify_adr_links

def test_verify_adr_links(tmp_path: Path):
    ws = tmp_path / ".ai-workspace"
    features_dir = ws / "features" / "active"
    features_dir.mkdir(parents=True)
    
    adrs_dir = tmp_path / "design" / "adrs"
    adrs_dir.mkdir(parents=True)
    
    # Create an ADR
    (adrs_dir / "ADR-001-test.md").write_text("# Test ADR")
    
    # Create feature with valid link
    (features_dir / "REQ-F-TEST-001.yml").write_text("adrs: [ADR-001]")
    
    # Create feature with broken link
    (features_dir / "REQ-F-TEST-002.yml").write_text("adrs: [ADR-999]")
    
    issues = verify_adr_links(tmp_path)
    
    assert len(issues) == 1
    assert "REQ-F-TEST-002.yml: Broken link to ADR-999" in issues[0]
