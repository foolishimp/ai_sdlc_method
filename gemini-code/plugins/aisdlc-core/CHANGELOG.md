# Changelog - aisdlc-core

All notable changes to the `aisdlc-core` plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.0] - 2025-11-20

### Added

**Foundation Skills** (3/3 complete):
- `requirement-traceability` - REQ-* key pattern definitions and validation
  - Functional requirements (REQ-F-*)
  - Non-functional requirements (REQ-NFR-*)
  - Data quality requirements (REQ-DATA-*)
  - Business rules (REQ-BR-*)
  - Subordinate keys (BR-*, C-*, F-*)
  - Validation functions for key format
  - Forward/backward traceability operations
  - Traceability matrix structure

- `check-requirement-coverage` - Homeostatic sensor detecting coverage gaps
  - Scans requirements documentation for all REQ-* keys
  - Checks implementation coverage (src/ has "# Implements:")
  - Checks test coverage (tests/ has "# Validates:")
  - Calculates coverage percentages
  - Reports gaps and recommendations
  - Homeostasis deviation signaling

- `propagate-req-keys` - Homeostatic actuator tagging artifacts
  - Tags implementation files with "# Implements: REQ-*"
  - Tags test files with "# Validates: REQ-*"
  - Tags BDD feature files
  - Supports multiple key tagging
  - Includes BR-*, C-*, F-* tagging
  - Bulk tagging operations
  - Verification of tags added

**Plugin Infrastructure**:
- `.claude-plugin/plugin.json` - Complete plugin manifest
  - Capabilities: traceability, coverage detection, key propagation
  - Configuration: REQ patterns, coverage thresholds, tag formats
  - No dependencies (foundation plugin)

- `README.md` - Comprehensive documentation
  - Overview of all 3 skills
  - Homeostasis architecture explanation
  - Usage examples
  - Configuration options
  - Integration with other plugins

- `CHANGELOG.md` - Version history (this file)

### Configuration Options

**REQ-* Key Patterns**:
- Customizable patterns for REQ-F-*, REQ-NFR-*, REQ-DATA-*, REQ-BR-*
- Validation regex for each type
- Domain and ID format rules

**Coverage Detection**:
- Minimum coverage percentage (default: 80%)
- Require implementation flag
- Require tests flag
- Auto-detection on save
- Exclude patterns for special requirements

**Key Propagation**:
- Auto-propagate on commit
- Tag format customization
- Test tag format customization
- Business rule inclusion
- Tag placement options (above, inline, block)

### Homeostasis Architecture

**Sensor-Actuator Loop**:
1. **Sensor** (`check-requirement-coverage`) detects requirements without tags
2. **Signal** sent: "Missing tags for REQ-*"
3. **Actuator** (`propagate-req-keys`) adds tags
4. **Sensor** re-checks: Coverage improved
5. **Homeostasis achieved**: coverage >= 80%

### Status

**Completion**: 100% (3/3 skills)

**Skills Complete**:
- ✅ requirement-traceability (495 lines)
- ✅ check-requirement-coverage (391 lines)
- ✅ propagate-req-keys (387 lines)

**Total**: 1,273 lines of skill documentation

---

## [Unreleased]

### To Add (v3.1.0)

**Advanced Traceability**:
- Requirement dependency graphs (REQ-A depends on REQ-B)
- Coverage trend analysis (coverage over time)
- Visual traceability diagrams
- Requirement impact analysis (what breaks if REQ changes)

**Enhanced Sensors**:
- Detect orphaned code (code without REQ-* tags)
- Detect duplicate requirements
- Detect conflicting requirements

**Enhanced Actuators**:
- Auto-update tags on file moves/renames
- Batch tag propagation for entire codebase
- Tag migration (update old tags to new format)

---

## Version History Summary

| Version | Date | Skills | Status |
|---------|------|--------|--------|
| 3.0.0 | 2025-11-20 | 3/3 | ✅ Initial release (foundation complete) |
| 3.1.0 | TBD | TBD | Advanced traceability features |

---

## Integration

This plugin is **required** by:
- `@aisdlc/code-skills` (TDD, BDD, generation workflows)
- `@aisdlc/requirements-skills` (requirement extraction)
- `@aisdlc/testing-skills` (coverage validation)
- `@aisdlc/runtime-skills` (telemetry tagging)
- All plugin bundles (startup, enterprise, qa, datascience)

**Install aisdlc-core first** before other AI SDLC plugins.

---

**"Excellence or nothing"** 🔥
