# BDD System Tests for AISDLC

This directory contains Behavior-Driven Development (BDD) test scenarios for validating the AI SDLC methodology implementation.

## Overview

These tests validate the **System Test stage (Stage 5)** of the AI SDLC methodology, ensuring that all components work correctly from a user's perspective using Given/When/Then scenarios.

## Test Structure

```
features/
├── README.md                     # This file
├── system-test/                  # BDD feature files
│   ├── commands.feature          # Slash command tests (REQ-F-CMD-001)
│   ├── plugin-system.feature     # Plugin system tests (REQ-F-PLUGIN-*)
│   ├── 7-stage-agents.feature    # Agent behavior tests (REQ-F-CMD-002)
│   └── requirement-traceability.feature  # Traceability tests (REQ-NFR-TRACE-*)
└── steps/                        # Step definitions
    ├── conftest.py               # Pytest fixtures and helpers
    └── command_steps.py          # Step implementations for commands
```

## Requirements Coverage

| Feature File | Requirements Validated |
|--------------|----------------------|
| commands.feature | REQ-F-CMD-001, REQ-F-TODO-003 |
| plugin-system.feature | REQ-F-PLUGIN-001, 002, 003, 004, REQ-F-HOOKS-001 |
| 7-stage-agents.feature | REQ-F-CMD-002 |
| requirement-traceability.feature | REQ-NFR-TRACE-001, 002 |

## Running Tests

### Prerequisites

Install pytest-bdd:

```bash
pip install pytest-bdd
```

### Run All BDD Tests

```bash
# From project root
pytest claude-code/tests/features/ -v

# With verbose output
pytest claude-code/tests/features/ -v --tb=short

# Specific feature file
pytest claude-code/tests/features/system-test/commands.feature -v
```

### Run Tests by Tag

```bash
# Run only command tests
pytest claude-code/tests/features/ -v -m "commands"

# Run only plugin tests
pytest claude-code/tests/features/ -v -m "plugins"

# Run only agent tests
pytest claude-code/tests/features/ -v -m "agents"

# Run only traceability tests
pytest claude-code/tests/features/ -v -m "traceability"

# Run error handling scenarios
pytest claude-code/tests/features/ -v -m "error-handling"
```

### Generate Reports

```bash
# HTML report
pytest claude-code/tests/features/ -v --html=report.html

# JUnit XML (for CI)
pytest claude-code/tests/features/ -v --junitxml=results.xml
```

## Feature File Format

Each feature file follows Gherkin syntax:

```gherkin
# Feature header with requirement traceability
# Validates: REQ-F-CMD-001

@system-test @commands @REQ-F-CMD-001
Feature: AISDLC Slash Commands
  As a developer using the AI SDLC methodology
  I want to use slash commands to manage my workflow
  So that I can track tasks, checkpoint progress, and create releases

  Background:
    Given the AISDLC methodology plugin is installed
    And a valid .ai-workspace directory exists

  @status @ST-001
  Scenario: Display status with empty workspace
    Given ACTIVE_TASKS.md has no tasks defined
    When I execute the /aisdlc-status command
    Then I should see the "AI SDLC Task Status" header
    And the active task count should be "0"
```

## Test Scenario Naming Convention

Each scenario has a unique ID following this pattern:

| Prefix | Meaning |
|--------|---------|
| ST-NNN | Status command scenarios |
| CP-NNN | Checkpoint command scenarios |
| CM-NNN | Commit command scenarios |
| FT-NNN | Finish task scenarios |
| RL-NNN | Release command scenarios |
| UP-NNN | Update command scenarios |
| HP-NNN | Help command scenarios |
| PL-NNN | Plugin installation scenarios |
| MK-NNN | Marketplace scenarios |
| FD-NNN | Federated loading scenarios |
| VS-NNN | Version management scenarios |
| HK-NNN | Hooks system scenarios |
| AG-XXX-NNN | Agent scenarios (XXX = agent type) |
| TR-NNN | Traceability scenarios |
| INT-NNN | Integration scenarios |

## Adding New Tests

### 1. Add Scenario to Feature File

```gherkin
@new-feature @NF-001
Scenario: New feature works correctly
  Given some precondition
  When I perform some action
  Then I should see expected result
```

### 2. Implement Step Definitions

```python
# In steps/new_feature_steps.py

from pytest_bdd import given, when, then, scenarios

scenarios('../system-test/new-feature.feature')

@given("some precondition")
def some_precondition(context):
    # Setup code
    pass

@when("I perform some action")
def perform_action(context):
    # Action code
    pass

@then("I should see expected result")
def verify_result(context):
    # Verification code
    assert True
```

### 3. Add Requirement Tags

Always include requirement traceability:

```gherkin
# Validates: REQ-F-NEW-001

@REQ-F-NEW-001
Scenario: ...
```

## Test Status

| Feature | Scenarios | Implemented | Status |
|---------|-----------|-------------|--------|
| commands.feature | 20 | 20 | COMPLETE |
| plugin-system.feature | 18 | 0 | STUBS |
| 7-stage-agents.feature | 22 | 0 | STUBS |
| requirement-traceability.feature | 20 | 0 | STUBS |

## Related Documentation

- [TCS Documents](../../docs/design/claude_aisdlc/tests/) - Test Case Specifications
- [pytest Tests](../commands/) - Unit tests for commands
- [AI SDLC Method](../../docs/ai_sdlc_method.md) - Section 8.0 System Test Stage

---

**Stage**: System Test (5)
**Methodology**: BDD (Given/When/Then)
**Implements**: REQ-F-TESTING-001
