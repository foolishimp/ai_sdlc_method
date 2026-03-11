# Feature Decomposition: REQ-F-ADR-LINK-001

**Implements**: REQ-F-ADR-LINK-001

## Overview
This feature ensures traceability from implementation features back to Architectural Decision Records (ADRs). It provides a mechanism to verify that any ADR referenced in a feature vector actually exists within the project's design documentation.

## Required Capabilities
1. **Feature Scanning**: The system must be able to scan active feature vectors in the `.ai-workspace/features/active` directory.
2. **ADR Link Extraction**: The system must parse feature definitions to extract references to ADRs (e.g., matching the pattern `ADR-XXX`).
3. **ADR Verification**: The system must check the `design/adrs` directory to confirm the existence of a corresponding markdown file for each extracted ADR reference.
4. **Issue Reporting**: The system must return a list of broken links, specifying the feature file and the missing ADR reference.
