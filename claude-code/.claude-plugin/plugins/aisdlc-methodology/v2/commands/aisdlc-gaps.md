# /aisdlc-gaps - Test Gap Analysis

Analyse REQ key coverage across the asset graph and identify uncovered trajectories.

<!-- Implements: REQ-TOOL-005 (Test Gap Analysis) -->

## Usage

```
/aisdlc-gaps [--scope code|tests|design|all]
```

| Option | Description |
|--------|-------------|
| `--scope` | Focus analysis (default: all) |

## Instructions

### Step 1: Gather REQ Keys

Collect all REQ keys from:
- Requirements documents (`docs/requirements/`)
- Feature vector files (`.ai-workspace/features/`)

### Step 2: Scan Assets

For each REQ key, check presence in:
- **Design**: component references
- **Code**: `# Implements: REQ-*` tags
- **Unit Tests**: `# Validates: REQ-*` tags
- **Integration Tests**: `# Validates: REQ-*` tags
- **UAT Tests**: `# Validates: REQ-*` tags

### Step 3: Report Coverage

```
REQ KEY COVERAGE ANALYSIS
=========================

| REQ Key | Design | Code | Unit Tests | Integration | UAT |
|---------|--------|------|------------|-------------|-----|
| REQ-F-AUTH-001 | Y | Y | Y | Y | N |
| REQ-F-AUTH-002 | Y | Y | N | N | N |
| REQ-F-DB-001 | Y | Y | Y | N | N |
| REQ-NFR-PERF-001 | Y | N | N | N | N |

Summary:
  Total REQ keys:    15
  Full coverage:      3 (20%)
  Partial coverage:   8 (53%)
  No coverage:        4 (27%)

CRITICAL GAPS:
  - REQ-F-AUTH-002: No tests at all
  - REQ-NFR-PERF-001: Design exists but no implementation
  - REQ-F-AUTH-001: Missing UAT test

RECOMMENDED NEXT ACTIONS:
  1. /aisdlc-iterate --edge "code↔unit_tests" --feature "REQ-F-AUTH-002"
  2. /aisdlc-iterate --edge "design→code" --feature "REQ-NFR-PERF-001"
  3. /aisdlc-iterate --edge "design→uat_tests" --feature "REQ-F-AUTH-001"
```
