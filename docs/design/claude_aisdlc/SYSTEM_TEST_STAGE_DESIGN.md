# System Test Stage - Design Document

**Document Type**: Technical Design Specification
**Project**: ai_sdlc_method (claude_aisdlc solution)
**Version**: 1.0
**Date**: 2025-12-03
**Status**: Draft
**Stage**: Design (Section 5.0)

---

## Requirements Traceability

This design implements the following requirements:

| Requirement | Description | Priority | Maps To |
|-------------|-------------|----------|---------|
| REQ-SYSTEST-001 | BDD Scenario Creation (Given/When/Then) | High | Sections 2, 3, 4 |
| REQ-SYSTEST-002 | Integration Test Execution (Automated BDD) | High | Sections 5, 6, 7 |
| REQ-SYSTEST-003 | Test-to-Requirement Traceability (# Validates: REQ-*) | High | Sections 3, 8, 9 |

**Source**: User-provided requirements for System Test Stage design

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [BDD Scenario Templates](#2-bdd-scenario-templates)
3. [Feature File Structure](#3-feature-file-structure)
4. [Step Definition Patterns](#4-step-definition-patterns)
5. [Test Execution Framework](#5-test-execution-framework)
6. [Integration with Test Runners](#6-integration-with-test-runners)
7. [Automation Architecture](#7-automation-architecture)
8. [Coverage Matrix Generation](#8-coverage-matrix-generation)
9. [Test-Requirement Linking](#9-test-requirement-linking)
10. [Quality Gates](#10-quality-gates)
11. [Implementation Guidance](#11-implementation-guidance)
12. [Examples](#12-examples)

---

## 1. Executive Summary

### 1.1 Purpose

The System Test Stage (Stage 5 in the 7-Stage AI SDLC) validates that code implementations satisfy requirements through **automated integration testing** using **Behavior-Driven Development (BDD)** methodology.

### 1.2 Design Principles

1. **Business-Readable Tests** - Gherkin syntax enables non-technical stakeholders to understand tests
2. **Requirement Traceability** - Every scenario links to REQ-* keys via tags and comments
3. **Automation-First** - All scenarios must be executable via pytest-bdd or behave
4. **Integration Focus** - Tests validate end-to-end workflows, not just unit behavior
5. **Coverage Metrics** - Generate reports showing requirement coverage by tests
6. **CI/CD Integration** - Tests run automatically on every commit

### 1.3 Key Design Decisions

| Decision | Rationale | Requirement |
|----------|-----------|-------------|
| pytest-bdd as primary framework | Python-native, integrates with existing pytest ecosystem | REQ-SYSTEST-002 |
| Gherkin (Given/When/Then) format | Industry standard, readable by business and technical teams | REQ-SYSTEST-001 |
| Tag-based requirement linking | Simple, parseable, works with Gherkin @tags | REQ-SYSTEST-003 |
| File-based organization | Mirrors requirement structure, easy to navigate | REQ-SYSTEST-001 |
| Coverage matrix in JSON + Markdown | Machine-readable and human-readable formats | REQ-SYSTEST-003 |
| Separate step definitions from features | Reusable steps across scenarios | REQ-SYSTEST-002 |

### 1.4 Architecture Overview

```
System Test Stage
├─ Feature Files (Gherkin)
│  ├─ Organized by functional area
│  ├─ Tagged with @REQ-* keys
│  └─ Comment headers: # Validates: REQ-*
│
├─ Step Definitions (Python)
│  ├─ @given, @when, @then decorators
│  ├─ Reusable across scenarios
│  └─ Integration with test fixtures
│
├─ Test Execution (pytest-bdd)
│  ├─ Automatic scenario discovery
│  ├─ Parallel execution
│  └─ HTML/JSON/JUnit reports
│
├─ Coverage Matrix Generator
│  ├─ Extracts REQ-* from scenarios
│  ├─ Generates coverage reports
│  └─ Highlights gaps
│
└─ CI/CD Integration
   ├─ GitHub Actions workflows
   ├─ Quality gate enforcement
   └─ Coverage thresholds
```

---

## 2. BDD Scenario Templates

### 2.1 Standard Scenario Template

**Template**: `SCENARIO_TEMPLATE.feature`

```gherkin
# Validates: <REQ-KEY>, <REQ-KEY>, ...
# Stage: System Test (Stage 5)
# Priority: <High|Medium|Low>

@system-test @<functional-area> @<REQ-KEY>
Feature: <Feature Name>
  As a <persona>
  I want <capability>
  So that <business value>

  Background:
    Given <common preconditions>
    And <setup state>

  @<scenario-tag> @<REQ-KEY>
  Scenario: <Scenario description>
    Given <precondition>
    When <action>
    Then <expected outcome>
    And <additional assertion>

  @<scenario-tag> @<REQ-KEY>
  Scenario Outline: <Parameterized scenario>
    Given <precondition with <parameter>>
    When <action with <parameter>>
    Then <expected outcome with <parameter>>

    Examples:
      | parameter | expected_result |
      | value1    | result1         |
      | value2    | result2         |
```

### 2.2 REQ Tag Integration Patterns

**Pattern 1: Comment Header (Mandatory)**

```gherkin
# Validates: REQ-F-AUTH-001, REQ-NFR-SEC-001
# Stage: System Test (Stage 5)
# Priority: High
```

**Pattern 2: Feature-Level Tags**

```gherkin
@system-test @authentication @REQ-F-AUTH-001
Feature: User Authentication
```

**Pattern 3: Scenario-Level Tags**

```gherkin
@login @REQ-F-AUTH-001 @REQ-NFR-PERF-001
Scenario: Successful user login
```

**Pattern 4: Table-Based Requirement Mapping**

```gherkin
Feature: Authentication
  # Requirements Coverage:
  # | Requirement        | Scenarios |
  # | REQ-F-AUTH-001     | SC-001, SC-002, SC-003 |
  # | REQ-NFR-SEC-001    | SC-002, SC-004 |
```

### 2.3 Requirement-Specific Templates

#### 2.3.1 Functional Requirement (REQ-F-*)

```gherkin
# Validates: REQ-F-AUTH-001 (User login with email/password)
# Stage: System Test (Stage 5)

@system-test @authentication @REQ-F-AUTH-001
Feature: User Authentication
  As a registered user
  I want to log in with my email and password
  So that I can access my account

  Background:
    Given a user with email "user@example.com" and password "SecurePass123" exists
    And the user account is active

  @happy-path @ST-001
  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter email "user@example.com"
    And I enter password "SecurePass123"
    And I click the "Login" button
    Then I should be redirected to the dashboard
    And I should see a welcome message "Welcome, User!"
    And a session token should be created

  @error-handling @ST-002
  Scenario: Failed login with invalid password
    Given I am on the login page
    When I enter email "user@example.com"
    And I enter password "WrongPassword"
    And I click the "Login" button
    Then I should see an error message "Invalid email or password"
    And I should remain on the login page
    And no session token should be created
```

#### 2.3.2 Non-Functional Requirement (REQ-NFR-*)

```gherkin
# Validates: REQ-NFR-PERF-001 (Login response time < 500ms)
# Stage: System Test (Stage 5)

@system-test @performance @REQ-NFR-PERF-001
Feature: Login Performance
  As a user
  I want login to be fast
  So that I don't experience delays

  @performance @ST-010
  Scenario: Login completes within performance threshold
    Given a user with email "user@example.com" exists
    And the system is under normal load
    When I submit login credentials
    Then the response should be received within 500 milliseconds
    And the response should contain a valid session token
```

#### 2.3.3 Data Quality Requirement (REQ-DATA-*)

```gherkin
# Validates: REQ-DATA-VAL-001 (Email validation)
# Stage: System Test (Stage 5)

@system-test @data-validation @REQ-DATA-VAL-001
Feature: Email Validation
  As a system
  I want to validate email formats
  So that invalid emails are rejected

  @validation @ST-020
  Scenario Outline: Email format validation
    Given I am registering a new user
    When I enter email "<email>"
    Then the email validation result should be "<result>"

    Examples:
      | email                | result  |
      | user@example.com     | valid   |
      | invalid.email        | invalid |
      | @example.com         | invalid |
      | user@                | invalid |
      | user@sub.example.com | valid   |
```

#### 2.3.4 Business Rule (REQ-BR-*)

```gherkin
# Validates: REQ-BR-PRICE-001 (Discount rules)
# Stage: System Test (Stage 5)

@system-test @business-rules @REQ-BR-PRICE-001
Feature: Pricing Discount Rules
  As a customer
  I want to receive applicable discounts
  So that I pay the correct price

  @pricing @ST-030
  Scenario: Apply 10% discount for orders over $100
    Given I have items in my cart totaling $120.00
    When I proceed to checkout
    Then a 10% discount should be applied
    And the final price should be $108.00
```

---

## 3. Feature File Structure

### 3.1 Directory Organization

```
tests/
├── features/
│   ├── system-test/                    # System Test Stage (Stage 5)
│   │   ├── authentication/             # Functional area
│   │   │   ├── login.feature           # REQ-F-AUTH-001, REQ-F-AUTH-002
│   │   │   ├── registration.feature    # REQ-F-AUTH-003
│   │   │   └── password_reset.feature  # REQ-F-AUTH-004
│   │   │
│   │   ├── data-validation/            # Data quality tests
│   │   │   ├── email_validation.feature     # REQ-DATA-VAL-001
│   │   │   ├── input_sanitization.feature   # REQ-DATA-SEC-001
│   │   │   └── data_integrity.feature       # REQ-DATA-INT-001
│   │   │
│   │   ├── performance/                # Non-functional tests
│   │   │   ├── response_times.feature       # REQ-NFR-PERF-001
│   │   │   ├── load_handling.feature        # REQ-NFR-SCALE-001
│   │   │   └── resource_usage.feature       # REQ-NFR-RESOURCE-001
│   │   │
│   │   ├── security/                   # Security tests
│   │   │   ├── authentication_security.feature  # REQ-NFR-SEC-001
│   │   │   ├── authorization.feature            # REQ-NFR-SEC-002
│   │   │   └── data_encryption.feature          # REQ-NFR-SEC-003
│   │   │
│   │   └── integration/                # Cross-component tests
│   │       ├── end_to_end_flows.feature
│   │       └── third_party_integrations.feature
│   │
│   ├── steps/                          # Step definitions
│   │   ├── conftest.py                 # pytest fixtures
│   │   ├── common_steps.py             # Shared steps (Given/When/Then)
│   │   ├── authentication_steps.py     # Domain-specific steps
│   │   ├── data_validation_steps.py
│   │   └── performance_steps.py
│   │
│   └── pytest.ini                      # pytest-bdd configuration
│
├── reports/                            # Test reports
│   ├── coverage/                       # Coverage reports
│   │   ├── requirement_coverage.json
│   │   ├── requirement_coverage.md
│   │   └── coverage_matrix.html
│   │
│   └── test-results/                   # Test execution results
│       ├── junit.xml
│       ├── report.html
│       └── test_run_<timestamp>.json
│
└── fixtures/                           # Test data
    ├── users.json
    ├── test_data.yml
    └── mock_responses/
```

### 3.2 Naming Conventions

| Artifact | Pattern | Example |
|----------|---------|---------|
| Feature file | `<functional_area>.feature` | `authentication.feature` |
| Scenario tag | `@<area>-<number>` or `@<REQ-KEY>` | `@ST-001`, `@REQ-F-AUTH-001` |
| Step definition file | `<area>_steps.py` | `authentication_steps.py` |
| Test fixture | `<purpose>_fixture` | `authenticated_user_fixture` |

### 3.3 Feature File Metadata

**Required Header Fields:**

```gherkin
# Validates: <comma-separated REQ keys>
# Stage: System Test (Stage 5)
# Priority: <High|Medium|Low>
# Owner: <QA Engineer name or team>
# Created: <YYYY-MM-DD>
# Updated: <YYYY-MM-DD>
```

**Example:**

```gherkin
# Validates: REQ-F-AUTH-001, REQ-F-AUTH-002
# Stage: System Test (Stage 5)
# Priority: High
# Owner: QA Team
# Created: 2025-12-03
# Updated: 2025-12-03

@system-test @authentication
Feature: User Authentication
```

---

## 4. Step Definition Patterns

### 4.1 Standard Step Definition Structure

**File**: `tests/features/steps/authentication_steps.py`

```python
#!/usr/bin/env python3
"""
Authentication Step Definitions

# Implements: REQ-SYSTEST-002 (BDD Step Execution)
# Validates: REQ-F-AUTH-001, REQ-F-AUTH-002
"""

import re
from pathlib import Path
from pytest_bdd import scenarios, given, when, then, parsers

# Import fixtures
from conftest import test_context, authenticated_user, login_page


# =============================================================================
# Scenario Loading
# =============================================================================

# Load all scenarios from authentication feature files
scenarios('../system-test/authentication/')


# =============================================================================
# Given Steps (Preconditions)
# =============================================================================

@given('a user with email "<email>" and password "<password>" exists')
@given(parsers.parse('a user with email "{email}" and password "{password}" exists'))
def given_user_exists(test_context, email, password):
    """
    Create a test user with specified credentials.

    # Validates: REQ-F-AUTH-001
    """
    from tests.fixtures.user_factory import create_user

    user = create_user(email=email, password=password)
    test_context['user'] = user
    test_context['credentials'] = {'email': email, 'password': password}

    assert user.email == email, f"User email mismatch: {user.email} != {email}"


@given('the user account is active')
def given_user_active(test_context):
    """
    Ensure the test user's account is in active state.

    # Validates: REQ-F-AUTH-001
    """
    user = test_context['user']
    user.activate()
    assert user.is_active, "User account should be active"


@given('I am on the login page')
def given_on_login_page(test_context, login_page):
    """
    Navigate to the login page.

    # Validates: REQ-F-AUTH-001
    """
    test_context['page'] = login_page
    login_page.navigate()
    assert login_page.is_loaded(), "Login page failed to load"


# =============================================================================
# When Steps (Actions)
# =============================================================================

@when('I enter email "<email>"')
@when(parsers.parse('I enter email "{email}"'))
def when_enter_email(test_context, email):
    """
    Enter email into login form.

    # Validates: REQ-F-AUTH-001
    """
    page = test_context['page']
    page.enter_email(email)
    test_context['entered_email'] = email


@when('I enter password "<password>"')
@when(parsers.parse('I enter password "{password}"'))
def when_enter_password(test_context, password):
    """
    Enter password into login form.

    # Validates: REQ-F-AUTH-001
    """
    page = test_context['page']
    page.enter_password(password)
    test_context['entered_password'] = password


@when('I click the "Login" button')
@when(parsers.parse('I click the "{button_text}" button'))
def when_click_button(test_context, button_text):
    """
    Click a button on the page.

    # Validates: REQ-F-AUTH-001
    """
    page = test_context['page']
    response = page.click_button(button_text)
    test_context['response'] = response


@when('I submit login credentials')
def when_submit_credentials(test_context):
    """
    Submit login form with stored credentials.

    # Validates: REQ-F-AUTH-001, REQ-NFR-PERF-001
    """
    import time

    page = test_context['page']
    credentials = test_context['credentials']

    start_time = time.time()
    response = page.submit_login(
        email=credentials['email'],
        password=credentials['password']
    )
    end_time = time.time()

    test_context['response'] = response
    test_context['response_time'] = (end_time - start_time) * 1000  # ms


# =============================================================================
# Then Steps (Assertions)
# =============================================================================

@then('I should be redirected to the dashboard')
def then_redirected_to_dashboard(test_context):
    """
    Verify redirect to dashboard page.

    # Validates: REQ-F-AUTH-001
    """
    page = test_context['page']
    assert page.current_url.endswith('/dashboard'), \
        f"Expected dashboard URL, got: {page.current_url}"


@then('I should see a welcome message "<message>"')
@then(parsers.parse('I should see a welcome message "{message}"'))
def then_see_welcome_message(test_context, message):
    """
    Verify welcome message is displayed.

    # Validates: REQ-F-AUTH-001
    """
    page = test_context['page']
    actual_message = page.get_welcome_message()
    assert message in actual_message, \
        f"Expected '{message}' in welcome message, got: {actual_message}"


@then('a session token should be created')
def then_session_token_created(test_context):
    """
    Verify session token exists.

    # Validates: REQ-F-AUTH-001
    """
    response = test_context['response']
    assert 'session_token' in response, "Session token not found in response"
    assert response['session_token'], "Session token is empty"
    test_context['session_token'] = response['session_token']


@then('I should see an error message "<message>"')
@then(parsers.parse('I should see an error message "{message}"'))
def then_see_error_message(test_context, message):
    """
    Verify error message is displayed.

    # Validates: REQ-F-AUTH-001
    """
    page = test_context['page']
    error_message = page.get_error_message()
    assert error_message, "No error message displayed"
    assert message in error_message, \
        f"Expected '{message}' in error, got: {error_message}"


@then('I should remain on the login page')
def then_remain_on_login_page(test_context):
    """
    Verify user stayed on login page.

    # Validates: REQ-F-AUTH-001
    """
    page = test_context['page']
    assert page.current_url.endswith('/login'), \
        f"Expected login URL, got: {page.current_url}"


@then('no session token should be created')
def then_no_session_token(test_context):
    """
    Verify no session token in response.

    # Validates: REQ-F-AUTH-001
    """
    response = test_context['response']
    assert 'session_token' not in response or not response.get('session_token'), \
        "Session token should not be present"


@then(parsers.parse('the response should be received within {milliseconds:d} milliseconds'))
def then_response_within_time(test_context, milliseconds):
    """
    Verify response time meets performance requirement.

    # Validates: REQ-NFR-PERF-001
    """
    response_time = test_context['response_time']
    assert response_time < milliseconds, \
        f"Response time {response_time}ms exceeds threshold {milliseconds}ms"


@then('the response should contain a valid session token')
def then_valid_session_token(test_context):
    """
    Verify session token format and validity.

    # Validates: REQ-F-AUTH-001
    """
    response = test_context['response']
    token = response.get('session_token')

    assert token, "Session token is missing"
    assert len(token) >= 32, "Session token is too short"
    assert re.match(r'^[A-Za-z0-9_-]+$', token), "Session token has invalid format"
```

### 4.2 Reusable Step Patterns

**Common Steps** (`common_steps.py`):

```python
"""
Common step definitions reusable across features.

# Implements: REQ-SYSTEST-002
"""

from pytest_bdd import given, when, then, parsers


@given('the system is under normal load')
def given_normal_load(test_context):
    """Standard system load conditions."""
    test_context['load_level'] = 'normal'


@given('the AISDLC methodology is in use')
def given_aisdlc_methodology(test_context):
    """Verify AISDLC methodology is active."""
    test_context['methodology'] = 'AISDLC'


@given(parsers.parse('the current stage is "{stage}"'))
def given_current_stage(test_context, stage):
    """Set the current SDLC stage."""
    test_context['current_stage'] = stage


@when('I wait for {seconds:d} seconds')
def when_wait(seconds):
    """Wait for specified duration."""
    import time
    time.sleep(seconds)


@then(parsers.parse('the operation should succeed'))
def then_operation_succeeds(test_context):
    """Verify operation success."""
    response = test_context.get('response')
    assert response, "No response recorded"
    assert response.get('success') or response.get('status') == 'success'
```

### 4.3 Step Definition Best Practices

1. **One step = one action/assertion**
2. **Use test_context fixture** for sharing state between steps
3. **Tag steps with # Validates: REQ-*** comments
4. **Support both literal and parsed parameters** (for flexibility)
5. **Include clear assertion messages** for debugging
6. **Keep steps focused and reusable**

---

## 5. Test Execution Framework

### 5.1 pytest-bdd Configuration

**File**: `tests/features/pytest.ini`

```ini
# pytest-bdd configuration
# Implements: REQ-SYSTEST-002

[pytest]
# Test discovery
testpaths = features/steps
python_files = test_*.py *_steps.py
python_classes = Test*
python_functions = test_*

# BDD configuration
bdd_features_base_dir = features/system-test

# Markers
markers =
    system-test: System Test Stage (Stage 5) tests
    authentication: Authentication feature tests
    data-validation: Data validation tests
    performance: Performance tests
    security: Security tests
    integration: Integration tests
    REQ-F-*: Functional requirement tests
    REQ-NFR-*: Non-functional requirement tests
    REQ-DATA-*: Data quality requirement tests
    REQ-BR-*: Business rule tests

# Output
addopts =
    -v
    --strict-markers
    --tb=short
    --maxfail=5
    --junit-xml=reports/test-results/junit.xml
    --html=reports/test-results/report.html
    --self-contained-html
    --cov=src
    --cov-report=html:reports/coverage/html
    --cov-report=term-missing

# Coverage thresholds
cov-fail-under = 80

# Logging
log_cli = true
log_cli_level = INFO
log_file = reports/test-results/pytest.log
log_file_level = DEBUG
```

### 5.2 Test Execution Commands

**Run all system tests:**

```bash
cd tests/features
pytest
```

**Run specific feature:**

```bash
pytest --feature system-test/authentication/login.feature
```

**Run tests for specific requirement:**

```bash
pytest -m REQ-F-AUTH-001
```

**Run tests by category:**

```bash
pytest -m authentication
pytest -m performance
pytest -m "system-test and not performance"
```

**Parallel execution:**

```bash
pytest -n auto  # Requires pytest-xdist
```

**Generate coverage report:**

```bash
pytest --cov=src --cov-report=html
```

### 5.3 Test Execution Output

**Expected output structure:**

```
tests/features/system-test/authentication/login.feature::test_successful_login
  PASSED                                                              [ 10%]
tests/features/system-test/authentication/login.feature::test_failed_login
  PASSED                                                              [ 20%]
...

======================== Test Coverage Summary =========================
src/auth_service.py                    95%
src/user_model.py                      90%
src/session_manager.py                 85%
-----------------------------------------------------------------------
TOTAL                                  90%

======================== Requirement Coverage ==========================
REQ-F-AUTH-001: 100% (5/5 scenarios passed)
REQ-F-AUTH-002: 100% (3/3 scenarios passed)
REQ-NFR-PERF-001: 100% (2/2 scenarios passed)
-----------------------------------------------------------------------
TOTAL COVERAGE                         100%

======================== 15 passed in 2.34s ============================
```

---

## 6. Integration with Test Runners

### 6.1 pytest-bdd Integration

**Installation:**

```bash
pip install pytest-bdd pytest-html pytest-cov pytest-xdist
```

**File**: `requirements-test.txt`

```txt
# Test framework dependencies
# Implements: REQ-SYSTEST-002

pytest>=7.4.0
pytest-bdd>=6.1.0
pytest-html>=3.2.0
pytest-cov>=4.1.0
pytest-xdist>=3.3.0  # Parallel execution
pytest-timeout>=2.1.0
pytest-mock>=3.11.0

# Assertion helpers
assertpy>=1.1

# Test data
faker>=19.0.0
factory-boy>=3.3.0

# API testing
requests>=2.31.0
responses>=0.23.0

# Performance testing
pytest-benchmark>=4.0.0
locust>=2.15.0  # Load testing
```

### 6.2 behave Integration (Alternative)

**Configuration**: `features/behave.ini`

```ini
# behave configuration (alternative to pytest-bdd)
# Implements: REQ-SYSTEST-002

[behave]
paths = features/system-test
junit = true
junit_directory = reports/test-results
format = progress
format = json
outfiles = reports/test-results/behave-results.json
summary = true

# Tags
tags = @system-test and not @skip

# Logging
logging_level = INFO
logging_format = %(levelname)s: %(message)s
```

**Execution:**

```bash
behave features/system-test/authentication/login.feature
behave --tags=@REQ-F-AUTH-001
behave --tags="@authentication and not @wip"
```

### 6.3 Comparison: pytest-bdd vs behave

| Feature | pytest-bdd | behave |
|---------|-----------|--------|
| **Integration** | Native pytest integration | Standalone |
| **Fixtures** | Full pytest fixtures | Custom context |
| **Plugins** | Full pytest plugin ecosystem | Limited |
| **Reporting** | pytest reports + plugins | Built-in + custom |
| **Parallel** | pytest-xdist | Not built-in |
| **Learning curve** | Steeper (pytest knowledge needed) | Gentler |
| **Recommendation** | **Primary choice** for Python projects | Alternative |

**Recommendation**: Use **pytest-bdd** as the primary framework for AISDLC System Test Stage.

---

## 7. Automation Architecture

### 7.1 Test Automation Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    Test Automation Stack                        │
└─────────────────────────────────────────────────────────────────┘
         │
         ├─ Layer 1: Feature Files (Gherkin)
         │    └─ Business-readable scenarios with REQ tags
         │
         ├─ Layer 2: Step Definitions (Python)
         │    └─ Map Gherkin steps to code execution
         │
         ├─ Layer 3: Test Fixtures (pytest)
         │    └─ Setup/teardown, test data, mocks
         │
         ├─ Layer 4: Page Objects / API Clients
         │    └─ Abstract interaction with system under test
         │
         ├─ Layer 5: Test Utilities
         │    └─ Helpers, assertions, data factories
         │
         └─ Layer 6: System Under Test
              └─ Application code being tested
```

### 7.2 Test Fixture Architecture

**File**: `tests/features/steps/conftest.py`

```python
"""
Test fixtures for System Test Stage.

# Implements: REQ-SYSTEST-002
"""

import pytest
from pathlib import Path
from datetime import datetime


# =============================================================================
# Scope: Session (once per test run)
# =============================================================================

@pytest.fixture(scope='session')
def test_config():
    """Load test configuration."""
    return {
        'base_url': 'http://localhost:8000',
        'timeout': 30,
        'retry_attempts': 3
    }


@pytest.fixture(scope='session')
def database_connection():
    """Create database connection for tests."""
    # Setup
    db = create_test_database()
    yield db
    # Teardown
    db.close()


# =============================================================================
# Scope: Module (once per test file)
# =============================================================================

@pytest.fixture(scope='module')
def api_client(test_config):
    """Create API client for testing."""
    from tests.utils.api_client import TestAPIClient
    return TestAPIClient(base_url=test_config['base_url'])


# =============================================================================
# Scope: Function (once per test)
# =============================================================================

@pytest.fixture
def test_context():
    """Shared context for passing data between BDD steps."""
    return {}


@pytest.fixture
def clean_database(database_connection):
    """Clean database before each test."""
    database_connection.truncate_all_tables()
    yield database_connection


@pytest.fixture
def authenticated_user(clean_database):
    """Create an authenticated test user."""
    from tests.fixtures.user_factory import create_user

    user = create_user(
        email="test@example.com",
        password="TestPass123",
        is_active=True
    )

    # # Validates: REQ-F-AUTH-001
    session_token = user.authenticate()

    return {
        'user': user,
        'session_token': session_token
    }


@pytest.fixture
def login_page(api_client):
    """Create login page object."""
    from tests.pages.login_page import LoginPage
    return LoginPage(api_client)


# =============================================================================
# Parametrized Fixtures
# =============================================================================

@pytest.fixture(params=['valid', 'invalid', 'expired'])
def token_type(request):
    """Parametrized fixture for token testing."""
    return request.param


# =============================================================================
# Hooks
# =============================================================================

def pytest_bdd_before_scenario(request, feature, scenario):
    """Hook: Before each scenario."""
    print(f"\n▶ Running: {feature.name} - {scenario.name}")


def pytest_bdd_after_scenario(request, feature, scenario):
    """Hook: After each scenario."""
    print(f"✓ Completed: {scenario.name}")


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Hook: On step error."""
    print(f"✗ Step failed: {step.keyword} {step.name}")
    print(f"  Error: {exception}")
```

### 7.3 Page Object Pattern (for UI tests)

**File**: `tests/pages/login_page.py`

```python
"""
Login page object for UI testing.

# Implements: REQ-SYSTEST-002
# Validates: REQ-F-AUTH-001
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LoginPage:
    """Page object for login page interactions."""

    # Locators
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.ID, "login-button")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    WELCOME_MESSAGE = (By.CLASS_NAME, "welcome-message")

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 10)

    def navigate(self):
        """Navigate to login page."""
        self.driver.get(f"{self.base_url}/login")

    def is_loaded(self):
        """Check if page is loaded."""
        return self.wait.until(
            EC.presence_of_element_located(self.EMAIL_INPUT)
        )

    def enter_email(self, email):
        """Enter email into input field."""
        element = self.driver.find_element(*self.EMAIL_INPUT)
        element.clear()
        element.send_keys(email)

    def enter_password(self, password):
        """Enter password into input field."""
        element = self.driver.find_element(*self.PASSWORD_INPUT)
        element.clear()
        element.send_keys(password)

    def click_button(self, button_text):
        """Click button by text."""
        button = self.driver.find_element(By.XPATH, f"//button[text()='{button_text}']")
        button.click()

    def submit_login(self, email, password):
        """Submit login form."""
        self.enter_email(email)
        self.enter_password(password)
        self.click_button("Login")

        # Wait for response
        self.wait.until(
            lambda d: d.current_url != f"{self.base_url}/login" or
                     self.get_error_message()
        )

        return {
            'success': d.current_url != f"{self.base_url}/login",
            'url': d.current_url
        }

    def get_error_message(self):
        """Get error message text."""
        try:
            element = self.driver.find_element(*self.ERROR_MESSAGE)
            return element.text
        except:
            return None

    def get_welcome_message(self):
        """Get welcome message text."""
        try:
            element = self.wait.until(
                EC.presence_of_element_located(self.WELCOME_MESSAGE)
            )
            return element.text
        except:
            return None

    @property
    def current_url(self):
        """Get current URL."""
        return self.driver.current_url
```

### 7.4 API Client Pattern (for API tests)

**File**: `tests/utils/api_client.py`

```python
"""
API client for integration testing.

# Implements: REQ-SYSTEST-002
"""

import requests
from typing import Dict, Any, Optional


class TestAPIClient:
    """HTTP client for API testing."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """
        POST request to API.

        # Validates: REQ-F-AUTH-001 (login endpoint)
        """
        url = f"{self.base_url}{endpoint}"

        if headers:
            self.session.headers.update(headers)

        response = self.session.post(
            url,
            json=data,
            timeout=self.timeout
        )

        return response

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and get session token.

        # Validates: REQ-F-AUTH-001
        """
        response = self.post(
            '/api/v1/auth/login',
            data={'email': email, 'password': password}
        )

        if response.status_code == 200:
            data = response.json()
            # Store token for subsequent requests
            self.session.headers['Authorization'] = f"Bearer {data['session_token']}"
            return data
        else:
            return {
                'success': False,
                'error': response.json().get('message', 'Login failed')
            }
```

---

## 8. Coverage Matrix Generation

### 8.1 Coverage Matrix Data Model

**File**: `tests/reports/coverage/requirement_coverage.json`

```json
{
  "generated_at": "2025-12-03T12:00:00Z",
  "project": "ai_sdlc_method",
  "stage": "system_test",
  "summary": {
    "total_requirements": 45,
    "requirements_with_tests": 42,
    "requirements_without_tests": 3,
    "total_scenarios": 127,
    "scenarios_passed": 125,
    "scenarios_failed": 2,
    "coverage_percentage": 93.33
  },
  "requirements": [
    {
      "key": "REQ-F-AUTH-001",
      "description": "User login with email/password",
      "category": "functional",
      "priority": "high",
      "stage": "system_test",
      "coverage": {
        "scenarios": [
          {
            "id": "ST-001",
            "name": "Successful login with valid credentials",
            "feature_file": "tests/features/system-test/authentication/login.feature",
            "status": "passed",
            "duration_ms": 234
          },
          {
            "id": "ST-002",
            "name": "Failed login with invalid password",
            "feature_file": "tests/features/system-test/authentication/login.feature",
            "status": "passed",
            "duration_ms": 189
          }
        ],
        "scenario_count": 5,
        "passed_count": 5,
        "failed_count": 0,
        "coverage_percentage": 100.0
      },
      "traceability": {
        "intent": "INT-001",
        "design": ["AuthenticationService", "ADR-003"],
        "tasks": ["TASK-001", "TASK-002"],
        "code": ["src/auth_service.py", "src/session_manager.py"],
        "unit_tests": ["tests/unit/test_auth_service.py"],
        "system_tests": ["tests/features/system-test/authentication/login.feature"],
        "uat": ["UAT-001"]
      }
    },
    {
      "key": "REQ-F-AUTH-002",
      "description": "User registration",
      "category": "functional",
      "priority": "high",
      "stage": "system_test",
      "coverage": {
        "scenarios": [
          {
            "id": "ST-010",
            "name": "Successful registration with valid data",
            "feature_file": "tests/features/system-test/authentication/registration.feature",
            "status": "passed",
            "duration_ms": 312
          }
        ],
        "scenario_count": 3,
        "passed_count": 3,
        "failed_count": 0,
        "coverage_percentage": 100.0
      }
    },
    {
      "key": "REQ-DATA-VAL-001",
      "description": "Email validation",
      "category": "data_quality",
      "priority": "medium",
      "stage": "system_test",
      "coverage": {
        "scenarios": [],
        "scenario_count": 0,
        "passed_count": 0,
        "failed_count": 0,
        "coverage_percentage": 0.0
      },
      "gaps": [
        {
          "type": "missing_tests",
          "severity": "error",
          "message": "No system test scenarios found for this requirement"
        }
      ]
    }
  ],
  "gaps": [
    {
      "requirement": "REQ-DATA-VAL-001",
      "issue": "No system test coverage",
      "severity": "error"
    },
    {
      "requirement": "REQ-NFR-PERF-002",
      "issue": "Only 1 scenario (minimum 2 required for NFR)",
      "severity": "warning"
    }
  ]
}
```

### 8.2 Coverage Matrix Generator Script

**File**: `tests/scripts/generate_coverage_matrix.py`

```python
#!/usr/bin/env python3
"""
Generate requirement coverage matrix from BDD test results.

# Implements: REQ-SYSTEST-003 (Traceability)

Usage:
    python generate_coverage_matrix.py
    python generate_coverage_matrix.py --output reports/coverage/
"""

import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict


# =============================================================================
# REQ Key Extraction
# =============================================================================

def extract_req_keys_from_feature(feature_file: Path) -> List[str]:
    """
    Extract REQ-* keys from feature file.

    # Implements: REQ-SYSTEST-003
    """
    content = feature_file.read_text()

    # Extract from comment header
    header_pattern = r'# Validates:\s+((?:REQ-[A-Z]+-[A-Z0-9]+-\d{3},?\s*)+)'
    header_match = re.search(header_pattern, content)

    # Extract from @tags
    tag_pattern = r'@(REQ-[A-Z]+-[A-Z0-9]+-\d{3})'
    tag_matches = re.findall(tag_pattern, content)

    req_keys = set()

    if header_match:
        keys = header_match.group(1).replace(' ', '').split(',')
        req_keys.update(keys)

    req_keys.update(tag_matches)

    return sorted(list(req_keys))


def extract_scenarios_from_feature(feature_file: Path) -> List[Dict[str, Any]]:
    """
    Extract scenario metadata from feature file.

    # Implements: REQ-SYSTEST-001
    """
    content = feature_file.read_text()
    scenarios = []

    # Pattern for scenarios
    scenario_pattern = r'@([\w-]+).*?\n\s+Scenario:\s+(.+?)$'

    for match in re.finditer(scenario_pattern, content, re.MULTILINE):
        tags = match.group(1)
        name = match.group(2)

        # Extract REQ keys from tags
        req_keys = re.findall(r'REQ-[A-Z]+-[A-Z0-9]+-\d{3}', tags)

        scenarios.append({
            'name': name.strip(),
            'tags': tags.split(),
            'req_keys': req_keys,
            'feature_file': str(feature_file)
        })

    return scenarios


# =============================================================================
# Test Results Parsing
# =============================================================================

def parse_pytest_junit_xml(junit_file: Path) -> Dict[str, Any]:
    """
    Parse pytest JUnit XML results.

    # Implements: REQ-SYSTEST-002
    """
    import xml.etree.ElementTree as ET

    tree = ET.parse(junit_file)
    root = tree.getroot()

    results = {}

    for testcase in root.iter('testcase'):
        name = testcase.get('name')
        classname = testcase.get('classname')
        time = float(testcase.get('time', 0))

        # Check for failure or error
        status = 'passed'
        error_msg = None

        if testcase.find('failure') is not None:
            status = 'failed'
            error_msg = testcase.find('failure').get('message')
        elif testcase.find('error') is not None:
            status = 'error'
            error_msg = testcase.find('error').get('message')

        results[name] = {
            'status': status,
            'duration_ms': int(time * 1000),
            'error': error_msg
        }

    return results


# =============================================================================
# Coverage Matrix Generation
# =============================================================================

def generate_coverage_matrix(
    features_dir: Path,
    requirements_file: Path,
    test_results_file: Path,
    output_dir: Path
):
    """
    Generate coverage matrix.

    # Implements: REQ-SYSTEST-003
    """

    # 1. Load requirements
    with open(requirements_file) as f:
        requirements = json.load(f)

    # 2. Load test results
    test_results = parse_pytest_junit_xml(test_results_file)

    # 3. Scan feature files
    req_coverage = defaultdict(lambda: {
        'scenarios': [],
        'scenario_count': 0,
        'passed_count': 0,
        'failed_count': 0
    })

    for feature_file in features_dir.rglob('*.feature'):
        req_keys = extract_req_keys_from_feature(feature_file)
        scenarios = extract_scenarios_from_feature(feature_file)

        for req_key in req_keys:
            for scenario in scenarios:
                if req_key in scenario['req_keys']:
                    # Find test result
                    test_name = scenario['name'].replace(' ', '_').lower()
                    result = test_results.get(test_name, {'status': 'unknown', 'duration_ms': 0})

                    req_coverage[req_key]['scenarios'].append({
                        'name': scenario['name'],
                        'feature_file': scenario['feature_file'],
                        'status': result['status'],
                        'duration_ms': result['duration_ms']
                    })

                    req_coverage[req_key]['scenario_count'] += 1

                    if result['status'] == 'passed':
                        req_coverage[req_key]['passed_count'] += 1
                    elif result['status'] == 'failed':
                        req_coverage[req_key]['failed_count'] += 1

    # 4. Build coverage report
    coverage_data = {
        'generated_at': datetime.now().isoformat(),
        'project': 'ai_sdlc_method',
        'stage': 'system_test',
        'summary': {
            'total_requirements': len(requirements),
            'requirements_with_tests': sum(1 for k in requirements if k in req_coverage and req_coverage[k]['scenario_count'] > 0),
            'requirements_without_tests': sum(1 for k in requirements if k not in req_coverage or req_coverage[k]['scenario_count'] == 0),
            'total_scenarios': sum(c['scenario_count'] for c in req_coverage.values()),
            'scenarios_passed': sum(c['passed_count'] for c in req_coverage.values()),
            'scenarios_failed': sum(c['failed_count'] for c in req_coverage.values())
        },
        'requirements': [],
        'gaps': []
    }

    # Coverage percentage
    if coverage_data['summary']['total_requirements'] > 0:
        coverage_data['summary']['coverage_percentage'] = round(
            100 * coverage_data['summary']['requirements_with_tests'] / coverage_data['summary']['total_requirements'],
            2
        )

    # 5. Build requirement details
    for req_key, req_data in requirements.items():
        coverage = req_coverage.get(req_key, {
            'scenarios': [],
            'scenario_count': 0,
            'passed_count': 0,
            'failed_count': 0
        })

        # Calculate coverage percentage
        if coverage['scenario_count'] > 0:
            coverage_pct = 100 * coverage['passed_count'] / coverage['scenario_count']
        else:
            coverage_pct = 0.0

        coverage['coverage_percentage'] = round(coverage_pct, 2)

        req_entry = {
            'key': req_key,
            'description': req_data.get('description', ''),
            'category': req_data.get('category', ''),
            'priority': req_data.get('priority', ''),
            'stage': 'system_test',
            'coverage': coverage
        }

        # Detect gaps
        if coverage['scenario_count'] == 0:
            req_entry['gaps'] = [{
                'type': 'missing_tests',
                'severity': 'error',
                'message': 'No system test scenarios found for this requirement'
            }]

            coverage_data['gaps'].append({
                'requirement': req_key,
                'issue': 'No system test coverage',
                'severity': 'error'
            })

        coverage_data['requirements'].append(req_entry)

    # 6. Write outputs
    output_dir.mkdir(parents=True, exist_ok=True)

    # JSON output
    json_file = output_dir / 'requirement_coverage.json'
    with open(json_file, 'w') as f:
        json.dump(coverage_data, f, indent=2)

    # Markdown output
    md_file = output_dir / 'requirement_coverage.md'
    generate_markdown_report(coverage_data, md_file)

    print(f"✓ Coverage matrix generated:")
    print(f"  - JSON: {json_file}")
    print(f"  - Markdown: {md_file}")
    print(f"\n📊 Summary:")
    print(f"  - Total requirements: {coverage_data['summary']['total_requirements']}")
    print(f"  - With tests: {coverage_data['summary']['requirements_with_tests']}")
    print(f"  - Coverage: {coverage_data['summary']['coverage_percentage']}%")


def generate_markdown_report(coverage_data: Dict[str, Any], output_file: Path):
    """
    Generate Markdown coverage report.

    # Implements: REQ-SYSTEST-003
    """

    lines = [
        "# System Test Coverage Report",
        "",
        f"**Generated**: {coverage_data['generated_at']}",
        f"**Project**: {coverage_data['project']}",
        f"**Stage**: {coverage_data['stage']}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- **Total Requirements**: {coverage_data['summary']['total_requirements']}",
        f"- **Requirements with Tests**: {coverage_data['summary']['requirements_with_tests']}",
        f"- **Requirements without Tests**: {coverage_data['summary']['requirements_without_tests']}",
        f"- **Total Scenarios**: {coverage_data['summary']['total_scenarios']}",
        f"- **Scenarios Passed**: {coverage_data['summary']['scenarios_passed']}",
        f"- **Scenarios Failed**: {coverage_data['summary']['scenarios_failed']}",
        f"- **Coverage**: {coverage_data['summary']['coverage_percentage']}%",
        "",
        "---",
        "",
        "## Coverage by Requirement",
        "",
        "| Requirement | Description | Priority | Scenarios | Passed | Failed | Coverage |",
        "|-------------|-------------|----------|-----------|--------|--------|----------|"
    ]

    for req in coverage_data['requirements']:
        cov = req['coverage']
        lines.append(
            f"| {req['key']} | {req['description'][:50]} | {req['priority']} | "
            f"{cov['scenario_count']} | {cov['passed_count']} | {cov['failed_count']} | "
            f"{cov['coverage_percentage']}% |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Gaps",
        ""
    ])

    if coverage_data['gaps']:
        lines.append("| Requirement | Issue | Severity |")
        lines.append("|-------------|-------|----------|")

        for gap in coverage_data['gaps']:
            lines.append(f"| {gap['requirement']} | {gap['issue']} | {gap['severity']} |")
    else:
        lines.append("**No gaps detected!** 🎉")

    output_file.write_text('\n'.join(lines))


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Generate requirement coverage matrix')
    parser.add_argument('--features', default='tests/features/system-test', help='Features directory')
    parser.add_argument('--requirements', default='docs/requirements/requirements.json', help='Requirements file')
    parser.add_argument('--results', default='tests/reports/test-results/junit.xml', help='Test results file')
    parser.add_argument('--output', default='tests/reports/coverage', help='Output directory')

    args = parser.parse_args()

    generate_coverage_matrix(
        features_dir=Path(args.features),
        requirements_file=Path(args.requirements),
        test_results_file=Path(args.results),
        output_dir=Path(args.output)
    )


if __name__ == '__main__':
    main()
```

### 8.3 HTML Coverage Dashboard

**File**: `tests/reports/coverage/generate_dashboard.py`

```python
#!/usr/bin/env python3
"""
Generate HTML coverage dashboard.

# Implements: REQ-SYSTEST-003
"""

import json
from pathlib import Path
from jinja2 import Template


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>System Test Coverage Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .summary { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px 20px; }
        .metric-value { font-size: 32px; font-weight: bold; color: #007bff; }
        .metric-label { font-size: 14px; color: #666; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #007bff; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .coverage-bar { height: 20px; background: #e0e0e0; border-radius: 3px; overflow: hidden; }
        .coverage-fill { height: 100%; background: #4caf50; }
        .coverage-low { background: #f44336; }
        .coverage-medium { background: #ff9800; }
        .gap { color: #f44336; font-weight: bold; }
    </style>
</head>
<body>
    <h1>System Test Coverage Dashboard</h1>

    <div class="summary">
        <div class="metric">
            <div class="metric-value">{{ summary.coverage_percentage }}%</div>
            <div class="metric-label">Coverage</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ summary.total_requirements }}</div>
            <div class="metric-label">Total Requirements</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ summary.requirements_with_tests }}</div>
            <div class="metric-label">With Tests</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ summary.total_scenarios }}</div>
            <div class="metric-label">Total Scenarios</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ summary.scenarios_passed }}</div>
            <div class="metric-label">Passed</div>
        </div>
    </div>

    <h2>Coverage by Requirement</h2>
    <table>
        <thead>
            <tr>
                <th>Requirement</th>
                <th>Description</th>
                <th>Priority</th>
                <th>Scenarios</th>
                <th>Coverage</th>
            </tr>
        </thead>
        <tbody>
            {% for req in requirements %}
            <tr>
                <td>{{ req.key }}</td>
                <td>{{ req.description }}</td>
                <td>{{ req.priority }}</td>
                <td>{{ req.coverage.scenario_count }}</td>
                <td>
                    <div class="coverage-bar">
                        <div class="coverage-fill {% if req.coverage.coverage_percentage < 50 %}coverage-low{% elif req.coverage.coverage_percentage < 80 %}coverage-medium{% endif %}"
                             style="width: {{ req.coverage.coverage_percentage }}%"></div>
                    </div>
                    {{ req.coverage.coverage_percentage }}%
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% if gaps %}
    <h2>Gaps</h2>
    <table>
        <thead>
            <tr>
                <th>Requirement</th>
                <th>Issue</th>
                <th>Severity</th>
            </tr>
        </thead>
        <tbody>
            {% for gap in gaps %}
            <tr>
                <td class="gap">{{ gap.requirement }}</td>
                <td>{{ gap.issue }}</td>
                <td>{{ gap.severity }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
</body>
</html>
"""


def generate_html_dashboard(coverage_file: Path, output_file: Path):
    """Generate HTML dashboard from coverage JSON."""

    with open(coverage_file) as f:
        coverage_data = json.load(f)

    template = Template(HTML_TEMPLATE)
    html = template.render(**coverage_data)

    output_file.write_text(html)
    print(f"✓ HTML dashboard generated: {output_file}")


if __name__ == '__main__':
    generate_html_dashboard(
        coverage_file=Path('requirement_coverage.json'),
        output_file=Path('coverage_matrix.html')
    )
```

---

## 9. Test-Requirement Linking

### 9.1 Linking Format Specification

**Primary linking method**: Comment headers + Gherkin tags

**Comment header** (mandatory):

```gherkin
# Validates: REQ-F-AUTH-001, REQ-NFR-SEC-001
```

**Gherkin tags** (recommended):

```gherkin
@REQ-F-AUTH-001 @REQ-NFR-SEC-001
```

### 9.2 Linking Extraction Algorithm

**Algorithm**: Extract REQ-* keys from feature files

```python
def extract_requirement_links(feature_file: Path) -> Dict[str, Any]:
    """
    Extract requirement links from feature file.

    # Implements: REQ-SYSTEST-003

    Returns:
        {
            'file': 'path/to/feature.feature',
            'feature_name': 'User Authentication',
            'requirements': ['REQ-F-AUTH-001', 'REQ-NFR-SEC-001'],
            'scenarios': [
                {
                    'name': 'Successful login',
                    'requirements': ['REQ-F-AUTH-001'],
                    'line_number': 15
                }
            ]
        }
    """
    content = feature_file.read_text()
    lines = content.split('\n')

    # Extract from comment header
    header_reqs = []
    for line in lines[:10]:  # Check first 10 lines
        if '# Validates:' in line:
            req_str = line.split('# Validates:')[1]
            header_reqs = [r.strip() for r in req_str.split(',')]
            break

    # Extract feature name
    feature_name = None
    feature_pattern = r'Feature:\s+(.+?)$'
    for line in lines:
        match = re.match(feature_pattern, line)
        if match:
            feature_name = match.group(1).strip()
            break

    # Extract scenario-level requirements
    scenarios = []
    for i, line in enumerate(lines):
        if 'Scenario:' in line:
            # Get tags from previous line(s)
            tags = []
            j = i - 1
            while j >= 0 and lines[j].strip().startswith('@'):
                tags.extend(lines[j].strip().split())
                j -= 1

            # Extract REQ keys from tags
            req_keys = [t[1:] for t in tags if t.startswith('@REQ-')]

            # Get scenario name
            scenario_name = line.split('Scenario:')[1].strip()

            scenarios.append({
                'name': scenario_name,
                'requirements': req_keys,
                'line_number': i + 1
            })

    return {
        'file': str(feature_file),
        'feature_name': feature_name,
        'requirements': header_reqs,
        'scenarios': scenarios
    }
```

### 9.3 Validation Rules

**Rule 1**: Every feature file must have at least one REQ-* key

**Rule 2**: REQ-* keys must match standard format (REQ-[F|NFR|DATA|BR]-[A-Z0-9]+-\d{3})

**Rule 3**: Every REQ-* key must exist in requirements documentation

**Rule 4**: Every scenario should validate at least one requirement

**Rule 5**: High-priority requirements must have ≥2 scenarios (positive + negative)

**Validation script**: `tests/scripts/validate_traceability.py`

```python
#!/usr/bin/env python3
"""
Validate test-requirement traceability.

# Implements: REQ-SYSTEST-003
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Any


REQ_KEY_PATTERN = re.compile(r'REQ-(?:F|NFR|DATA|BR)-[A-Z0-9]+-\d{3}')


def validate_feature_file(feature_file: Path, all_requirements: List[str]) -> List[Dict[str, Any]]:
    """
    Validate a single feature file.

    Returns list of validation errors.
    """
    errors = []
    content = feature_file.read_text()

    # Extract all REQ keys from file
    req_keys = REQ_KEY_PATTERN.findall(content)

    # Rule 1: At least one REQ key
    if not req_keys:
        errors.append({
            'file': str(feature_file),
            'rule': 'RULE-001',
            'severity': 'error',
            'message': 'No REQ-* keys found in feature file'
        })

    # Rule 3: All REQ keys must exist
    for req_key in req_keys:
        if req_key not in all_requirements:
            errors.append({
                'file': str(feature_file),
                'rule': 'RULE-003',
                'severity': 'error',
                'message': f'Requirement {req_key} not found in requirements documentation'
            })

    return errors


def validate_all_features(features_dir: Path, requirements_file: Path) -> int:
    """
    Validate all feature files.

    Returns exit code (0 = success, 1 = errors found).
    """
    # Load requirements
    import json
    with open(requirements_file) as f:
        requirements_data = json.load(f)

    all_requirements = list(requirements_data.keys())

    # Validate each feature file
    all_errors = []

    for feature_file in features_dir.rglob('*.feature'):
        errors = validate_feature_file(feature_file, all_requirements)
        all_errors.extend(errors)

    # Report results
    if all_errors:
        print("❌ Traceability validation FAILED\n")

        for error in all_errors:
            print(f"[{error['severity'].upper()}] {error['rule']}: {error['file']}")
            print(f"  {error['message']}\n")

        print(f"Total errors: {len(all_errors)}")
        return 1
    else:
        print("✓ Traceability validation PASSED")
        return 0


if __name__ == '__main__':
    exit_code = validate_all_features(
        features_dir=Path('tests/features/system-test'),
        requirements_file=Path('docs/requirements/requirements.json')
    )

    sys.exit(exit_code)
```

---

## 10. Quality Gates

### 10.1 System Test Quality Gate Checklist

**Before exiting System Test Stage:**

- [ ] **All BDD scenarios created** for functional requirements (REQ-F-*)
- [ ] **All scenarios executable** via pytest-bdd (no syntax errors)
- [ ] **≥90% scenario pass rate** (at least 90% of scenarios passing)
- [ ] **100% requirement coverage** (every requirement has ≥1 scenario)
- [ ] **High-priority requirements** have ≥2 scenarios each (positive + negative)
- [ ] **Traceability validation passed** (all REQ-* keys valid)
- [ ] **Coverage matrix generated** (JSON + Markdown reports exist)
- [ ] **No critical bugs** (no P0/P1 bugs found during testing)
- [ ] **Performance tests passed** (for REQ-NFR-PERF-* requirements)
- [ ] **Security tests passed** (for REQ-NFR-SEC-* requirements)
- [ ] **Test reports committed** to version control

### 10.2 Quality Gate Automation

**CI/CD Pipeline** (GitHub Actions):

**File**: `.github/workflows/system-test.yml`

```yaml
# System Test Stage - CI/CD Workflow
# Implements: REQ-SYSTEST-002

name: System Test Stage

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  system-test:
    name: Run System Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt

      - name: Run System Tests
        run: |
          cd tests/features
          pytest -v --junit-xml=../../reports/test-results/junit.xml \
                    --html=../../reports/test-results/report.html \
                    --self-contained-html

      - name: Generate Coverage Matrix
        run: |
          python tests/scripts/generate_coverage_matrix.py

      - name: Validate Traceability
        run: |
          python tests/scripts/validate_traceability.py

      - name: Check Quality Gate
        run: |
          python tests/scripts/check_quality_gate.py

      - name: Upload Test Reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: system-test-reports
          path: |
            reports/test-results/
            reports/coverage/

      - name: Comment PR with Coverage
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const coverage = JSON.parse(fs.readFileSync('reports/coverage/requirement_coverage.json'));

            const comment = `## System Test Coverage Report

            - **Coverage**: ${coverage.summary.coverage_percentage}%
            - **Requirements with Tests**: ${coverage.summary.requirements_with_tests}/${coverage.summary.total_requirements}
            - **Scenarios Passed**: ${coverage.summary.scenarios_passed}/${coverage.summary.total_scenarios}

            ${coverage.gaps.length > 0 ? '⚠️ **Gaps Found**: ' + coverage.gaps.length : '✅ **No Gaps**'}
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

**Quality Gate Check Script**:

**File**: `tests/scripts/check_quality_gate.py`

```python
#!/usr/bin/env python3
"""
Check System Test Stage quality gate.

# Implements: REQ-SYSTEST-002, REQ-SYSTEST-003
"""

import json
import sys
from pathlib import Path


def check_quality_gate(coverage_file: Path, thresholds: dict) -> int:
    """
    Check if quality gate criteria are met.

    Returns:
        0 if passed, 1 if failed
    """
    with open(coverage_file) as f:
        coverage = json.load(f)

    summary = coverage['summary']
    failures = []

    # Check coverage percentage
    if summary['coverage_percentage'] < thresholds['min_coverage']:
        failures.append(
            f"Coverage {summary['coverage_percentage']}% "
            f"< threshold {thresholds['min_coverage']}%"
        )

    # Check scenario pass rate
    total_scenarios = summary['total_scenarios']
    passed_scenarios = summary['scenarios_passed']

    if total_scenarios > 0:
        pass_rate = 100 * passed_scenarios / total_scenarios

        if pass_rate < thresholds['min_pass_rate']:
            failures.append(
                f"Scenario pass rate {pass_rate:.1f}% "
                f"< threshold {thresholds['min_pass_rate']}%"
            )

    # Check for critical gaps
    critical_gaps = [g for g in coverage.get('gaps', []) if g['severity'] == 'error']

    if critical_gaps:
        failures.append(f"Found {len(critical_gaps)} critical gaps")

    # Report results
    if failures:
        print("❌ Quality Gate FAILED\n")

        for failure in failures:
            print(f"  - {failure}")

        return 1
    else:
        print("✅ Quality Gate PASSED")
        print(f"  - Coverage: {summary['coverage_percentage']}%")
        print(f"  - Scenarios: {passed_scenarios}/{total_scenarios} passed")

        return 0


if __name__ == '__main__':
    thresholds = {
        'min_coverage': 90.0,     # 90% requirement coverage
        'min_pass_rate': 90.0     # 90% scenario pass rate
    }

    exit_code = check_quality_gate(
        coverage_file=Path('reports/coverage/requirement_coverage.json'),
        thresholds=thresholds
    )

    sys.exit(exit_code)
```

---

## 11. Implementation Guidance

### 11.1 Implementation Phases

**Phase 1: Setup (Week 1)**
- [ ] Install pytest-bdd and dependencies
- [ ] Configure pytest.ini
- [ ] Create directory structure
- [ ] Setup conftest.py with basic fixtures
- [ ] Create first feature file (smoke test)

**Phase 2: Core Scenarios (Week 2-3)**
- [ ] Write feature files for all functional requirements
- [ ] Implement step definitions
- [ ] Create page objects / API clients
- [ ] Run first test suite execution

**Phase 3: Coverage & Traceability (Week 4)**
- [ ] Implement coverage matrix generator
- [ ] Add REQ-* tags to all scenarios
- [ ] Generate initial coverage report
- [ ] Fix gaps

**Phase 4: Automation & CI/CD (Week 5)**
- [ ] Setup GitHub Actions workflow
- [ ] Implement quality gate checks
- [ ] Configure automatic report generation
- [ ] Test full pipeline

**Phase 5: Advanced Testing (Week 6)**
- [ ] Add performance tests (REQ-NFR-PERF-*)
- [ ] Add security tests (REQ-NFR-SEC-*)
- [ ] Add data validation tests (REQ-DATA-*)
- [ ] Optimize test execution time

### 11.2 Development Workflow

**Daily workflow for QA Engineer:**

1. **Morning**: Check which requirements need test coverage
2. **Write scenarios**: Create feature files with REQ tags
3. **Implement steps**: Write step definitions in Python
4. **Run tests locally**: `pytest -v`
5. **Generate coverage**: `python generate_coverage_matrix.py`
6. **Fix failures**: Debug and fix failing scenarios
7. **Commit**: Push to version control
8. **CI/CD runs**: Automatic validation

### 11.3 Integration with Other Stages

**From Code Stage (Stage 4)**:
- **Input**: Deployed code, API endpoints, UI components
- **Action**: Write integration tests validating end-to-end flows

**To UAT Stage (Stage 6)**:
- **Output**: System test results, coverage report
- **Handoff**: Only proceed if quality gate passed

### 11.4 Common Pitfalls

**Pitfall 1**: Writing scenarios without REQ tags
- **Solution**: Use linter to enforce REQ tag presence

**Pitfall 2**: Step definitions too specific (not reusable)
- **Solution**: Use parametrized steps with parsers.parse()

**Pitfall 3**: Tests depend on execution order
- **Solution**: Each scenario must be independent (setup in Background/Given)

**Pitfall 4**: Hardcoded test data
- **Solution**: Use fixtures and data factories

**Pitfall 5**: Ignoring failing tests
- **Solution**: Enforce quality gate in CI/CD

---

## 12. Examples

### 12.1 Complete Example: Authentication Feature

**Feature File**: `tests/features/system-test/authentication/login.feature`

```gherkin
# Validates: REQ-F-AUTH-001, REQ-NFR-PERF-001, REQ-NFR-SEC-001
# Stage: System Test (Stage 5)
# Priority: High
# Owner: QA Team
# Created: 2025-12-03

@system-test @authentication @REQ-F-AUTH-001
Feature: User Authentication
  As a registered user
  I want to log in with my email and password
  So that I can access my account securely

  Background:
    Given the authentication service is running
    And a user with email "test@example.com" and password "SecurePass123" exists
    And the user account is active

  @happy-path @ST-001 @REQ-F-AUTH-001
  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter email "test@example.com"
    And I enter password "SecurePass123"
    And I click the "Login" button
    Then I should be redirected to the dashboard
    And I should see a welcome message "Welcome, Test User!"
    And a session token should be created
    And the session token should be valid for 24 hours

  @error-handling @ST-002 @REQ-F-AUTH-001
  Scenario: Failed login with invalid password
    Given I am on the login page
    When I enter email "test@example.com"
    And I enter password "WrongPassword"
    And I click the "Login" button
    Then I should see an error message "Invalid email or password"
    And I should remain on the login page
    And no session token should be created

  @error-handling @ST-003 @REQ-F-AUTH-001
  Scenario: Failed login with non-existent email
    Given I am on the login page
    When I enter email "nonexistent@example.com"
    And I enter password "AnyPassword"
    And I click the "Login" button
    Then I should see an error message "Invalid email or password"
    And I should remain on the login page

  @performance @ST-004 @REQ-NFR-PERF-001
  Scenario: Login response time under normal load
    Given the system is under normal load
    When I submit login credentials for "test@example.com"
    Then the response should be received within 500 milliseconds
    And the response should contain a valid session token

  @security @ST-005 @REQ-NFR-SEC-001
  Scenario: Login enforces HTTPS
    Given I attempt to connect via HTTP
    When I try to access the login endpoint
    Then I should be automatically redirected to HTTPS

  @security @ST-006 @REQ-NFR-SEC-001
  Scenario: Login rate limiting prevents brute force
    Given I have made 5 failed login attempts in the last minute
    When I attempt another login
    Then I should see an error message "Too many login attempts. Please try again later."
    And I should be blocked for 5 minutes
```

**Step Definitions**: `tests/features/steps/authentication_steps.py`

(See Section 4.1 for full implementation)

**Test Execution**:

```bash
$ cd tests/features
$ pytest -v -m REQ-F-AUTH-001

============================= test session starts ==============================
platform darwin -- Python 3.11.5, pytest-7.4.3, pluggy-1.3.0
collected 6 items

test_authentication.py::test_successful_login PASSED                     [ 16%]
test_authentication.py::test_failed_login_invalid_password PASSED        [ 33%]
test_authentication.py::test_failed_login_nonexistent_email PASSED       [ 50%]
test_authentication.py::test_login_performance PASSED                    [ 66%]
test_authentication.py::test_login_enforces_https PASSED                 [ 83%]
test_authentication.py::test_login_rate_limiting PASSED                  [100%]

============================== 6 passed in 2.14s ===============================
```

**Coverage Report**:

```
Requirement Coverage: REQ-F-AUTH-001
  Scenarios: 6
  Passed: 6
  Failed: 0
  Coverage: 100%
```

---

## Appendix A: REQ Tag Format Reference

| Tag Format | Example | Description |
|------------|---------|-------------|
| `REQ-F-<AREA>-NNN` | `REQ-F-AUTH-001` | Functional requirement |
| `REQ-NFR-<TYPE>-NNN` | `REQ-NFR-PERF-001` | Non-functional requirement |
| `REQ-DATA-<TYPE>-NNN` | `REQ-DATA-VAL-001` | Data quality requirement |
| `REQ-BR-<AREA>-NNN` | `REQ-BR-PRICE-001` | Business rule |

**Naming conventions**:
- `<AREA>`: AUTH, USER, PRODUCT, ORDER, PAYMENT, etc.
- `<TYPE>`: PERF, SEC, SCALE, AVAIL, VAL, INT, etc.
- `NNN`: Zero-padded 3-digit number (001-999)

---

## Appendix B: Useful pytest-bdd Commands

| Command | Description |
|---------|-------------|
| `pytest --feature <file>` | Run specific feature file |
| `pytest -m <tag>` | Run tests with specific marker |
| `pytest -k <pattern>` | Run tests matching name pattern |
| `pytest -v` | Verbose output |
| `pytest -s` | Show print statements |
| `pytest --pdb` | Drop into debugger on failure |
| `pytest -n auto` | Parallel execution (requires pytest-xdist) |
| `pytest --lf` | Run last failed tests |
| `pytest --ff` | Run failed tests first |

---

## Appendix C: CI/CD Integration Checklist

- [ ] GitHub Actions workflow configured
- [ ] Test execution on every commit
- [ ] Coverage report generation automated
- [ ] Traceability validation automated
- [ ] Quality gate enforcement
- [ ] Test reports uploaded as artifacts
- [ ] PR comments with coverage summary
- [ ] Failure notifications (email/Slack)
- [ ] Performance test thresholds configured
- [ ] Security scan integration

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-03 | AISDLC Design Agent | Initial design document |

---

**Next Steps**

1. Review this design with QA team
2. Create ADR for pytest-bdd vs behave decision
3. Implement Phase 1 (setup) from Section 11.1
4. Create first smoke test feature file
5. Generate initial coverage matrix

---

**Mantra**: "Every test validates a requirement, every requirement has tests, quality is enforced automatically" 🎯
