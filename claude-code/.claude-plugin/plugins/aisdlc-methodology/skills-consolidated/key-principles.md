---
name: key-principles
description: Apply the Key Principles to development work - TDD, Fail Fast, Modular, Reuse, Open Source First, No Legacy, Excellence. Consolidates apply-key-principles, seven-questions-checklist.
allowed-tools: [Read, Write, Edit, Grep, Glob]
---

# Key Principles

**Skill Type**: Guidelines (Code Stage)
**Purpose**: Apply the Key Principles to all development work
**Consolidates**: apply-key-principles, seven-questions-checklist

---

## The Key Principles

### 1. Test Driven Development
**"No code without tests"**

Write tests FIRST, then implementation.

```
RED → GREEN → REFACTOR → COMMIT
```

**Anti-pattern**: Writing code first, tests later (or never).

---

### 2. Fail Fast & Root Cause
**"Break loudly, fix completely"**

- Detect errors immediately
- Surface root cause, not symptoms
- No swallowing exceptions
- Explicit error handling

```python
# GOOD: Fail fast with clear error
def get_user(user_id: str) -> User:
    if not user_id:
        raise ValueError("user_id is required")
    user = self.repo.find(user_id)
    if not user:
        raise UserNotFoundException(f"User {user_id} not found")
    return user

# BAD: Silent failure
def get_user(user_id: str) -> Optional[User]:
    try:
        return self.repo.find(user_id)
    except:
        return None  # Silent failure - BAD
```

---

### 3. Modular & Maintainable
**"Single responsibility, loose coupling"**

- Each module does ONE thing
- Clear interfaces between components
- Easy to understand in isolation
- Easy to modify without ripple effects

```python
# GOOD: Single responsibility
class UserValidator:
    def validate_email(self, email: str) -> bool: ...
    def validate_password(self, password: str) -> bool: ...

class UserRepository:
    def find(self, user_id: str) -> User: ...
    def save(self, user: User) -> None: ...

class UserService:
    def __init__(self, validator: UserValidator, repo: UserRepository):
        self.validator = validator
        self.repo = repo

# BAD: God class
class UserManager:
    def validate_email(self, email): ...
    def validate_password(self, password): ...
    def find_user(self, user_id): ...
    def save_user(self, user): ...
    def send_email(self, user, message): ...
    def generate_report(self, user): ...
    # ... 50 more methods
```

---

### 4. Reuse Before Build
**"Check first, create second"**

Before writing code:
1. Check if it exists in the codebase
2. Check if a library does it
3. Check if a standard pattern applies

```python
# GOOD: Reuse existing
from validators import validate_email  # Already exists!

# BAD: Reinventing the wheel
def validate_email(email: str) -> bool:
    # 50 lines of regex that already exists elsewhere
    pass
```

---

### 5. Open Source First
**"Suggest alternatives, human decides"**

For common problems:
1. Research open source solutions
2. Present options with trade-offs
3. Let human decide

```markdown
## Email Validation Options

1. **email-validator** (recommended)
   - 10M downloads/month
   - Active maintenance
   - DNS validation support

2. **validators**
   - Part of larger package
   - Simpler API

3. **Custom regex**
   - Full control
   - Maintenance burden

Recommendation: email-validator
```

---

### 6. No Legacy Baggage
**"Clean slate, no debt"**

- No technical debt
- No commented-out code
- No "temporary" hacks
- No unused code

```python
# GOOD: Clean code
def calculate_discount(amount: Decimal, rate: Decimal) -> Decimal:
    return amount * rate

# BAD: Legacy baggage
def calculate_discount(amount, rate):
    # TODO: Fix this later
    # Old implementation (don't use):
    # return amount * 0.1
    result = amount * rate
    # Hack for legacy system
    if rate > 0.5:
        result = result * 1.1  # Magic number, nobody knows why
    return result
```

---

### 7. Perfectionist Excellence
**"Best of breed only"**

- Don't settle for "good enough"
- Quality is non-negotiable
- If it's worth doing, do it right

```python
# GOOD: Excellence
@dataclass
class LoginResult:
    """Result of login attempt.

    Implements: REQ-F-AUTH-001
    """
    success: bool
    user: Optional[User] = None
    token: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[ErrorCode] = None
    attempts_remaining: Optional[int] = None

# BAD: "Good enough"
def login(email, pwd):
    # Returns True/False, good enough
    return check_password(email, pwd)
```

---

## The Seven Questions Checklist

**Before writing ANY code, ask yourself:**

### 1. Have I written tests first?
*Principle #1: Test Driven Development*

- [ ] Test file exists
- [ ] Tests are RED (failing)
- [ ] Tests cover requirements

### 2. Will this fail loudly if wrong?
*Principle #2: Fail Fast & Root Cause*

- [ ] Explicit error handling
- [ ] Clear error messages
- [ ] No silent failures

### 3. Is this module focused?
*Principle #3: Modular & Maintainable*

- [ ] Single responsibility
- [ ] Clear interface
- [ ] Low coupling

### 4. Did I check if this exists?
*Principle #4: Reuse Before Build*

- [ ] Searched codebase
- [ ] Checked libraries
- [ ] Reviewed patterns

### 5. Have I researched alternatives?
*Principle #5: Open Source First*

- [ ] Evaluated options
- [ ] Documented trade-offs
- [ ] Human approved choice

### 6. Am I avoiding tech debt?
*Principle #6: No Legacy Baggage*

- [ ] No TODOs without tickets
- [ ] No commented code
- [ ] No magic numbers

### 7. Is this excellent?
*Principle #7: Perfectionist Excellence*

- [ ] Would I be proud of this?
- [ ] Would I accept this in a code review?
- [ ] Is this the best solution?

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    KEY PRINCIPLES                           │
├─────────────────────────────────────────────────────────────┤
│ 1. TDD           │ Tests first. Always.                     │
│ 2. Fail Fast     │ Errors are loud and clear.               │
│ 3. Modular       │ One module, one job.                     │
│ 4. Reuse First   │ Don't reinvent. Check first.             │
│ 5. Open Source   │ Research options. Human decides.         │
│ 6. No Legacy     │ Clean code. No debt. No hacks.           │
│ 7. Excellence    │ Best solution or nothing.                │
├─────────────────────────────────────────────────────────────┤
│                  "Excellence or nothing"                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Applying to Code Reviews

**When reviewing code, check for:**

| Principle | Review Question |
|-----------|-----------------|
| TDD | Are there tests? Do they cover the requirements? |
| Fail Fast | Are errors handled explicitly? Clear messages? |
| Modular | Single responsibility? Low coupling? |
| Reuse | Could this use existing code/library? |
| Open Source | Was alternatives research documented? |
| No Legacy | Any TODOs, dead code, magic numbers? |
| Excellence | Is this the best solution? |

---

## Code Templates

### Function Template

```python
def function_name(param: Type) -> ReturnType:
    """Brief description.

    Implements: REQ-*
    Business Rules: BR-*

    Args:
        param: Description

    Returns:
        Description

    Raises:
        ErrorType: When condition
    """
    # Fail fast - validate inputs
    if not param:
        raise ValueError("param is required")

    # Implementation
    result = ...

    return result
```

### Class Template

```python
@dataclass
class ClassName:
    """Brief description.

    Implements: REQ-*

    Attributes:
        field: Description
    """
    field: Type

    def method(self, param: Type) -> ReturnType:
        """Brief description.

        Implements: REQ-*
        """
        pass
```

### Test Template

```python
class TestClassName:
    """Tests for ClassName.

    Validates: REQ-*
    """

    def test_happy_path(self):
        """Test successful case."""
        # Validates: REQ-*
        # Arrange
        input = ...

        # Act
        result = function(input)

        # Assert
        assert result == expected

    def test_error_case(self):
        """Test error handling."""
        # Validates: Principle #2 (Fail Fast)
        with pytest.raises(ExpectedError):
            function(invalid_input)
```

---

## Output Format

```
[KEY PRINCIPLES CHECK]

Code: src/auth/login.py

Principle 1 (TDD):
  ✅ Tests exist: tests/auth/test_login.py
  ✅ Tests written first (git history confirms)
  ✅ Coverage: 95%

Principle 2 (Fail Fast):
  ✅ Explicit error handling
  ✅ Clear error messages
  ❌ One silent failure at line 45 (caught exception, returns None)

Principle 3 (Modular):
  ✅ Single responsibility
  ✅ Clear interface
  ✅ Low coupling

Principle 4 (Reuse):
  ✅ Using email-validator library
  ✅ Using existing UserRepository

Principle 5 (Open Source):
  ✅ bcrypt chosen (documented in ADR-002)

Principle 6 (No Legacy):
  ✅ No TODOs
  ✅ No commented code
  ❌ Magic number at line 23 (should be constant)

Principle 7 (Excellence):
  ✅ Type hints complete
  ✅ Docstrings present
  ✅ Clean implementation

Issues Found: 2
  1. Line 45: Silent failure - add explicit error handling
  2. Line 23: Magic number - extract to constant

Recommendation: Fix 2 issues before merge
```

---

## Configuration

```yaml
# .claude/plugins.yml
plugins:
  - name: "@aisdlc/aisdlc-methodology"
    config:
      principles:
        enforce_tdd: true
        require_tests_first: true
        fail_fast_check: true
        modularity_check: true
        check_for_existing: true
        no_legacy_baggage: true
        excellence_standard: true
        block_on_violations: true
```

---

## Ultimate Mantra

**"Excellence or nothing"**

If you can't answer "yes" to all seven questions, don't write the code yet.

Quality is non-negotiable.
