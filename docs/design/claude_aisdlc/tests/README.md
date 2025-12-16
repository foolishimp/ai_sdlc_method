# Test Case Specifications (TCS) Index

**Purpose**: Track all Test Case Specifications for the claude_aisdlc solution

**Solution**: claude_aisdlc (AISDLC methodology implementation for Claude Code)

---

## Overview

This directory contains Test Case Specifications (TCS) for system-level BDD tests that validate the AISDLC methodology implementation. Each TCS document describes test scenarios, acceptance criteria, and traceability to requirements.

**Test Methodology**: BDD (Behavior-Driven Development) using Given/When/Then scenarios

**Test Framework**: pytest-bdd

**Test Location**: `claude-code/tests/features/system-test/`

---

## Active Test Specifications

| ID | Component | Requirement | Status | Created | Updated |
|----|-----------|-------------|--------|---------|---------|
| TCS-012 | Context Snapshot | REQ-TOOL-012.0.1.0 | ✅ Implemented | 2025-12-16 | 2025-12-16 |

---

## TCS-012: Context Snapshot and Recovery

**Component**: `/aisdlc-snapshot-context` command

**Requirement**: REQ-TOOL-012.0.1.0 - Context Snapshot and Recovery

**Status**: ✅ Implemented

**Files**:
- **Specification**: [TCS-012-context-snapshot.md](./TCS-012-context-snapshot.md)
- **Feature File**: `claude-code/tests/features/system-test/context_snapshot.feature`
- **Step Definitions**: `claude-code/tests/features/steps/context_snapshot_steps.py`

**Test Scenarios**: 25 scenarios covering:
- Basic snapshot creation (SS-001 to SS-004)
- Task context gathering (SS-005)
- Git integration (SS-006, SS-025)
- Template variable substitution (SS-007)
- Error handling (SS-008, SS-009)
- Warning handling (SS-010, SS-011, SS-012)
- Recovery guidance (SS-013)
- Snapshot tracking (SS-014)
- Immutability (SS-015)
- Integration with checkpoint (SS-016)
- Conversation markers (SS-017, SS-018, SS-019)
- Recent finished tasks (SS-020)
- Metadata accuracy (SS-021)
- Archival (SS-022, SS-023)
- Success message (SS-024)
- Edge cases (long titles, special characters)
- Full workflow integration

**Coverage**:
- Functional: 100%
- Error Handling: 100%
- Integration: 100%
- Edge Cases: 90%

**Run Tests**:
```bash
# Run all context snapshot tests
pytest claude-code/tests/features/system-test/context_snapshot.feature -v

# Run specific scenario by tag
pytest -m snapshot_creation
pytest -m git-integration
pytest -m error-handling

# Run with coverage
pytest --cov=.ai-workspace claude-code/tests/features/
```

---

## Test Development Workflow

### 1. Create TCS Document FIRST (Mandatory)

Before writing any tests:

```bash
# Create TCS document at:
docs/design/claude_aisdlc/tests/TCS-XXX-{component}.md
```

**Required Sections**:
- Purpose
- Scope (in scope / out of scope)
- Test Scenarios (table with ID, scenario, input, output, priority)
- Test Data (sample inputs)
- Acceptance Criteria (Given/When/Then)
- Test Environment (setup/teardown)
- Validation Approach (manual + automated)
- Coverage Requirements
- Traceability (requirements, design docs, related tests)

### 2. Implement BDD Feature File

```bash
# Create feature file at:
claude-code/tests/features/system-test/{component}.feature
```

**Feature File Format**:
```gherkin
# Feature: Component Name
# Validates: REQ-ID
# TCS Reference: TCS-XXX
# Stage: System Test (Stage 5)

@system-test @component-tag @REQ-ID
Feature: Component Description
  As a [role]
  I want to [action]
  So that [benefit]

  Background:
    Given [common setup]

  @tag @scenario-id
  Scenario: Scenario description
    Given [precondition]
    When [action]
    Then [expected outcome]
```

### 3. Implement Step Definitions

```bash
# Create step definitions at:
claude-code/tests/features/steps/{component}_steps.py
```

**Step Definition Format**:
```python
#!/usr/bin/env python3
"""
BDD Step Definitions for Component

# Validates: REQ-ID
# Validates: TCS-XXX
"""

from pytest_bdd import scenario, given, when, then, parsers

@scenario('../system-test/{component}.feature', 'Scenario name')
def test_scenario_name():
    """Scenario-ID: Description."""
    pass

@given("precondition text")
def given_step(test_context):
    """Setup step."""
    # Implementation
    pass

@when("action text")
def when_step(test_context):
    """Action step."""
    # Implementation
    pass

@then("expected outcome")
def then_step(test_context):
    """Assertion step."""
    # Implementation
    pass
```

### 4. Update Fixtures (if needed)

Add helper functions and fixtures to `conftest.py`:
```python
def helper_function(param: Type) -> ReturnType:
    """Helper description."""
    # Implementation
    pass
```

### 5. Run Tests

```bash
# Run all tests
pytest claude-code/tests/features/ -v

# Run specific feature
pytest claude-code/tests/features/system-test/{component}.feature -v

# Run with specific tags
pytest -m @tag-name

# Run with coverage
pytest --cov=.ai-workspace claude-code/tests/features/
```

### 6. Update TCS Status

After tests pass:
- Update TCS document: **Status**: 📋 Specified → **Status**: ✅ Implemented
- Add test execution results
- Update this README with TCS entry

---

## Test Organization

### Directory Structure

```
claude-code/tests/
├── features/
│   ├── system-test/           # BDD feature files
│   │   ├── commands.feature
│   │   ├── context_snapshot.feature
│   │   └── ...
│   ├── steps/                 # Step definitions
│   │   ├── conftest.py        # Fixtures and helpers
│   │   ├── test_commands.py
│   │   ├── context_snapshot_steps.py
│   │   └── ...
│   └── pytest.ini             # Pytest configuration
├── sdk/                       # SDK tests
├── commands/                  # Command tests
└── specs/                     # Test specifications

docs/design/claude_aisdlc/tests/
├── README.md                  # This file
├── TCS-012-context-snapshot.md
└── ...
```

### Naming Conventions

**TCS Files**: `TCS-{NNN}-{component-name}.md`
- Example: `TCS-012-context-snapshot.md`

**Feature Files**: `{component-name}.feature`
- Example: `context_snapshot.feature`

**Step Files**: `{component-name}_steps.py`
- Example: `context_snapshot_steps.py`

**Scenario IDs**: `{PREFIX}-{NNN}`
- Example: `SS-001` (Snapshot Scenario 001)

**Test Functions**: `test_{component}_{scenario}`
- Example: `test_snapshot_basic_creation()`

---

## Test Tags

Use tags for organizing and filtering tests:

| Tag | Purpose | Example |
|-----|---------|---------|
| `@system-test` | All system tests | Marks Stage 5 tests |
| `@REQ-{ID}` | Requirement tracing | `@REQ-TOOL-012` |
| `@component-tag` | Component group | `@context-snapshot` |
| `@scenario-id` | Specific scenario | `@SS-001` |
| `@error-handling` | Error cases | Error validation |
| `@integration` | Integration tests | Multi-component |
| `@edge-cases` | Edge case tests | Boundary conditions |

**Run by tag**:
```bash
pytest -m system-test          # All system tests
pytest -m REQ-TOOL-012         # All tests for requirement
pytest -m context-snapshot     # All snapshot tests
pytest -m error-handling       # All error tests
```

---

## Coverage Requirements

**Minimum Coverage**: 95%

**Coverage Types**:
1. **Functional Coverage**: All features implemented
2. **Error Handling**: All error conditions tested
3. **Edge Cases**: Boundary conditions validated
4. **Integration**: Cross-component interactions
5. **Regression**: Existing functionality preserved

**Measure Coverage**:
```bash
# Generate coverage report
pytest --cov=.ai-workspace --cov-report=html claude-code/tests/features/

# View report
open htmlcov/index.html
```

---

## Traceability

### Requirements → Tests

Every test MUST trace back to a requirement:

| Requirement | TCS | Feature File | Status |
|-------------|-----|--------------|--------|
| REQ-TOOL-012.0.1.0 | TCS-012 | context_snapshot.feature | ✅ |

### Tests → Requirements

Use requirement tags in feature files:
```gherkin
@REQ-TOOL-012
Feature: Context Snapshot and Recovery
```

And in step definitions:
```python
# Validates: REQ-TOOL-012.0.1.0
```

---

## Quality Gates

Before marking TCS as "Implemented":

- [ ] TCS document exists and is complete
- [ ] TCS registered in this README
- [ ] Feature file created with BDD scenarios
- [ ] Step definitions implemented
- [ ] All scenarios passing
- [ ] ≥95% requirement coverage
- [ ] Test code references TCS scenario IDs
- [ ] Error handling validated
- [ ] Edge cases covered
- [ ] Integration tested
- [ ] Documentation updated

---

## Best Practices

### 1. Test Independence
- Each scenario should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 2. Descriptive Scenarios
- Use clear, business-readable language
- Follow Given/When/Then pattern strictly
- Include context in scenario names

### 3. Data Tables
Use data tables for multiple examples:
```gherkin
Given ACTIVE_TASKS.md contains the following tasks:
  | ID | Title    | Status      |
  | 1  | Task One | In Progress |
  | 2  | Task Two | Pending     |
```

### 4. Fixtures and Helpers
- Reuse fixtures in conftest.py
- Create helper functions for common operations
- Document fixture purposes

### 5. Error Testing
- Test both happy path and error conditions
- Verify error messages are helpful
- Test recovery from errors

### 6. Comments and Traceability
```python
# Validates: TCS-012
# Scenario: SS-001

@scenario('../system-test/context_snapshot.feature', 'Create basic snapshot')
def test_snapshot_basic_creation():
    """SS-001: Basic snapshot creation."""
    pass
```

---

## Future Test Specifications

**Planned TCS**:
- TCS-001: Status Command (existing in commands.feature)
- TCS-002: Checkpoint Command (existing in commands.feature)
- TCS-003: Commit Command (existing in commands.feature)
- TCS-004: Finish Task Command (existing in commands.feature)
- TCS-005: Release Command (existing in commands.feature)
- TCS-006: Update Command (existing in commands.feature)
- TCS-007: Help Command (existing in commands.feature)
- TCS-013: Context Restoration
- TCS-014: Snapshot Archival
- TCS-015: Snapshot Search

---

## Contributing

When adding new tests:

1. **Create TCS FIRST** - Never write tests without specification
2. **Follow BDD format** - Given/When/Then scenarios
3. **Tag appropriately** - Use requirement and component tags
4. **Update this README** - Add TCS to the index
5. **Verify traceability** - Link to requirements
6. **Run full test suite** - Ensure no regressions

---

## Questions?

- **BDD Syntax**: See existing feature files for examples
- **Fixtures**: Check `conftest.py` for available fixtures
- **Test Patterns**: Review `test_commands.py` for patterns
- **TCS Format**: Use TCS-012 as template

---

**Last Updated**: 2025-12-16

**Maintained By**: System Test Agent
