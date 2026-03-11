# Design: ADR Link Verification (REQ-F-ADR-LINK-001)

**Implements**: REQ-F-ADR-LINK-001

## 1. Architectural Strategy
The verification will be implemented as a standalone stateless function `verify_adr_links(project_root: Path)` that inspects the workspace file system and cross-references feature vectors against the ADR directory.

## 2. Component Design
- **`code.adr_link_verification.verify_adr_links`**: 
  - Iterates through `.ai-workspace/features/active/*.yml`.
  - Uses regular expressions (`r"(ADR(?:-[A-Z]+)?-\d{3}[A-Za-z0-9-]*)"`) to find ADR citations within the raw text of the feature files.
  - Compares found citations against the set of known ADR files in `design/adrs`.
  - Returns a list of strings detailing any broken links.

## 3. Interfaces
- `verify_adr_links(project_root: Path) -> List[str]`

## 4. Test Strategy
- Provide a temporary workspace structure mimicking `.ai-workspace` and `design/adrs`.
- Create mock feature files with both valid and invalid ADR references.
- Assert that the function correctly identifies the invalid reference and ignores the valid one.
