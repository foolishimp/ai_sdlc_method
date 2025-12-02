# TCS-010: Test Case Specification Creation Skill

**Status**: ✅ Implemented
**Date**: 2025-11-27
**Requirements**: REQ-NFR-TRACE-001, REQ-NFR-QUALITY-001
**ADR Reference**: [ADR-002](../adrs/ADR-002-commands-for-workflow-integration.md)
**Implementation**: `claude-code/plugins/testing-skills/skills/create-test-specification/SKILL.md`

---

## Purpose

Validate that the TCS creation skill correctly generates test case specification documents with proper structure, naming conventions, requirement traceability, and registry integration. This is a meta-level test - testing the test specification process itself.

---

## Preconditions

- TCS skill exists at `claude-code/plugins/testing-skills/skills/create-test-specification/SKILL.md`
- Test registry exists at `docs/design/claude_aisdlc/tests/README.md`
- At least one existing TCS document for reference (e.g., TCS-001)
- Requirements exist in `docs/requirements/`

---

## Test Scenarios

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| TCS-001 | Valid TCS creation | Complete TCS data | TCS document with all required sections | High |
| TCS-002 | TCS naming validation | TCS number and slug | Validates TCS-XXX-slug.md pattern | High |
| TCS-003 | Required sections present | Generated TCS | All mandatory sections exist | High |
| TCS-004 | Requirement traceability | TCS with REQ references | Traceability matrix created | High |
| TCS-005 | Registry entry creation | New TCS | Entry added to README.md | High |
| TCS-006 | Status field validation | TCS document | Status is one of: Specified, Implemented, Deprecated | Medium |
| TCS-007 | Test scenario ID format | Test scenarios table | IDs follow XXX-001 pattern | Medium |
| TCS-008 | Invalid TCS number | Duplicate or malformed number | Error with clear message | Medium |
| TCS-009 | Missing requirement | TCS without REQ reference | Warning or error raised | Low |
| TCS-010 | Template compliance | Generated TCS | Matches skill template structure | High |

---

## Validation Criteria

### TCS Document Structure
- [ ] Header contains: Title, Status, Date, Requirements, ADR Reference, Implementation
- [ ] Status is one of: Specified, Implemented, Deprecated
- [ ] Date follows YYYY-MM-DD format
- [ ] Requirements field contains valid REQ-* identifiers
- [ ] All required sections present: Purpose, Preconditions, Test Scenarios, Validation Criteria, Test Implementation, Requirement Traceability, Notes

### TCS Naming Convention
- [ ] Filename matches pattern: `TCS-XXX-slug.md`
- [ ] XXX is a zero-padded 3-digit number (e.g., 010, 011)
- [ ] Slug is kebab-case and descriptive
- [ ] Number is sequential (no gaps unless deprecated)

### Test Scenarios Table
- [ ] Table has columns: ID, Scenario, Input State, Expected Output, Priority
- [ ] Scenario IDs follow pattern: XXX-001, XXX-002, etc.
- [ ] Priority is one of: High, Medium, Low
- [ ] At least one scenario exists

### Requirement Traceability
- [ ] Traceability matrix table exists
- [ ] All requirements from header appear in matrix
- [ ] Each requirement linked to at least one test scenario
- [ ] Matrix has columns: Requirement, How Validated

### Registry Integration
- [ ] TCS entry added to `docs/design/claude_aisdlc/tests/README.md`
- [ ] Entry contains: ID (linked), Title, Requirements, Status
- [ ] Entry appears in Test Case Index table
- [ ] Test Case Summary counts updated

---

## Expected TCS Template Structure

```markdown
# TCS-XXX: {Title}

**Status**: Specified | Implemented | Deprecated
**Date**: YYYY-MM-DD
**Requirements**: REQ-F-*, REQ-NFR-*
**ADR Reference**: [ADR-XXX](link)
**Implementation**: path/to/file

---

## Purpose
What this test case validates.

---

## Preconditions
Required state before test execution.

---

## Test Scenarios

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| XXX-001 | ... | ... | ... | High |

---

## Validation Criteria
- [ ] Criterion 1
- [ ] Criterion 2

---

## Test Implementation

**File**: path/to/test_file.py
**Class**: TestClassName
**Tests**: N

```python
class TestClassName:
    def test_scenario_xxx_001(self):
        """XXX-001: Scenario description."""
        ...
```

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-F-XXX-001 | Test scenario XXX-001 |

---

## Notes
Additional context.
```

---

## Test Implementation

**File**: `claude-code/tests/skills/test_tcs_creation.py`
**Class**: `TestTCSCreation`
**Tests**: 10

```python
# Validates: TCS-010

class TestTCSCreation:
    """Test the TCS creation skill workflow."""

    def test_valid_tcs_creation(self):
        """TCS-001: Create valid TCS document with all sections."""

    def test_tcs_naming_validation(self):
        """TCS-002: Validate TCS-XXX-slug.md naming pattern."""

    def test_required_sections_present(self):
        """TCS-003: All mandatory sections exist in TCS."""

    def test_requirement_traceability(self):
        """TCS-004: Traceability matrix correctly links requirements."""

    def test_registry_entry_creation(self):
        """TCS-005: Entry added to README.md registry."""

    def test_status_field_validation(self):
        """TCS-006: Status field contains valid value."""

    def test_scenario_id_format(self):
        """TCS-007: Test scenario IDs follow XXX-001 pattern."""

    def test_invalid_tcs_number(self):
        """TCS-008: Error on duplicate or malformed TCS number."""

    def test_missing_requirement_warning(self):
        """TCS-009: Warning when TCS has no REQ reference."""

    def test_template_compliance(self):
        """TCS-010: Generated TCS matches skill template."""
```

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-NFR-TRACE-001 | TCS-004: Traceability matrix validation |
| REQ-NFR-QUALITY-001 | TCS-003: Required sections check |

---

## Notes

### Meta-Testing Approach

This TCS is unique because it tests the TCS creation process itself - a meta-level validation. The tests should:

1. **Validate Structure**: Parse TCS markdown and verify all required sections
2. **Check Naming**: Regex pattern matching for TCS-XXX-slug.md
3. **Verify Traceability**: Parse traceability matrix and cross-reference with requirements
4. **Test Registry**: Verify README.md updates when new TCS created
5. **Template Compliance**: Compare generated TCS against skill template

### Test Data Strategy

Tests should use:
- **Golden Master**: TCS-001 as a reference example
- **Generated TCS**: Create test TCS documents programmatically
- **Validation Rules**: Defined in skill specification
- **Negative Cases**: Invalid numbers, missing sections, malformed tables

### Automation Potential

The TCS validation logic could be extracted into:
- **Pre-commit hook**: Validate TCS structure before commit
- **CI/CD check**: Ensure all TCS documents are valid
- **Coverage tool**: Generate traceability reports

---

## Test Results

All 19 tests passing (2 test classes):

**TestTCSCreation** (15 tests):
- TCS-001: Valid TCS creation ✅
- TCS-002: TCS naming validation ✅
- TCS-003: Required sections present ✅
- TCS-004: Requirement traceability ✅
- TCS-005: Registry entry creation ✅
- TCS-006: Status field validation ✅
- TCS-007: Scenario ID format ✅
- TCS-008: Invalid TCS number ✅
- TCS-009: Missing requirement warning ✅
- TCS-010: Template compliance ✅
- Additional validation tests (5) ✅

**TestTCSMetaValidation** (4 tests):
- Sequential numbering ✅
- All TCS have implementation ✅
- All TCS have requirements ✅
- Registry completeness ✅

### Issues Found & Resolved

**Issue**: Initial test failure in `test_requirement_traceability`
- **Cause**: TCS-010 contains template examples with placeholder REQ-F-XXX-001 identifiers
- **Fix**: Updated test to filter out placeholder requirements and search only in actual content section
- **Result**: All tests passing ✅

---

**Last Updated**: 2025-11-27
**Next Review**: After implementing TCS validation tests
