# Skill: Create Test Case Specification (TCS)

**Stage**: 5 - System Test
**Purpose**: Generate TCS documents with full requirement traceability

<!-- Implements: REQ-NFR-TRACE-001 (Requirement Traceability) -->
<!-- Implements: REQ-NFR-QUALITY-001 (Code Quality Standards) -->

---

## When to Use

Use this skill when:
- Starting System Test stage for a component
- Adding tests for new functionality
- Validating requirement coverage

---

## TCS Pattern

Test Case Specifications follow the same traceability pattern as ADRs:

```
Requirements (REQ-*)
    ↓
Design (ADRs)
    ↓
Implementation
    ↓
Test Cases (TCS-*) ← This skill creates these
    ↓
Test Implementation (pytest, etc.)
```

---

## TCS Document Structure

Create TCS documents at: `docs/design/<solution>/tests/TCS-XXX-<slug>.md`

```markdown
# TCS-XXX: {Component/Feature Name}

**Status**: Specified | Implemented | Deprecated
**Date**: YYYY-MM-DD
**Requirements**: REQ-F-*, REQ-NFR-*
**ADR Reference**: ADR-XXX (if applicable)
**Implementation**: Path to implementation file

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
| XXX-001 | ... | ... | ... | High/Medium/Low |
| XXX-002 | ... | ... | ... | ... |

---

## Validation Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

---

## Test Implementation

**File**: `path/to/test_file.py`
**Class**: `TestClassName`
**Tests**: N

```python
class TestClassName:
    def test_scenario_001(self):
        """XXX-001: Scenario description."""
        ...
```

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-F-XXX-001 | Test scenario XXX-001 |
| REQ-NFR-XXX-001 | Test scenario XXX-002 |

---

## Notes
Additional context or considerations.
```

---

## Step-by-Step Process

### 1. Identify Requirements to Test

```bash
# List requirements for the component
grep -r "REQ-" docs/requirements/ | grep "<component>"
```

### 2. Create TCS Document

```bash
# Determine next TCS number
ls docs/design/<solution>/tests/TCS-*.md | tail -1

# Create TCS file
TCS_NUM="010"  # Next available
touch docs/design/<solution>/tests/TCS-${TCS_NUM}-<component>.md
```

### 3. Define Test Scenarios

For each requirement:
- Create at least one test scenario
- Include positive and negative cases
- Define clear input/output
- Assign priority (High for core functionality)

### 4. Create Test Registry Entry

Add to `docs/design/<solution>/tests/README.md`:

```markdown
| [TCS-XXX](TCS-XXX-<slug>.md) | Component Name | REQ-F-*, REQ-NFR-* | Status |
```

### 5. Implement Tests

Create test file referencing TCS scenarios:

```python
# Validates: TCS-XXX

class TestComponent:
    def test_scenario_xxx_001(self):
        """XXX-001: <scenario description>"""
        # Test implementation
```

---

## TCS Naming Convention

| Pattern | Example | Use For |
|---------|---------|---------|
| TCS-0XX-command-* | TCS-001-command-status | Slash commands |
| TCS-0XX-hook-* | TCS-008-hooks-lifecycle | Lifecycle hooks |
| TCS-0XX-installer-* | TCS-009-installer-setup | Installers |
| TCS-0XX-skill-* | TCS-010-skill-tcs | Skills |
| TCS-0XX-agent-* | TCS-011-agent-system-test | Agents |

---

## Traceability Validation

After creating TCS, validate:

```bash
# Check all requirements have test coverage
grep -h "REQ-" docs/requirements/*.md | sort -u > /tmp/all_reqs.txt
grep -rh "REQ-" docs/design/*/tests/TCS-*.md | sort -u > /tmp/tested_reqs.txt
diff /tmp/all_reqs.txt /tmp/tested_reqs.txt
```

---

## Example: Command TCS

```markdown
# TCS-001: /aisdlc-status Command

**Status**: ✅ Implemented
**Date**: 2025-11-27
**Requirements**: REQ-F-CMD-001, REQ-F-TODO-003
**ADR Reference**: ADR-002
**Implementation**: claude-code/plugins/aisdlc-methodology/commands/aisdlc-status.md

---

## Purpose
Validate that /aisdlc-status displays correct task queue status.

---

## Test Scenarios

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| ST-001 | Empty workspace | No tasks | "0 Active Tasks" | High |
| ST-002 | With tasks | 2 tasks | Lists both tasks | High |

---

## Validation Criteria
- [ ] Output contains "AI SDLC Task Status" header
- [ ] Active task count matches file

---

## Test Implementation

**File**: `claude-code/tests/commands/test_commands.py`
**Class**: `TestStatusCommand`
**Tests**: 4

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-F-CMD-001 | Command executes |
| REQ-F-TODO-003 | TODO list displayed |
```

---

## Integration with System Test Agent

The System Test Agent should:

1. **Before writing tests**: Create TCS document
2. **During test creation**: Reference TCS scenario IDs
3. **After tests pass**: Update TCS status to "Implemented"
4. **On failure**: Update TCS with failure notes

---

## Quality Gates

- [ ] TCS document exists before test implementation
- [ ] All requirements have TCS coverage
- [ ] Test code references TCS scenario IDs
- [ ] TCS README updated with new entry
- [ ] Traceability validation passes
