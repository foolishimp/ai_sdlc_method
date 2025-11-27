# testing-skills Plugin

<!-- Implements: REQ-F-TESTING-002 (Test generation) -->
<!-- Implements: REQ-F-TESTING-001 (Test coverage validation) -->

**Test Coverage Validation and Auto-Generation for AI SDLC v3.0**

Version: 1.0.0

---

## Overview

The `testing-skills` plugin provides homeostatic test coverage management - sensors detect coverage gaps, actuators generate missing tests, and reporters provide visibility into testing status with requirement traceability.

**Homeostasis Architecture**: Coverage below threshold → Sensor detects → Actuator generates tests → Coverage restored

---

## Capabilities

### 1. Coverage Validation (Sensor)

**Skill**: `validate-test-coverage`

**Purpose**: Homeostatic sensor detecting test coverage gaps

**Validates**:
- Overall coverage percentage (>= 80%)
- Coverage per requirement (REQ-*)
- Critical path coverage (P0 = 100%)
- Requirements without tests

**Workflow**:
```
Run coverage tool → Parse coverage data → Calculate per-REQ coverage
  → Detect gaps → Signal deviation if < 80%
```

---

### 2. Test Generation (Actuator)

**Skill**: `generate-missing-tests`

**Purpose**: Homeostatic actuator auto-generating missing tests

**Generates**:
- Happy path tests (valid inputs)
- Edge case tests (zero, null, boundaries)
- Error case tests (invalid inputs)
- Boundary tests (min/max limits)

**Workflow**:
```
Receive coverage gaps → Analyze uncovered code → Generate test cases
  → Write test file → Run tests → Verify coverage improved
```

**Generation Strategies**:
- From business rules (BR-*) → Generate validation tests
- From uncovered lines → Generate tests covering those lines
- From code structure (if/else, try/except) → Generate branch tests

---

### 3. Integration Testing

**Skill**: `run-integration-tests`

**Purpose**: Execute integration tests validating system behavior

**Runs**:
- BDD scenarios (Given/When/Then)
- API integration tests
- Database integration tests
- End-to-end tests

**Workflow**:
```
Discover integration tests → Run BDD scenarios → Run API tests
  → Run database tests → Run E2E tests → Aggregate results
  → Map to requirements
```

---

### 4. Coverage Reporting

**Skill**: `create-coverage-report`

**Purpose**: Generate comprehensive coverage report with REQ-* mapping

**Report Includes**:
- Executive summary (overall stats)
- Coverage per requirement (REQ-*)
- Coverage gaps and recommendations
- Coverage by file
- Test statistics (unit, integration, E2E)
- Coverage trends (historical)

**Formats**:
- Console (quick summary)
- HTML (full detail with navigation)
- JSON (machine-readable for CI/CD)
- Markdown (documentation)

---

### 5. Test Case Specification (TCS)

**Skill**: `create-test-specification`

**Purpose**: Create TCS documents with full requirement traceability

**Creates**:
- TCS document at `docs/design/<solution>/tests/TCS-XXX-<component>.md`
- Test registry entry in `README.md`
- Requirement traceability matrix

**TCS Pattern**:
```
Requirements (REQ-*)
    ↓
Design (ADRs)
    ↓
Implementation
    ↓
Test Specs (TCS-*) ← This skill creates these
    ↓
Test Implementation (pytest, etc.)
```

**Workflow**:
```
1. Identify requirements to test
2. Create TCS document with scenarios
3. Register in tests/README.md
4. Implement tests referencing TCS IDs
5. Update TCS status to "Implemented"
```

**Usage**: Required by System Test Agent BEFORE writing any tests.

---

## Homeostasis Loop

**Sensor → Actuator → Sensor**:

```
1. validate-test-coverage (Sensor):
   → Detects: <REQ-ID> at 72.1% (below 80%)
   → Signal: "Coverage gap detected"
   ↓

2. generate-missing-tests (Actuator):
   → Generates: 8 tests for uncovered lines
   → Runs: All tests pass ✓
   → Coverage: 72.1% → 95.3%
   ↓

3. validate-test-coverage (Sensor):
   → Re-checks: <REQ-ID> now at 95.3%
   → Status: ✅ Homeostasis achieved
```

---

## Installation

```bash
/plugin marketplace add foolishimp/ai_sdlc_method
/plugin install @aisdlc/testing-skills
```

---

## Usage Examples

### Example 1: Validate Coverage

```
You: "Check test coverage"

Claude: (invokes validate-test-coverage)

Overall Coverage: 87.5% ✅

Requirements Below 80% (2):
  ⚠️ <REQ-ID>: 72.1%
  ❌ REQ-F-CART-001: 45.8%

Recommendation: Generate missing tests?
```

---

### Example 2: Generate Missing Tests

```
You: "Generate tests for <REQ-ID>"

Claude: (invokes generate-missing-tests)

Analyzing coverage gaps for <REQ-ID>...

Uncovered Lines: 28 lines
  - Line 45: Zero amount check
  - Lines 67-72: Invalid token handling
  - Line 89: Max amount check

Generating 8 tests...
  ✓ test_payment_with_zero_amount
  ✓ test_payment_with_negative_amount
  ✓ test_payment_with_invalid_token
  ... (5 more)

Running tests... All 8 passing ✓

Coverage:
  Before: 72.1%
  After: 95.3%
  Improvement: +23.2%

✅ Tests generated and passing!
```

---

### Example 3: Run Integration Tests

```
You: "Run integration tests"

Claude: (invokes run-integration-tests)

Running BDD scenarios...
  ✓ 12 scenarios, 67 steps, all passing

Running API tests...
  ✓ 24 tests, all passing

Running E2E tests...
  ✓ 6 tests, all passing

Total: 57 integration tests
Pass Rate: 100% ✅
Duration: 59.6s
```

---

### Example 4: Coverage Report

```
You: "Generate coverage report"

Claude: (invokes create-coverage-report)

Generating comprehensive coverage report...

Overall: 87.5% ✅
Requirements: 36/42 tested (85.7%)

Top Gaps:
  1. REQ-F-CART-001: 45.8%
  2. <REQ-ID>: 72.1%
  3. REQ-F-PROFILE-001: 0%

Report generated:
  - coverage-reports/coverage-2025-11-20.html
  - coverage-reports/coverage-2025-11-20.json
  - coverage-reports/coverage-2025-11-20.md

Open: coverage-reports/coverage-2025-11-20.html
```

---

## Configuration

```yaml
plugins:
  - name: "@aisdlc/testing-skills"
    config:
      coverage:
        minimum_percentage: 80
        critical_paths_coverage: 100
        require_per_requirement: true

      test_generation:
        auto_generate_on_gap: false    # Ask first
        include_edge_cases: true
        include_error_cases: true
        frameworks:
          python: "pytest"

      integration_tests:
        auto_run_on_commit: false
        timeout_seconds: 300

      reporting:
        format: "html"
        include_req_mapping: true
        include_trends: true
```

---

## Dependencies

- **Required**: `@aisdlc/aisdlc-core` (^3.0.0) - REQ-* patterns and coverage detection

**Works With**:
- `@aisdlc/code-skills` - Complements TDD/BDD workflows
- `@aisdlc/requirements-skills` - Uses BR-* for test generation

---

## Skills Status

| Skill | Status | Type | Lines |
|-------|--------|------|-------|
| validate-test-coverage | ✅ | Sensor | 291 |
| generate-missing-tests | ✅ | Actuator | 363 |
| run-integration-tests | ✅ | Runner | 270 |
| create-coverage-report | ✅ | Reporter | 254 |
| create-test-specification | ✅ | Traceability | 254 |
| **TOTAL** | **✅ 100%** | **-** | **1,432** |

---

**"Excellence or nothing"** 🔥
