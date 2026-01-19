# REQ-* Tagging Rule

**Version**: 1.0
**Date**: 2026-01-20
**Purpose**: Define requirement key format and usage across all SDLC artifacts
**Implements**: REQ-ROO-RULE-003

---

## Overview

This rule defines the **requirement key format** (REQ-*) and **tagging practices** for achieving complete traceability from intent through runtime. Every artifact in the SDLC - requirements, design, tasks, code, tests, commits, matrix - must reference the REQ-* keys it implements or validates.

**Core Principle**: **"No artifact without traceability"**

---

## REQ Key Format

```
REQ-{TYPE}-{DOMAIN}-{SEQ}
```

### Components

#### TYPE: Requirement Category

- **`F`** - Functional requirement (features, behavior, user-facing functionality)
- **`NFR`** - Non-functional requirement (performance, security, usability, reliability, scalability)
- **`DATA`** - Data quality requirement (accuracy, completeness, consistency, validation)
- **`BR`** - Business rule (constraints, policies, calculations, domain logic)

#### DOMAIN: Functional Area

- **Format**: 2-8 uppercase letters
- **Purpose**: Groups related requirements
- **Examples**:
  - `AUTH` - Authentication and authorization
  - `USER` - User management
  - `PAY` - Payments and billing
  - `REPORT` - Reporting and analytics
  - `ADMIN` - Administration
  - `API` - API functionality
  - `PERF` - Performance
  - `SEC` - Security
  - `TRACE` - Traceability
  - `REFINE` - Iterative refinement
- **Rule**: Use consistent naming within project

#### SEQ: Sequence Number

- **Format**: 3 digits, zero-padded (001, 002, ..., 999)
- **Start**: 001 for each domain
- **Increment**: Sequential within domain
- **Immutability**: **Never reuse keys** (even if requirement deleted)

---

### Valid Examples

```
REQ-F-AUTH-001        # User login with email/password
REQ-F-AUTH-002        # User logout
REQ-F-USER-001        # User profile creation
REQ-NFR-PERF-001      # Login response time < 500ms
REQ-NFR-SEC-001       # Passwords hashed with bcrypt
REQ-DATA-USER-001     # Email must be valid format
REQ-BR-PAY-001        # Refunds within 30 days only
```

### Invalid Examples

```
❌ REQ-AUTH-1          # Missing TYPE, sequence not zero-padded
❌ REQ-F-1             # Missing DOMAIN
❌ req-f-auth-001      # Wrong case (must be uppercase)
❌ REQ-F-AUTH          # Missing SEQ
❌ REQ-FUNC-AUTH-001   # Invalid TYPE (use F, not FUNC)
```

---

## Where to Use REQ Tags

### 1. Requirements Documents

**Location**: `docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`

**Format**:

```markdown
## REQ-F-AUTH-001: User Login

**Type**: Functional
**Priority**: Critical
**Release**: 1.0

**Description**:
System shall allow users to authenticate using email and password.

**Acceptance Criteria**:
1. User can enter email address (valid format per REQ-DATA-USER-001)
2. User can enter password (minimum 8 characters)
3. System validates credentials against database
4. Successful login redirects to dashboard
5. Failed login displays error message (3 attempts max per REQ-BR-AUTH-001)
6. Response time < 500ms (per REQ-NFR-PERF-001)

**Source**: INTENT-001 (Customer self-service portal)
**Dependencies**: None
**Stakeholders**: Product Owner, End Users
```

---

### 2. Design Documents

**Location**: `docs/design/{variant}_aisdlc/AISDLC_IMPLEMENTATION_DESIGN.md`

**Format**:

```markdown
## Component: AuthenticationService

**Purpose**: Handle user authentication workflows

**Implements**:
- REQ-F-AUTH-001 (User Login)
- REQ-F-AUTH-002 (User Logout)
- REQ-NFR-PERF-001 (Login Performance)
- REQ-NFR-SEC-001 (Password Security)

**Architecture**:

### Methods

#### login(email, password) → LoginResult
**Implements**: REQ-F-AUTH-001
- Validates email format (REQ-DATA-USER-001)
- Checks password against bcrypt hash (REQ-NFR-SEC-001)
- Enforces rate limiting (REQ-BR-AUTH-001)
- Returns result in < 500ms (REQ-NFR-PERF-001)

#### logout(session_id) → void
**Implements**: REQ-F-AUTH-002
- Invalidates session token
- Clears session cache
```

**ADR Example**:

```markdown
# ADR-003: Use bcrypt for Password Hashing

**Status**: Accepted
**Date**: 2026-01-20
**Implements**: REQ-NFR-SEC-001

## Context
Need secure password storage per REQ-NFR-SEC-001 (bcrypt hashing requirement).

## Decision
Use bcrypt algorithm with work factor 12 for all password hashing operations.

## Consequences
**Positive**:
- Meets REQ-NFR-SEC-001 security requirement
- Industry standard, well-tested
- Adaptive cost (future-proof)

**Negative**:
- Slower than SHA-256 (by design)
- Impacts REQ-NFR-PERF-001 login performance (acceptable: 120ms vs target 500ms)

## Requirements Addressed
- REQ-NFR-SEC-001: Secure password hashing
```

---

### 3. Task Descriptions

**Location**: `.ai-workspace/tasks/active/ACTIVE_TASKS.md`

**Format**:

```markdown
## TASK-AUTH-001: Implement User Login

**Priority**: Critical
**Status**: In Progress
**Estimated**: 5 hours

**Implements**:
- REQ-F-AUTH-001 (User Login)
- REQ-NFR-PERF-001 (Login Performance)
- REQ-NFR-SEC-001 (Password Security)

**Description**:
Implement login functionality with email/password authentication using TDD approach.

**Acceptance Criteria**:
- All criteria from REQ-F-AUTH-001 met
- Performance threshold from REQ-NFR-PERF-001 achieved (< 500ms)
- Security requirement from REQ-NFR-SEC-001 met (bcrypt hashing)
- Test coverage ≥ 80%
- All tests passing

**Dependencies**:
- TASK-USER-001 (User model) - completed

**Sub-tasks**:
1. Write failing test for valid credentials (RED)
2. Implement minimal login logic (GREEN)
3. Refactor for quality (REFACTOR)
4. Add error handling and edge cases
5. Verify performance requirements
6. Update traceability matrix
```

---

### 4. Code Comments

#### Python Examples

**Production Code**:

```python
# src/auth/service.py

# Implements: REQ-F-AUTH-001, REQ-NFR-PERF-001, REQ-NFR-SEC-001
class AuthenticationService:
    """Handle user authentication workflows.

    Implements:
    - REQ-F-AUTH-001: User Login
    - REQ-NFR-PERF-001: Login Performance (< 500ms)
    - REQ-NFR-SEC-001: Password Security (bcrypt)
    """

    # Implements: REQ-F-AUTH-001
    def login(self, email: str, password: str) -> LoginResult:
        """Authenticate user with email and password.

        Args:
            email: User email address (validated per REQ-DATA-USER-001)
            password: User password (plaintext, will be hashed)

        Returns:
            LoginResult with success flag, user object, or error message

        Raises:
            ValueError: If email format invalid (REQ-DATA-USER-001)
            AuthenticationError: If credentials invalid
            RateLimitError: If too many attempts (REQ-BR-AUTH-001)

        Implements: REQ-F-AUTH-001
        Performance: < 500ms (REQ-NFR-PERF-001)
        Security: bcrypt hashing (REQ-NFR-SEC-001)
        """
        start_time = time.time()

        # Validate email format (REQ-DATA-USER-001)
        if not self._is_valid_email(email):
            raise ValueError("Invalid email format")

        # Check rate limiting (REQ-BR-AUTH-001)
        if self._is_rate_limited(email):
            raise RateLimitError("Too many login attempts")

        # Find user
        user = self.user_repository.get_by_email(email)

        # Verify password with bcrypt (REQ-NFR-SEC-001)
        if user and bcrypt.verify(password, user.password_hash):
            # Check performance target (REQ-NFR-PERF-001)
            elapsed_ms = (time.time() - start_time) * 1000
            self.metrics.record("login_duration_ms", elapsed_ms)

            return LoginResult(success=True, user=user)

        # Record failed attempt (REQ-BR-AUTH-001)
        self._record_failed_attempt(email)

        return LoginResult(success=False, error="Invalid credentials")

    # Implements: REQ-DATA-USER-001
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format per REQ-DATA-USER-001."""
        return email_regex.match(email) is not None

    # Implements: REQ-BR-AUTH-001
    def _is_rate_limited(self, email: str) -> bool:
        """Check if user is rate limited (3 attempts per REQ-BR-AUTH-001)."""
        attempts = self.cache.get(f"login_attempts:{email}", 0)
        return attempts >= 3
```

**Test Code**:

```python
# tests/auth/test_service.py

# Validates: REQ-F-AUTH-001
class TestAuthentication:
    """Test authentication functionality.

    Validates: REQ-F-AUTH-001 (User Login)
    """

    # Validates: REQ-F-AUTH-001
    def test_login_with_valid_credentials(self):
        """Test successful login with valid email and password.

        Validates: REQ-F-AUTH-001 - Acceptance Criteria 1, 2, 3, 4
        """
        # Arrange
        user = create_test_user(
            email="test@example.com",
            password="password123"
        )
        service = AuthenticationService()

        # Act
        result = service.login("test@example.com", "password123")

        # Assert
        assert result.success == True
        assert result.user.email == "test@example.com"

    # Validates: REQ-F-AUTH-001
    def test_login_with_invalid_password(self):
        """Test failed login with wrong password.

        Validates: REQ-F-AUTH-001 - Acceptance Criterion 5 (error handling)
        """
        # Arrange
        user = create_test_user(
            email="test@example.com",
            password="password123"
        )
        service = AuthenticationService()

        # Act
        result = service.login("test@example.com", "wrong_password")

        # Assert
        assert result.success == False
        assert result.error == "Invalid credentials"

    # Validates: REQ-DATA-USER-001
    def test_login_with_invalid_email_format(self):
        """Test login rejects invalid email format.

        Validates: REQ-DATA-USER-001 (email validation)
        """
        service = AuthenticationService()

        with pytest.raises(ValueError, match="Invalid email format"):
            service.login("not-an-email", "password123")

    # Validates: REQ-NFR-PERF-001
    def test_login_performance(self):
        """Test login completes within performance threshold.

        Validates: REQ-NFR-PERF-001 (< 500ms response time)
        """
        user = create_test_user(
            email="test@example.com",
            password="password123"
        )
        service = AuthenticationService()

        start = time.time()
        result = service.login("test@example.com", "password123")
        elapsed_ms = (time.time() - start) * 1000

        assert result.success == True
        assert elapsed_ms < 500, f"Login took {elapsed_ms}ms (limit: 500ms)"

    # Validates: REQ-BR-AUTH-001
    def test_login_rate_limiting(self):
        """Test login enforces rate limiting after 3 failed attempts.

        Validates: REQ-BR-AUTH-001 (3 attempts max)
        """
        service = AuthenticationService()
        email = "test@example.com"

        # First 3 attempts should work
        for i in range(3):
            result = service.login(email, "wrong_password")
            assert result.success == False

        # 4th attempt should raise rate limit error
        with pytest.raises(RateLimitError, match="Too many login attempts"):
            service.login(email, "wrong_password")

    # Validates: REQ-NFR-SEC-001
    def test_password_stored_as_bcrypt_hash(self):
        """Test passwords stored with bcrypt hashing.

        Validates: REQ-NFR-SEC-001 (bcrypt password hashing)
        """
        user = create_test_user(
            email="test@example.com",
            password="password123"
        )

        # Verify password hash format (bcrypt starts with $2b$)
        assert user.password_hash.startswith("$2b$")

        # Verify bcrypt work factor (should be 12)
        assert user.password_hash.startswith("$2b$12$")
```

#### TypeScript/JavaScript Examples

**Production Code**:

```typescript
// src/auth/AuthenticationService.ts

// Implements: REQ-F-AUTH-001, REQ-NFR-PERF-001, REQ-NFR-SEC-001
export class AuthenticationService {
  /**
   * Handle user authentication workflows.
   *
   * Implements:
   * - REQ-F-AUTH-001: User Login
   * - REQ-NFR-PERF-001: Login Performance (< 500ms)
   * - REQ-NFR-SEC-001: Password Security (bcrypt)
   */

  // Implements: REQ-F-AUTH-001
  async login(email: string, password: string): Promise<LoginResult> {
    /**
     * Authenticate user with email and password.
     *
     * @param email - User email address (validated per REQ-DATA-USER-001)
     * @param password - User password (plaintext)
     * @returns LoginResult with success flag and user object
     * @throws ValueError if email format invalid (REQ-DATA-USER-001)
     * @throws RateLimitError if too many attempts (REQ-BR-AUTH-001)
     *
     * Implements: REQ-F-AUTH-001
     * Performance: < 500ms (REQ-NFR-PERF-001)
     * Security: bcrypt hashing (REQ-NFR-SEC-001)
     */
    const startTime = Date.now();

    // Validate email format (REQ-DATA-USER-001)
    if (!this.isValidEmail(email)) {
      throw new ValueError("Invalid email format");
    }

    // Check rate limiting (REQ-BR-AUTH-001)
    if (await this.isRateLimited(email)) {
      throw new RateLimitError("Too many login attempts");
    }

    // Find user
    const user = await this.userRepository.getByEmail(email);

    // Verify password with bcrypt (REQ-NFR-SEC-001)
    if (user && await bcrypt.compare(password, user.passwordHash)) {
      // Check performance target (REQ-NFR-PERF-001)
      const elapsedMs = Date.now() - startTime;
      this.metrics.record("login_duration_ms", elapsedMs);

      return { success: true, user };
    }

    // Record failed attempt (REQ-BR-AUTH-001)
    await this.recordFailedAttempt(email);

    return { success: false, error: "Invalid credentials" };
  }

  // Implements: REQ-DATA-USER-001
  private isValidEmail(email: string): boolean {
    /**
     * Validate email format per REQ-DATA-USER-001.
     */
    return EMAIL_REGEX.test(email);
  }

  // Implements: REQ-BR-AUTH-001
  private async isRateLimited(email: string): Promise<boolean> {
    /**
     * Check if user is rate limited (3 attempts per REQ-BR-AUTH-001).
     */
    const attempts = await this.cache.get(`login_attempts:${email}`) || 0;
    return attempts >= 3;
  }
}
```

**Test Code**:

```typescript
// tests/auth/AuthenticationService.test.ts

// Validates: REQ-F-AUTH-001
describe('AuthenticationService', () => {
  /**
   * Test authentication functionality.
   * Validates: REQ-F-AUTH-001 (User Login)
   */

  // Validates: REQ-F-AUTH-001
  it('should login with valid credentials', async () => {
    /**
     * Test successful login with valid email and password.
     * Validates: REQ-F-AUTH-001 - Acceptance Criteria 1, 2, 3, 4
     */
    // Arrange
    const user = await createTestUser({
      email: 'test@example.com',
      password: 'password123'
    });
    const service = new AuthenticationService();

    // Act
    const result = await service.login('test@example.com', 'password123');

    // Assert
    expect(result.success).toBe(true);
    expect(result.user?.email).toBe('test@example.com');
  });

  // Validates: REQ-F-AUTH-001
  it('should fail login with invalid password', async () => {
    /**
     * Test failed login with wrong password.
     * Validates: REQ-F-AUTH-001 - Acceptance Criterion 5 (error handling)
     */
    // Arrange
    await createTestUser({
      email: 'test@example.com',
      password: 'password123'
    });
    const service = new AuthenticationService();

    // Act
    const result = await service.login('test@example.com', 'wrong_password');

    // Assert
    expect(result.success).toBe(false);
    expect(result.error).toBe('Invalid credentials');
  });

  // Validates: REQ-NFR-PERF-001
  it('should complete login within 500ms', async () => {
    /**
     * Test login completes within performance threshold.
     * Validates: REQ-NFR-PERF-001 (< 500ms response time)
     */
    const user = await createTestUser({
      email: 'test@example.com',
      password: 'password123'
    });
    const service = new AuthenticationService();

    const start = Date.now();
    const result = await service.login('test@example.com', 'password123');
    const elapsedMs = Date.now() - start;

    expect(result.success).toBe(true);
    expect(elapsedMs).toBeLessThan(500);
  });
});
```

---

### 5. Commit Messages

**Format**:

```
<action> <description> (<REQ-KEY>)

<detailed description>

Implements: <REQ-KEY-1>, <REQ-KEY-2>
Validates: <REQ-KEY-1>, <REQ-KEY-2>
```

**Examples**:

```
Implement user login (REQ-F-AUTH-001)

Add authentication service with email/password login:
- Implement login() with email validation
- Add bcrypt password hashing
- Add rate limiting (3 attempts max)
- Add performance monitoring
- Add unit tests for happy path and error cases

Performance: < 500ms (meets REQ-NFR-PERF-001)
Security: bcrypt work factor 12 (meets REQ-NFR-SEC-001)
Rate limiting: 3 attempts (meets REQ-BR-AUTH-001)

Implements: REQ-F-AUTH-001, REQ-NFR-PERF-001, REQ-NFR-SEC-001
Validates: REQ-F-AUTH-001, REQ-NFR-PERF-001, REQ-NFR-SEC-001, REQ-BR-AUTH-001
```

```
Refactor authentication for modularity (REQ-F-AUTH-001)

Extract email validation and rate limiting to separate methods:
- Extract _is_valid_email() for REQ-DATA-USER-001
- Extract _is_rate_limited() for REQ-BR-AUTH-001
- Add comprehensive docstrings with REQ-* references
- Improve test coverage to 92%

No functional changes, all tests passing.

Implements: REQ-F-AUTH-001, REQ-DATA-USER-001, REQ-BR-AUTH-001
```

```
Fix login performance regression (REQ-NFR-PERF-001)

Optimize database query to reduce login latency:
- Add index on users.email column
- Cache bcrypt work factor
- Reduce database connection overhead

Performance improved: 650ms → 280ms (now meets < 500ms target)

Implements: REQ-NFR-PERF-001
```

---

### 6. BDD Feature Files

**Location**: `tests/features/*.feature`

**Format**:

```gherkin
Feature: User Authentication
  # Validates: REQ-F-AUTH-001, REQ-NFR-PERF-001

  As a user
  I want to log in with email and password
  So that I can access my account

  Background:
    Given a user exists with email "user@example.com" and password "password123"

  # Validates: REQ-F-AUTH-001
  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter email "user@example.com"
    And I enter password "password123"
    And I click "Login"
    Then I should be redirected to the dashboard
    And I should see "Welcome back"

  # Validates: REQ-F-AUTH-001
  Scenario: Failed login with invalid password
    Given I am on the login page
    When I enter email "user@example.com"
    And I enter password "wrong_password"
    And I click "Login"
    Then I should see error message "Invalid credentials"
    And I should remain on the login page

  # Validates: REQ-DATA-USER-001
  Scenario: Failed login with invalid email format
    Given I am on the login page
    When I enter email "not-an-email"
    And I enter password "password123"
    And I click "Login"
    Then I should see error message "Invalid email format"

  # Validates: REQ-BR-AUTH-001
  Scenario: Rate limiting after 3 failed attempts
    Given I am on the login page
    When I attempt login 3 times with wrong password
    And I attempt login again
    Then I should see error message "Too many login attempts"
    And I should be temporarily locked out

  # Validates: REQ-NFR-PERF-001
  @performance
  Scenario: Login completes within 500ms
    Given I am on the login page
    When I enter valid credentials and click "Login"
    Then the response should complete in less than 500ms
```

---

### 7. Traceability Matrix

**Location**: `docs/TRACEABILITY_MATRIX.md`

**Format**:

```markdown
| Requirement | Design | Tasks | Code | Tests | Status |
|-------------|--------|-------|------|-------|--------|
| REQ-F-AUTH-001 | AuthenticationService.login() | TASK-AUTH-001 | src/auth/service.py:45 | tests/auth/test_service.py:12 | ✅ Implemented |
| REQ-F-AUTH-002 | AuthenticationService.logout() | TASK-AUTH-002 | src/auth/service.py:78 | tests/auth/test_service.py:98 | 🚧 In Progress |
| REQ-NFR-PERF-001 | Performance monitoring | TASK-AUTH-001 | src/auth/service.py:45 | tests/auth/test_service.py:87 | ✅ Implemented |
| REQ-NFR-SEC-001 | bcrypt hashing | TASK-AUTH-001 | src/auth/service.py:62 | tests/auth/test_service.py:134 | ✅ Implemented |
| REQ-DATA-USER-001 | Email validation | TASK-AUTH-001 | src/auth/service.py:101 | tests/auth/test_service.py:67 | ✅ Implemented |
| REQ-BR-AUTH-001 | Rate limiting | TASK-AUTH-001 | src/auth/service.py:108 | tests/auth/test_service.py:112 | ✅ Implemented |
```

---

## Validation Checklist

Before committing any artifact, verify:

- [ ] **REQ-* tag is present** - Every artifact has at least one REQ-* tag
- [ ] **REQ-* tag follows correct format** - `REQ-{TYPE}-{DOMAIN}-{SEQ}`
- [ ] **TYPE is valid** - One of: F, NFR, DATA, BR
- [ ] **DOMAIN is consistent** - Matches project naming conventions
- [ ] **SEQ is zero-padded** - 001, 002, not 1, 2
- [ ] **REQ-* tag is traceable** - Tag exists in requirements document
- [ ] **REQ-* tag is unique** - No duplicate keys
- [ ] **REQ-* tag is immutable** - Never changed after creation
- [ ] **Traceability matrix updated** - Entry exists for this requirement

---

## Enforcement

This rule is loaded by **ALL modes** via `@rules/req-tagging.md`.

### Agent Responsibilities

All agents must:

1. **Validate format** when creating new REQ-* keys
2. **Propagate tags** to all downstream artifacts
3. **Check traceability** before marking work complete
4. **Reject** artifacts without proper REQ-* tags
5. **Update traceability matrix** when adding or modifying REQ-* tags

### Automated Validation

The traceability validator (`validate_traceability.py`) checks:

- All REQ-* keys in requirements doc are unique and valid format
- All code has `# Implements: REQ-*` tags
- All tests have `# Validates: REQ-*` tags
- All REQ-* tags reference existing requirements
- Traceability matrix is up-to-date
- No orphaned tags (tags without corresponding requirement)

---

## Complete Examples by Artifact Type

### Requirements Document Example

```markdown
# Authentication Requirements

## Functional Requirements

### REQ-F-AUTH-001: User Login

**Type**: Functional
**Priority**: Critical
**Release**: 1.0
**Phase**: 1

**Description**:
System shall allow users to authenticate using email and password.

**Acceptance Criteria**:
1. User can enter email address (valid format per REQ-DATA-USER-001)
2. User can enter password (minimum 8 characters)
3. System validates credentials against database
4. Successful login redirects to dashboard
5. Failed login displays error message
6. Response time < 500ms (per REQ-NFR-PERF-001)

**Source**: INTENT-001 (Customer self-service portal)
**Dependencies**:
- REQ-DATA-USER-001 (Email validation)
- REQ-NFR-PERF-001 (Performance target)
- REQ-NFR-SEC-001 (Password security)

**Stakeholders**:
- Product Owner (approval)
- End Users (benefit)
- Security Team (compliance)

**Test Strategy**:
- Unit tests: Happy path, error cases, edge cases
- Integration tests: Database interaction, session management
- Performance tests: Load testing, response time validation
- BDD scenarios: User acceptance testing

---

### REQ-F-AUTH-002: User Logout

**Type**: Functional
**Priority**: High
**Release**: 1.0
**Phase**: 1

**Description**:
System shall allow authenticated users to terminate their session.

**Acceptance Criteria**:
1. User can click logout button
2. Session token is invalidated
3. User is redirected to login page
4. Cached data is cleared

**Source**: INTENT-001 (Customer self-service portal)
**Dependencies**: REQ-F-AUTH-001 (must login before logout)

## Non-Functional Requirements

### REQ-NFR-PERF-001: Login Performance

**Type**: Non-Functional (Performance)
**Priority**: High
**Release**: 1.0
**Phase**: 1

**Description**:
Login response time shall be under 500ms at 95th percentile under normal load.

**Acceptance Criteria**:
1. 95th percentile response time < 500ms
2. Normal load defined as 100 concurrent users
3. Measured from submit button click to dashboard display
4. Includes database query, bcrypt verification, session creation

**Source**: INTENT-001 (Performance expectations)
**Dependencies**: REQ-F-AUTH-001 (login functionality)

**Measurement**:
- Tool: Performance monitoring (Datadog, New Relic)
- Metric: `auth.login.duration_ms_p95`
- Alert threshold: 500ms

### REQ-NFR-SEC-001: Password Security

**Type**: Non-Functional (Security)
**Priority**: Critical
**Release**: 1.0
**Phase**: 1

**Description**:
All user passwords shall be hashed using bcrypt with work factor ≥ 12.

**Acceptance Criteria**:
1. Passwords never stored in plaintext
2. bcrypt algorithm used for hashing
3. Work factor (cost) set to 12 or higher
4. Hash format: `$2b$12$...` (bcrypt identifier, work factor, salt+hash)

**Source**: Security policy, industry best practices
**Dependencies**: None

**Compliance**: OWASP Password Storage Cheat Sheet

## Data Quality Requirements

### REQ-DATA-USER-001: Email Validation

**Type**: Data Quality
**Priority**: High
**Release**: 1.0
**Phase**: 1

**Description**:
User email addresses shall conform to RFC 5322 format specification.

**Acceptance Criteria**:
1. Email must contain exactly one @ symbol
2. Local part (before @) must be 1-64 characters
3. Domain part (after @) must be valid domain format
4. No whitespace allowed
5. Case-insensitive comparison

**Source**: Data quality standards
**Dependencies**: None

**Validation**: Regex pattern matching or email validation library

## Business Rules

### REQ-BR-AUTH-001: Login Rate Limiting

**Type**: Business Rule
**Priority**: Medium
**Release**: 1.0
**Phase**: 1

**Description**:
System shall enforce rate limiting of 3 failed login attempts per email address within 15-minute window.

**Acceptance Criteria**:
1. Track failed login attempts by email address
2. After 3 failed attempts, lock account for 15 minutes
3. Display clear error message: "Too many login attempts. Try again in 15 minutes."
4. Counter resets after successful login or 15-minute timeout
5. Admin can manually reset rate limit

**Source**: Security policy (prevent brute force attacks)
**Dependencies**: REQ-F-AUTH-001 (login functionality)

**Rationale**: Balance security (prevent brute force) with usability (temporary lockout only)
```

---

### Design Document Example

```markdown
# Authentication System Design

## Component: AuthenticationService

**Purpose**: Centralized service for user authentication workflows

**Implements**:
- REQ-F-AUTH-001: User Login
- REQ-F-AUTH-002: User Logout
- REQ-NFR-PERF-001: Login Performance
- REQ-NFR-SEC-001: Password Security

**Architecture**:

```
┌─────────────────────────────────────┐
│    AuthenticationService            │
├─────────────────────────────────────┤
│ + login(email, password)            │ ← REQ-F-AUTH-001
│ + logout(session_id)                │ ← REQ-F-AUTH-002
│ - _is_valid_email(email)            │ ← REQ-DATA-USER-001
│ - _is_rate_limited(email)           │ ← REQ-BR-AUTH-001
│ - _record_failed_attempt(email)     │ ← REQ-BR-AUTH-001
└─────────────────────────────────────┘
         │              │
         │              └─────> UserRepository
         └────────────────────> SessionManager
```

### Public Methods

#### login(email: str, password: str) → LoginResult

**Implements**: REQ-F-AUTH-001

**Flow**:
1. Validate email format (REQ-DATA-USER-001)
2. Check rate limiting (REQ-BR-AUTH-001)
3. Query user by email (UserRepository)
4. Verify password with bcrypt (REQ-NFR-SEC-001)
5. Create session (SessionManager)
6. Record metrics (REQ-NFR-PERF-001)
7. Return result

**Performance**: Target < 500ms (REQ-NFR-PERF-001)
- Database query: ~50ms
- bcrypt verification: ~100ms
- Session creation: ~20ms
- Total: ~170ms (buffer: 330ms)

**Error Handling**:
- Invalid email format → ValueError
- Rate limited → RateLimitError
- Invalid credentials → Return LoginResult(success=False)

#### logout(session_id: str) → void

**Implements**: REQ-F-AUTH-002

**Flow**:
1. Validate session_id exists
2. Invalidate session token (SessionManager)
3. Clear session cache
4. Record logout event

### Private Methods

#### _is_valid_email(email: str) → bool

**Implements**: REQ-DATA-USER-001

Validates email format using regex pattern per RFC 5322.

#### _is_rate_limited(email: str) → bool

**Implements**: REQ-BR-AUTH-001

Checks if email has exceeded 3 failed attempts within 15-minute window.

#### _record_failed_attempt(email: str) → void

**Implements**: REQ-BR-AUTH-001

Records failed login attempt with timestamp in cache.

---

## Data Model

### User

```python
class User:
    id: int
    email: str              # REQ-DATA-USER-001
    password_hash: str      # REQ-NFR-SEC-001 (bcrypt)
    created_at: datetime
    updated_at: datetime
```

### Session

```python
class Session:
    id: int
    user_id: int
    token: str
    expires_at: datetime
    created_at: datetime
```

---

## Architecture Decision Records

### ADR-003: Use bcrypt for Password Hashing

**Status**: Accepted
**Date**: 2026-01-20
**Implements**: REQ-NFR-SEC-001

See: `docs/design/{variant}_aisdlc/adrs/ADR-003-bcrypt-password-hashing.md`
```

---

## Anti-Patterns (DO NOT DO THIS)

### ❌ Missing Tag

**Wrong**:
```python
def login(email, password):  # No REQ-* tag
    pass
```

**Correct**:
```python
# Implements: REQ-F-AUTH-001
def login(email: str, password: str) -> LoginResult:
    """Authenticate user with credentials."""
    pass
```

---

### ❌ Wrong Format

**Wrong**:
```python
# REQ-AUTH-1  # Missing TYPE, wrong sequence format
def login(email, password):
    pass
```

**Correct**:
```python
# Implements: REQ-F-AUTH-001  # TYPE-DOMAIN-SEQ format
def login(email: str, password: str) -> LoginResult:
    pass
```

---

### ❌ Untraceable Tag

**Wrong**:
```python
# Implements: REQ-F-XYZ-999  # Doesn't exist in requirements doc
def login(email, password):
    pass
```

**Correct**:
```python
# Implements: REQ-F-AUTH-001  # Exists in REQUIREMENTS.md
def login(email: str, password: str) -> LoginResult:
    pass
```

---

### ❌ Commit Without Tags

**Wrong**:
```
Add login feature

- Implement login functionality
- Add tests
```

**Correct**:
```
Implement user login (REQ-F-AUTH-001)

- Add login() method with email/password validation
- Add bcrypt password hashing
- Add unit tests for login scenarios

Implements: REQ-F-AUTH-001
Validates: REQ-F-AUTH-001
```

---

### ❌ Vague Tag

**Wrong**:
```python
# Implements: login  # Not a REQ-* key
def login(email, password):
    pass
```

**Correct**:
```python
# Implements: REQ-F-AUTH-001  # Specific requirement key
def login(email: str, password: str) -> LoginResult:
    pass
```

---

### ❌ Wrong Type

**Wrong**:
```python
# Implements: REQ-F-PERF-001  # Performance is NFR, not F
def login(email, password):
    pass
```

**Correct**:
```python
# Implements: REQ-F-AUTH-001, REQ-NFR-PERF-001  # Correct types
def login(email: str, password: str) -> LoginResult:
    pass
```

---

## Tips and Best Practices

### Tip 1: Tag Early and Often

Tag requirements, design, and tasks **before writing code**. This ensures traceability from the start.

### Tip 2: Use Multiple Tags When Appropriate

If code implements multiple requirements, list them all:

```python
# Implements: REQ-F-AUTH-001, REQ-NFR-PERF-001, REQ-NFR-SEC-001
def login(email: str, password: str) -> LoginResult:
    ...
```

### Tip 3: Tag Both Production and Test Code

**Production code**: `# Implements: REQ-*`
**Test code**: `# Validates: REQ-*`

### Tip 4: Update Traceability Matrix Regularly

After implementing a requirement, update `docs/TRACEABILITY_MATRIX.md` with file paths and line numbers.

### Tip 5: Use Validation Tools

Run `validate_traceability.py` before commits to catch missing or invalid tags.

### Tip 6: Reference REQ Keys in Documentation

Link requirements to code in docstrings and comments for easy navigation.

### Tip 7: Tag Refactoring Commits

Even if no new functionality, tag refactoring commits with affected requirements:

```
Refactor authentication for modularity (REQ-F-AUTH-001)

Implements: REQ-F-AUTH-001
```

---

## Version History

- **1.0** (2026-01-20): Initial version for Roo AISDLC Phase 1A
  - Complete REQ-* format specification
  - Usage examples for all 7 artifact types
  - Validation checklist for agents
  - Complete code examples (Python, TypeScript)
  - Anti-patterns section
  - 600+ lines of comprehensive content
  - Implements: REQ-ROO-RULE-003

---

## Remember

- **Every requirement** has a unique, immutable REQ-* key
- **Every artifact** (requirements, design, tasks, code, tests, commits) references REQ-* keys
- **Every agent** validates and propagates REQ-* tags
- **Traceability enables**:
  - Impact analysis (which code affected by requirement change?)
  - Coverage analysis (which requirements lack tests?)
  - Root cause analysis (which requirement caused production issue?)
  - Audit compliance (prove requirements were implemented and tested)

**"No artifact without traceability"** 🔗
