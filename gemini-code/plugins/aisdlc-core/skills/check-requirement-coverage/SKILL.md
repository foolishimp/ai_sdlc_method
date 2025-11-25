---
name: check-requirement-coverage
description: Homeostatic sensor detecting requirements without implementation or test coverage. Scans for REQ-* keys in requirements docs and checks if they have corresponding code and tests. Use to find coverage gaps.
allowed-tools: [Read, Grep, Glob]
---

# check-requirement-coverage

**Skill Type**: Sensor (Homeostasis)
**Purpose**: Detect requirements without implementation or test coverage
**Prerequisites**: Requirements exist in documentation

---

## Agent Instructions

You are a **Sensor** in the AI SDLC's homeostasis system. Your primary function is to **detect deviations** from the desired state of full requirement coverage.

**Desired State**: `coverage = 100%` (all requirements have corresponding implementation and tests)

Your goal is to meticulously **find any requirements that lack code or test coverage** and clearly signal this deviation.

---

## Workflow

### Step 1: Find All Requirements

**Search for REQ-* keys** in the requirements documentation:

```bash
# Find all requirement files in the docs
find docs/requirements -name "*.md" -type f

# Extract all unique REQ-* keys from the documentation
grep -rho "REQ-[A-Z-]*-[0-9]*" docs/requirements/ | sort -u
```

### Step 2: Check Implementation Coverage

For each unique REQ-* key, search for its implementation in the `src` directory:

```bash
# Check if a specific requirement has a corresponding implementation
grep -rn "# Implements: <REQ-ID>" src/
```

**Coverage Criteria**:
-   ✅ **Covered**: At least one file in the `src/` directory contains the tag `# Implements: {REQ-KEY}`.
-   ❌ **Not Covered**: No files in `src/` reference the requirement key.

### Step 3: Check Test Coverage

For each unique REQ-* key, search for its test validation in the `tests` and `features` directories:

```bash
# Check if a requirement has corresponding tests
grep -rn "# Validates: <REQ-ID>" tests/

# Also check BDD feature files for validation
grep -rn "# Validates: <REQ-ID>" features/
```

**Coverage Criteria**:
-   ✅ **Covered**: At least one file in `tests/` or `features/` contains the tag `# Validates: {REQ-KEY}`.
-   ❌ **Not Covered**: No test files reference the requirement key.

### Step 4: Calculate and Report Coverage

Calculate the coverage percentages and report the findings, highlighting any gaps.

**Formulas**:
```python
implementation_coverage = (requirements_with_code / total_requirements) * 100
test_coverage = (requirements_with_tests / total_requirements) * 100
full_coverage = (requirements_with_both_code_and_tests / total_requirements) * 100
```

## Output Format

When you detect coverage gaps, provide a clear and actionable report:

```
[COVERAGE SENSOR - DEVIATION DETECTED]

Requirements Scanned: 42

Coverage Summary:
  Implementation: 36/42 (86%) ✅ PASS (≥80%)
  Tests: 32/42 (76%) ❌ FAIL (target: ≥80%)
  Full Coverage: 30/42 (71%) ❌ FAIL (target: ≥80%)

Homeostasis Deviation: Test coverage is below the 80% threshold.

Coverage Gaps Identified:

❌ No Implementation (6 requirements):
  1. REQ-F-PROFILE-001 - User profile editing
  2. REQ-F-PROFILE-002 - Avatar upload
  ...

⚠️ No Tests (10 requirements):
  1. <REQ-ID> - Payment processing (Code: src/payments/payment.py:45)
  2. REQ-F-CART-001 - Shopping cart (Code: src/cart/cart.py:23)
  ...

Recommended Actions:
1. Invoke the 'generate-missing-tests' skill for the 10 requirements that are missing tests.
2. Implement the 6 requirements that have no code using the 'tdd-workflow' skill.
```

---

## Homeostasis Behavior

-   **When deviation is detected**: Report the coverage gaps and recommend invoking the appropriate actuator skills (e.g., `generate-missing-tests`).
-   **When homeostasis is achieved**: Report that the system is stable and coverage targets are met.

---

## Configuration

This skill respects the configuration in `.gemini/plugins.yml`:

```yaml
plugins:
  - name: "@aisdlc/aisdlc-core"
    config:
      coverage:
        minimum_percentage: 80
        require_implementation: true
        require_tests: true
        exclude_patterns:
          - "REQ-DATA-*"
```