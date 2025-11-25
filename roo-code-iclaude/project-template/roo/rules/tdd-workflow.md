# TDD Workflow

The Test-Driven Development workflow for the Code stage (Stage 4).

## The Cycle

```
RED → GREEN → REFACTOR → COMMIT → REPEAT
```

## Phase 1: RED (Write Failing Test)

**Goal**: Define expected behavior before implementation

1. Identify the requirement (REQ-* key)
2. Write a test that validates the requirement
3. Add tag: `# Validates: REQ-F-*`
4. Run test - it MUST fail
5. Failure message should be clear

```python
def test_user_login_with_valid_credentials():
    """
    # Validates: REQ-F-AUTH-001
    User can login with valid email and password.
    """
    user = create_test_user(email="test@example.com", password="valid123")
    result = login(email="test@example.com", password="valid123")
    assert result.success is True
    assert result.user.email == "test@example.com"
```

**Checkpoint**: Test fails with clear message about missing implementation.

## Phase 2: GREEN (Make It Pass)

**Goal**: Write minimal code to pass the test

1. Write the simplest implementation
2. Add tag: `# Implements: REQ-F-*`
3. No extra features
4. No premature optimization
5. Run test - it MUST pass

```python
# Implements: REQ-F-AUTH-001
def login(email: str, password: str) -> LoginResult:
    """Authenticate user with email and password."""
    user = User.get_by_email(email)
    if user and user.check_password(password):
        return LoginResult(success=True, user=user)
    return LoginResult(success=False)
```

**Checkpoint**: Test passes. No more code than needed.

## Phase 3: REFACTOR (Improve Quality)

**Goal**: Improve code without changing behavior

1. All tests still pass
2. Improve readability
3. Remove duplication
4. Add type hints if missing
5. Improve naming
6. No new features

**Refactoring candidates**:
- Long functions → Extract methods
- Duplicate code → Extract helper
- Complex conditionals → Early returns
- Magic numbers → Named constants
- Missing types → Add type hints

**Checkpoint**: Tests still pass. Code is cleaner.

## Phase 4: COMMIT (Save Progress)

**Goal**: Record the work with traceability

1. Stage changes: `git add .`
2. Write commit message with REQ-* key
3. Include what and why
4. Commit: `git commit`

```
Add user login authentication (REQ-F-AUTH-001)

- Implement login() function with email/password
- Add unit tests for valid and invalid credentials
- Validates REQ-F-AUTH-001 acceptance criteria

# Implements: REQ-F-AUTH-001
```

**Checkpoint**: Work is saved with clear traceability.

## Phase 5: REPEAT

**Goal**: Continue with next test

1. Pick next requirement or edge case
2. Return to Phase 1 (RED)
3. Build features incrementally
4. Each cycle is small (5-15 minutes)

## Coverage Requirements

- **Minimum overall**: 80%
- **Critical paths**: 100%
- **New code**: Must have tests

Check coverage before commit:
```bash
pytest --cov=src --cov-report=term-missing
```

## Anti-Patterns to Avoid

### DON'T: Write Code First
```
# WRONG: Implementation before test
def login(email, password):  # No test exists yet!
    ...
```

### DON'T: Test After
```
# WRONG: Writing test to match existing code
def test_login():  # Written to pass existing code
    ...
```

### DON'T: Skip Refactor
```
# WRONG: Moving on without cleaning up
# "I'll refactor later" = Never
```

### DON'T: Big Commits
```
# WRONG: Committing hours of work at once
# Keep commits small and focused
```

## Remember

- Tests are documentation
- Tests are design
- Tests are safety
- Tests come first

**No code without tests. Ever.**
