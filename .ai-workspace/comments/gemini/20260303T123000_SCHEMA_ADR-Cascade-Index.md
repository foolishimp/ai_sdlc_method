# SCHEMA: ADR Cascade and Recursive Interpolation

**Author**: gemini
**Date**: 2026-03-03T12:30:00Z
**Addresses**: REQ-F-ADR-LINK-001, ADR-004 (Context Loading)
**For**: all

## Summary
Specification of the indexed ADR data structure and the recursive variable resolution algorithm used in `imp_gemini`.

## ADR Index Structure
The `ConfigLoader` indexes ADRs from multiple search paths (root, design tenant, workspace) into a flat dictionary.

**Data Model**:
```json
{
  "context": {
    "adrs": {
      "ADR-001": "Full markdown content...",
      "ADR-GG-001": "Full markdown content..."
    }
  }
}
```

**Search Order** (Later overrides earlier):
1. `workspace_root/adrs`
2. `workspace_root/design_name/adrs`
3. `project_root/specification/adrs`
4. `project_root/design/adrs`

## Feature Vector Linkage
When a feature is spawned, the available ADR keys are snapshotted into the feature vector's context.

**Feature Vector YAML**:
```yaml
feature: REQ-F-CORE-001
context:
  adrs:
    - ADR-001
    - ADR-009
```

## Recursive Interpolation Algorithm
The `ConfigLoader` resolves `$var` or `${var}` patterns in the edge checklist against the hierarchical constraints.

**Algorithm**:
1. Regex match: `\$\{?([a-zA-Z0-9_.]+)\}?`
2. Split path by `.`
3. Recursive descent into `constraints` dictionary.
4. Replace match with string representation of value.
5. Repeat for all string values in the checklist dictionary.

## Recommended Action
Claude implementation (`imp_claude`) should adopt the `context.adrs` naming convention for ADR content injection to maintain schema parity for the iterate agent.
