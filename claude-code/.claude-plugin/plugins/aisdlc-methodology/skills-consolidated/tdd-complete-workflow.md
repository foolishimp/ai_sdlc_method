---
name: tdd-complete-workflow
description: Complete Test-Driven Development workflow - RED (write failing tests) → GREEN (minimal implementation) → REFACTOR (quality + tech debt) → COMMIT (traceability). Consolidates tdd-workflow, red-phase, green-phase, refactor-phase, commit-with-req-tag.
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
---

# TDD Complete Workflow

**Skill Type**: Complete Workflow (Code Stage)
**Purpose**: Implement requirements using TDD with full traceability
**Consolidates**: tdd-workflow, red-phase, green-phase, refactor-phase, commit-with-req-tag

---

## When to Use This Skill

Use this skill when:
- Implementing a new requirement (REQ-*)
- Adding new functionality with tests
- Following Test-Driven Development approach
- Need full requirement traceability

---

## Prerequisites

Before starting, verify:
1. Requirement key exists (REQ-F-*, REQ-NFR-*, REQ-DATA-*, REQ-BR-*)
2. Requirement details available (what to implement)
3. Working directory is a git repository
4. No uncommitted changes (clean working tree)

**If prerequisites missing**:
- No REQ-* key → Use `requirements-extraction` skill first
- No requirement details → Ask user for clarification
- Dirty working tree → Ask user to commit or stash

---

## Complete Workflow

### Phase 1: RED (Write Failing Tests)

**Goal**: Write tests that FAIL because implementation doesn't exist yet.

**Steps**:

1. **Analyze Requirement**
   - What functionality needs to be implemented?
   - What are the business rules (BR-*)?
   - What are the expected inputs/outputs?

2. **Design Test Cases**
   - Happy path (valid inputs, expected success)
   - Business rules (each BR-* gets at least 1 test)
   - Edge cases (boundaries, empty values)
   - Error cases (invalid inputs)

3. **Create Test File**

   **Python (pytest)**:
   ```python
   # tests/auth/test_login.py

   # Validates: REQ-F-AUTH-001
   # Business Rules: BR-001, BR-002, BR-003

   import pytest
   from auth.login import login, LoginResult  # Will fail - doesn't exist

   def test_login_with_valid_credentials():
       """Test successful login with valid email and password"""
       # Validates: REQ-F-AUTH-001 (happy path)
       result = login("user@example.com", "SecurePass123!")
       assert result.success == True
       assert result.user is not None

   def test_login_fails_with_invalid_email():
       """Test login fails with invalid email format"""
       # Validates: BR-001 (email validation)
       result = login("invalid-email", "SecurePass123!")
       assert result.success == False
       assert result.error == "Invalid email format"

   def test_login_fails_with_short_password():
       """Test login fails with password < 12 characters"""
       # Validates: BR-002 (password minimum length)
       result = login("user@example.com", "short")
       assert result.success == False
   ```

   **TypeScript (Jest)**:
   ```typescript
   // login.test.ts

   // Validates: REQ-F-AUTH-001
   // Business Rules: BR-001, BR-002

   import { login } from './login';  // Will fail - doesn't exist

   describe('Login', () => {
     test('successful login with valid credentials', () => {
       // Validates: REQ-F-AUTH-001
       const result = login('user@example.com', 'SecurePass123!');
       expect(result.success).toBe(true);
     });

     test('fails with invalid email', () => {
       // Validates: BR-001
       const result = login('invalid-email', 'SecurePass123!');
       expect(result.success).toBe(false);
     });
   });
   ```

4. **Run Tests (Expect FAILURE)**
   ```bash
   # Python
   pytest tests/auth/test_login.py -v

   # TypeScript
   npm test login.test.ts
   ```

   Expected: `ImportError` or `ModuleNotFoundError` - tests fail because code doesn't exist.

5. **Commit RED Phase**
   ```bash
   git add tests/
   git commit -m "RED: Add tests for REQ-F-AUTH-001

   Write failing tests for user login functionality.

   Tests: 5 tests (all failing as expected)
   Validates: REQ-F-AUTH-001
   Business Rules: BR-001, BR-002, BR-003
   "
   ```

---

### Phase 2: GREEN (Make Tests Pass)

**Goal**: Write MINIMAL code to make tests pass. No over-engineering.

**Steps**:

1. **Create Implementation File**

   **Python**:
   ```python
   # src/auth/login.py

   # Implements: REQ-F-AUTH-001

   from dataclasses import dataclass
   from typing import Optional
   import re

   @dataclass
   class User:
       email: str

   @dataclass
   class LoginResult:
       success: bool
       user: Optional[User] = None
       error: Optional[str] = None

   def login(email: str, password: str) -> LoginResult:
       """Authenticate user with email and password.

       Implements: REQ-F-AUTH-001
       Business Rules: BR-001, BR-002
       """
       # BR-001: Email validation
       if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
           return LoginResult(success=False, error="Invalid email format")

       # BR-002: Password minimum length
       if len(password) < 12:
           return LoginResult(success=False, error="Password must be at least 12 characters")

       # Minimal implementation - just return success for valid inputs
       return LoginResult(success=True, user=User(email=email))
   ```

2. **Run Tests (Expect SUCCESS)**
   ```bash
   pytest tests/auth/test_login.py -v
   ```

   Expected: All tests PASS.

3. **Commit GREEN Phase**
   ```bash
   git add src/
   git commit -m "GREEN: Implement REQ-F-AUTH-001

   Add minimal implementation to pass all tests.

   Implements: REQ-F-AUTH-001
   Business Rules: BR-001, BR-002
   Tests: All passing
   "
   ```

---

### Phase 3: REFACTOR (Quality + Tech Debt Elimination)

**Goal**: Improve code quality and eliminate tech debt WITHOUT changing behavior.

**Steps**:

1. **Code Quality Improvements**
   - Add type hints (Python) / type annotations (TypeScript)
   - Add docstrings to public methods
   - Improve variable names
   - Extract magic numbers to constants

2. **Tech Debt Elimination** (Principle #6: No Legacy Baggage)
   - **Delete** unused imports
   - **Remove** dead code (functions with zero callers)
   - **Delete** commented-out code
   - **Simplify** over-complex logic (cyclomatic complexity > 10)
   - **Remove** code duplication

3. **Run Tests (Expect STILL PASSING)**
   ```bash
   pytest tests/auth/test_login.py -v
   ```

4. **Commit REFACTOR Phase**
   ```bash
   git add .
   git commit -m "REFACTOR: Clean up REQ-F-AUTH-001

   Code Quality:
   - Added type hints to all functions
   - Improved docstrings
   - Extracted regex to constant

   Tech Debt Pruning:
   - Deleted 2 unused imports
   - Removed 1 dead function

   Tests: Still passing
   "
   ```

---

### Phase 4: COMMIT (Final with Traceability)

**Goal**: Create final commit with full requirement traceability.

**Steps**:

1. **Create Final Commit**
   ```bash
   git commit -m "feat: Add user login (REQ-F-AUTH-001)

   Implements user authentication with email and password.

   Business Rules:
   - BR-001: Email validation
   - BR-002: Password minimum 12 characters

   Tests: 5 tests, 100% coverage

   Implements: REQ-F-AUTH-001
   "
   ```

2. **Optional: Squash Commits**
   If configured, squash RED/GREEN/REFACTOR into single commit:
   ```bash
   git rebase -i HEAD~3
   # squash all into "feat: Add user login (REQ-F-AUTH-001)"
   ```

---

## Output Format

When TDD workflow completes, show:

```
[TDD Workflow: REQ-F-AUTH-001]

Phase 1: RED (Write Failing Tests)
  Created: tests/auth/test_login.py (5 tests)
  Tests FAILED as expected
  Commit: RED: Add tests for REQ-F-AUTH-001

Phase 2: GREEN (Make Tests Pass)
  Created: src/auth/login.py
  Implemented: login() function
  Tests PASSED
  Commit: GREEN: Implement REQ-F-AUTH-001

Phase 3: REFACTOR (Quality + Tech Debt)
  Code Quality: Added type hints, docstrings
  Tech Debt: Deleted 2 unused imports
  Tests still PASSING
  Commit: REFACTOR: Clean up REQ-F-AUTH-001

Phase 4: COMMIT (Final)
  Final commit: feat: Add user login (REQ-F-AUTH-001)

TDD Workflow Complete!
  Files: 2 (login.py, test_login.py)
  Tests: 5 tests, all passing
  Commits: 4 (RED, GREEN, REFACTOR, final)
  Traceability: REQ-F-AUTH-001 → commit abc123
```

---

## Test Templates by Language

### Python (pytest)

```python
# tests/test_feature.py

# Validates: REQ-*
# Business Rules: BR-*, BR-*

import pytest
from module import function

class TestFeature:
    """Test suite for Feature. Validates: REQ-*"""

    def test_happy_path(self):
        """Test successful case. Validates: REQ-*"""
        result = function("valid_input")
        assert result == expected_output

    def test_business_rule(self):
        """Test business rule enforcement. Validates: BR-001"""
        with pytest.raises(ValidationError):
            function("invalid_input")

    @pytest.mark.parametrize("input,expected", [
        ("edge1", "output1"),
        ("edge2", "output2"),
    ])
    def test_edge_cases(self, input, expected):
        """Test edge cases. Validates: REQ-*"""
        assert function(input) == expected
```

### TypeScript (Jest)

```typescript
// feature.test.ts

// Validates: REQ-*
// Business Rules: BR-*, BR-*

import { function } from './module';

describe('Feature', () => {
  describe('happy path', () => {
    test('successful case - REQ-*', () => {
      const result = function('valid_input');
      expect(result).toBe(expected_output);
    });
  });

  describe('business rules', () => {
    test('BR-001 - validation error', () => {
      expect(() => function('invalid_input')).toThrow(ValidationError);
    });
  });

  describe.each([
    ['edge1', 'output1'],
    ['edge2', 'output2'],
  ])('edge cases', (input, expected) => {
    test(`${input} returns ${expected}`, () => {
      expect(function(input)).toBe(expected);
    });
  });
});
```

### Java (JUnit 5)

```java
// FeatureTest.java

// Validates: REQ-*
// Business Rules: BR-*, BR-*

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

class FeatureTest {
    @Test
    @DisplayName("Happy path - REQ-*")
    void testHappyPath() {
        var result = Feature.function("valid_input");
        assertEquals(expected_output, result);
    }

    @Test
    @DisplayName("BR-001 - validation error")
    void testBusinessRule() {
        assertThrows(ValidationException.class, () -> {
            Feature.function("invalid_input");
        });
    }

    @ParameterizedTest
    @CsvSource({"edge1,output1", "edge2,output2"})
    void testEdgeCases(String input, String expected) {
        assertEquals(expected, Feature.function(input));
    }
}
```

---

## Configuration

```yaml
# .claude/plugins.yml
plugins:
  - name: "@aisdlc/aisdlc-methodology"
    config:
      tdd:
        minimum_coverage: 80          # Fail if coverage < 80%
        enforce_red_green_refactor: true  # Enforce phase order
        allow_skip_tests: false       # Block if user tries to skip tests
        squash_commits: false         # Keep RED/GREEN/REFACTOR commits separate
        tech_debt_threshold: 0        # No tech debt allowed
```

---

## Homeostasis Behavior

**If prerequisites not met**:
- Detect: Missing REQ-* key
- Signal: "Need requirement extraction first"
- Action: Use `requirements-extraction` skill
- Retry: TDD workflow with new REQ-*

**If tests fail in GREEN phase**:
- Detect: Tests still failing after implementation
- Signal: "Implementation incomplete"
- Action: Fix implementation
- Do NOT proceed to REFACTOR until tests pass

**If tech debt in REFACTOR phase**:
- Detect: Unused code, high complexity, etc.
- Signal: "Tech debt detected"
- Action: Clean up code
- Verify: Tech debt eliminated before commit

---

## Key Principles Applied

1. **Test Driven Development** - "No code without tests" (tests first in RED phase)
2. **Fail Fast** - Tests fail immediately in RED (expected behavior)
3. **No Legacy Baggage** - Tech debt eliminated in REFACTOR phase
4. **Perfectionist Excellence** - Quality improvements in REFACTOR

**"Excellence or nothing"**
