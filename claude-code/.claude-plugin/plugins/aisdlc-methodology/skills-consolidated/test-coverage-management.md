---
name: test-coverage-management
description: Complete test coverage workflow - create specifications, generate missing tests, validate coverage, run integration tests. Consolidates create-test-specification, generate-missing-tests, validate-test-coverage, run-integration-tests, create-coverage-report.
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
---

# Test Coverage Management

**Skill Type**: Quality Gate (System Test Stage)
**Purpose**: Ensure comprehensive test coverage with requirement traceability
**Consolidates**: create-test-specification, generate-missing-tests, validate-test-coverage, run-integration-tests, create-coverage-report

---

## When to Use This Skill

Use this skill when:
- Need to assess current test coverage
- Identifying gaps in test coverage
- Generating missing tests for requirements
- Creating test specifications (TCS)
- Before releases to validate coverage

---

## Test Coverage Workflow

### Phase 1: Create Test Specification

**Goal**: Document what tests are needed for each requirement.

**Test Case Specification (TCS) Template**:

```markdown
# TCS-001: User Login Test Specification

**Requirement**: REQ-F-AUTH-001
**Business Rules**: BR-001, BR-002, BR-003
**Priority**: P0 (Critical)
**Type**: Unit + Integration

## Test Cases

### TC-001-01: Successful Login (Happy Path)
**Description**: Verify user can login with valid credentials
**Preconditions**:
- User exists with email "user@example.com"
- User is not locked
**Steps**:
1. Enter email "user@example.com"
2. Enter password "SecurePass123!"
3. Click Login
**Expected Result**: Login succeeds, JWT token returned
**Validates**: REQ-F-AUTH-001, BR-001, BR-002

### TC-001-02: Invalid Email Format
**Description**: Verify login fails with invalid email
**Steps**:
1. Enter email "invalid-email"
2. Enter password "SecurePass123!"
3. Click Login
**Expected Result**: Error "Invalid email format"
**Validates**: BR-001

### TC-001-03: Short Password
**Description**: Verify login fails with password < 12 chars
**Steps**:
1. Enter email "user@example.com"
2. Enter password "short"
3. Click Login
**Expected Result**: Error "Password must be at least 12 characters"
**Validates**: BR-002

### TC-001-04: Account Lockout
**Description**: Verify account locks after 3 failed attempts
**Preconditions**:
- User exists with email "user@example.com"
- User has 0 failed attempts
**Steps**:
1. Attempt login with wrong password (3 times)
2. Attempt login with correct password
**Expected Result**: Error "Account locked. Try again in 15 minutes"
**Validates**: BR-003

## Coverage Matrix

| Test Case | REQ | BR-001 | BR-002 | BR-003 |
|-----------|-----|--------|--------|--------|
| TC-001-01 | ✅  | ✅     | ✅     | ❌     |
| TC-001-02 | ❌  | ✅     | ❌     | ❌     |
| TC-001-03 | ❌  | ❌     | ✅     | ❌     |
| TC-001-04 | ❌  | ❌     | ❌     | ✅     |
```

---

### Phase 2: Validate Test Coverage

**Goal**: Identify gaps between requirements and existing tests.

**Coverage Analysis**:

```python
# scripts/coverage_analysis.py

def analyze_coverage(requirements_dir: str, tests_dir: str) -> dict:
    """Analyze test coverage against requirements.

    Returns coverage report showing gaps.
    """
    requirements = load_requirements(requirements_dir)
    tests = scan_tests(tests_dir)

    coverage = {}
    for req_id, req in requirements.items():
        # Find tests that validate this requirement
        validating_tests = [
            t for t in tests
            if req_id in t.validates
        ]

        coverage[req_id] = {
            'requirement': req.description,
            'tests': len(validating_tests),
            'business_rules': {
                br: any(br in t.validates for t in validating_tests)
                for br in req.business_rules
            },
            'has_unit_tests': any(t.type == 'unit' for t in validating_tests),
            'has_integration_tests': any(t.type == 'integration' for t in validating_tests),
            'coverage_percent': calculate_coverage(req, validating_tests)
        }

    return coverage
```

**Coverage Report Output**:

```
[TEST COVERAGE REPORT]

Date: 2025-12-03
Requirements: 8
Tests: 45

=== Coverage by Requirement ===

REQ-F-AUTH-001: User Login
  Tests: 12 (Unit: 8, Integration: 4)
  Business Rules: BR-001 ✅, BR-002 ✅, BR-003 ✅
  Coverage: 100%

REQ-F-AUTH-002: Password Reset
  Tests: 5 (Unit: 3, Integration: 2)
  Business Rules: BR-005 ✅, BR-006 ❌
  Coverage: 80%
  GAP: Missing test for BR-006 (reset link expiration)

REQ-F-PORTAL-001: View Balance
  Tests: 0
  Coverage: 0%
  GAP: No tests! Critical requirement.

REQ-F-PORTAL-002: Update Profile
  Tests: 3 (Unit: 3, Integration: 0)
  Coverage: 60%
  GAP: Missing integration tests

REQ-F-PORTAL-003: Download Invoices
  Tests: 2 (Unit: 1, Integration: 1)
  Coverage: 50%
  GAP: Missing edge case tests

REQ-NFR-PERF-001: Response Time
  Tests: 2 (Performance: 2)
  Coverage: 100%

REQ-NFR-SEC-001: SSL/TLS
  Tests: 1 (Security: 1)
  Coverage: 100%

REQ-DATA-VAL-001: Email Validation
  Tests: 5 (Unit: 5)
  Coverage: 100%

=== Summary ===

Total Coverage: 73% (35/48 test cases)

By Type:
  Unit Tests: 28/40 (70%)
  Integration Tests: 7/20 (35%)
  Performance Tests: 2/3 (67%)
  Security Tests: 1/2 (50%)

Critical Gaps:
  1. REQ-F-PORTAL-001 - NO TESTS (0%)
  2. REQ-F-AUTH-002 - Missing BR-006 test
  3. REQ-F-PORTAL-002 - No integration tests

Recommendation: Add 13 tests to reach 80% coverage
```

---

### Phase 3: Generate Missing Tests

**Goal**: Auto-generate tests for uncovered requirements.

**For each gap, generate**:

```python
# tests/test_portal_001_balance.py

# Generated for: REQ-F-PORTAL-001 (View Balance)
# Gap identified: No existing tests

import pytest
from decimal import Decimal
from services.balance import get_balance, BalanceResult

class TestViewBalance:
    """Test suite for REQ-F-PORTAL-001: View Account Balance"""

    # TC-PORTAL-001-01: Happy path
    def test_get_balance_returns_correct_amounts(self, test_user):
        """Verify balance calculation is correct.

        Validates: REQ-F-PORTAL-001, F-001
        Formula: available = total - pending
        """
        # Arrange
        test_user.total_balance = Decimal("1000.00")
        test_user.pending_holds = Decimal("150.00")

        # Act
        result = get_balance(test_user.id)

        # Assert
        assert result.total_balance == Decimal("1000.00")
        assert result.pending_holds == Decimal("150.00")
        assert result.available_balance == Decimal("850.00")  # F-001

    # TC-PORTAL-001-02: Zero balance
    def test_get_balance_with_zero_balance(self, test_user):
        """Verify handling of zero balance.

        Validates: REQ-F-PORTAL-001 (edge case)
        """
        test_user.total_balance = Decimal("0.00")
        test_user.pending_holds = Decimal("0.00")

        result = get_balance(test_user.id)

        assert result.available_balance == Decimal("0.00")

    # TC-PORTAL-001-03: Pending exceeds total (edge case)
    def test_get_balance_with_negative_available(self, test_user):
        """Verify handling when holds exceed balance.

        Validates: REQ-F-PORTAL-001 (edge case)
        """
        test_user.total_balance = Decimal("100.00")
        test_user.pending_holds = Decimal("150.00")

        result = get_balance(test_user.id)

        # Should show negative available or zero?
        # Per business rule, show actual negative
        assert result.available_balance == Decimal("-50.00")

    # TC-PORTAL-001-04: User not found
    def test_get_balance_user_not_found(self):
        """Verify error when user doesn't exist.

        Validates: REQ-F-PORTAL-001 (error case)
        """
        with pytest.raises(UserNotFoundException):
            get_balance("nonexistent-user-id")

    # TC-PORTAL-001-05: Currency formatting
    def test_balance_display_format(self, test_user):
        """Verify currency display format.

        Validates: F-002 (display_format)
        """
        test_user.total_balance = Decimal("1234.567")

        result = get_balance(test_user.id)

        assert result.formatted_balance == "$1,234.57"  # F-002
```

---

### Phase 4: Run Integration Tests

**Goal**: Execute integration tests with reporting.

**Command**:
```bash
# Run with coverage
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Run specific requirement tests
pytest tests/ -v -k "REQ_F_AUTH_001"

# Run with markers
pytest tests/ -v -m "integration"
pytest tests/ -v -m "critical"
```

**Integration Test Example**:

```python
# tests/integration/test_auth_integration.py

# Integration tests for: REQ-F-AUTH-001

import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestAuthIntegration:
    """Integration tests for authentication flow.

    Validates: REQ-F-AUTH-001 (end-to-end)
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def registered_user(self, client):
        """Create user for testing."""
        response = client.post("/api/v1/users", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        return response.json()

    @pytest.mark.integration
    def test_login_flow_success(self, client, registered_user):
        """Test complete login flow.

        Validates: REQ-F-AUTH-001 (integration)
        """
        # Login
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        assert response.status_code == 200
        assert "token" in response.json()
        assert "expires_at" in response.json()

        # Verify token works
        token = response.json()["token"]
        response = client.get(
            "/api/v1/auth/session",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    @pytest.mark.integration
    def test_login_lockout_flow(self, client, registered_user):
        """Test account lockout after failed attempts.

        Validates: BR-003 (integration)
        """
        # Fail 3 times
        for _ in range(3):
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "wrong_password"
            })
            assert response.status_code == 401

        # 4th attempt should be locked
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!"  # Even correct password
        })
        assert response.status_code == 423  # Locked
        assert "locked" in response.json()["error"].lower()
```

---

### Phase 5: Generate Coverage Report

**Goal**: Create comprehensive coverage report.

**HTML Report**:
```bash
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html
```

**Traceability Report**:

```markdown
# Test Coverage Traceability Report

Generated: 2025-12-03
Project: customer-portal

## Executive Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Line Coverage | 87% | 80% | ✅ |
| Branch Coverage | 72% | 70% | ✅ |
| Requirement Coverage | 85% | 100% | ⚠️ |
| Business Rule Coverage | 90% | 100% | ⚠️ |

## Coverage by Requirement

| Requirement | Unit | Integration | Total | Status |
|-------------|------|-------------|-------|--------|
| REQ-F-AUTH-001 | 8/8 | 4/4 | 100% | ✅ |
| REQ-F-AUTH-002 | 3/4 | 2/2 | 83% | ⚠️ |
| REQ-F-PORTAL-001 | 5/5 | 2/3 | 88% | ✅ |
| REQ-F-PORTAL-002 | 3/3 | 0/2 | 60% | ❌ |
| REQ-F-PORTAL-003 | 2/4 | 1/2 | 50% | ❌ |
| REQ-NFR-PERF-001 | 2/2 | - | 100% | ✅ |
| REQ-NFR-SEC-001 | 1/1 | - | 100% | ✅ |
| REQ-DATA-VAL-001 | 5/5 | - | 100% | ✅ |

## Gaps Requiring Action

1. **REQ-F-AUTH-002**: Missing test for BR-006 (reset link expiration)
2. **REQ-F-PORTAL-002**: No integration tests
3. **REQ-F-PORTAL-003**: Missing 2 unit tests, 1 integration test

## Recommendation

Add 6 tests to achieve 100% requirement coverage:
- 1 unit test for BR-006
- 2 integration tests for REQ-F-PORTAL-002
- 2 unit tests + 1 integration test for REQ-F-PORTAL-003

Estimated effort: 4 hours
```

---

## Output Format

```
[TEST COVERAGE MANAGEMENT]

Action: Coverage Analysis + Gap Generation

Current State:
  Requirements: 8
  Existing Tests: 45
  Line Coverage: 87%
  Requirement Coverage: 73%

Gaps Identified: 6
  1. REQ-F-PORTAL-001 - No tests (GENERATED)
  2. REQ-F-AUTH-002/BR-006 - Missing test (GENERATED)
  3. REQ-F-PORTAL-002 - No integration tests (GENERATED)
  ...

Tests Generated: 13 new tests
  + tests/test_portal_001_balance.py (5 tests)
  + tests/test_auth_002_reset.py (2 tests)
  + tests/integration/test_portal_002.py (3 tests)
  + tests/integration/test_portal_003.py (3 tests)

New Coverage:
  Requirement Coverage: 100%
  Line Coverage: 92%

Test Coverage Management Complete!
  Next: Run full test suite to verify
```

---

## Configuration

```yaml
# .claude/plugins.yml
plugins:
  - name: "@aisdlc/aisdlc-methodology"
    config:
      test_coverage:
        minimum_line_coverage: 80
        minimum_branch_coverage: 70
        minimum_requirement_coverage: 100
        require_integration_tests: true
        generate_missing_tests: true
        coverage_report_format: ["html", "term", "json"]
        block_deploy_if_below_threshold: true
```

---

## Homeostasis Behavior

**If coverage below threshold**:
- Detect: Coverage < 80%
- Signal: "Coverage insufficient"
- Action: Generate missing tests
- Block: Deploy blocked until threshold met

**If requirement has no tests**:
- Detect: REQ-* with 0 tests
- Signal: "Critical gap - untested requirement"
- Action: Generate test specification + tests

---

## Key Principles Applied

- **Test Driven Development**: Tests validate requirements
- **Fail Fast**: Detect gaps early
- **Perfectionist Excellence**: 100% requirement coverage

**"Excellence or nothing"**
