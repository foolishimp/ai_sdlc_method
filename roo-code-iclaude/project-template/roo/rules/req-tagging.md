# REQ Tagging Rules

Requirement key format and tagging rules for traceability.

## Key Format

```
REQ-<TYPE>-<DOMAIN>-<NUMBER>
```

### Types
- `REQ-F-*` - Functional requirements (what system does)
- `REQ-NFR-*` - Non-functional requirements (quality attributes)
- `REQ-DATA-*` - Data quality requirements (validation, format)
- `REQ-BR-*` - Business rules (domain logic)

### Domains
Examples:
- AUTH - Authentication
- USER - User management
- PAY - Payments
- PERF - Performance
- SEC - Security
- TRACE - Traceability

### Numbers
- Sequential within domain
- Never reused (immutable)
- Start at 001

## Examples

```
REQ-F-AUTH-001    # User login with email/password
REQ-F-AUTH-002    # Password reset flow
REQ-NFR-PERF-001  # Login response < 500ms
REQ-NFR-SEC-001   # Passwords hashed with bcrypt
REQ-DATA-USER-001 # Email must be valid format
REQ-BR-PAY-001    # Refunds within 30 days only
```

## Code Tagging

### Production Code
```python
# Implements: REQ-F-AUTH-001
def login(email: str, password: str) -> LoginResult:
    """Authenticate user with credentials."""
    ...
```

### Test Code
```python
def test_user_login():
    """
    # Validates: REQ-F-AUTH-001
    User can login with valid credentials.
    """
    ...
```

### Multiple Requirements
```python
# Implements: REQ-F-AUTH-001, REQ-NFR-SEC-001
def login(email: str, password: str) -> LoginResult:
    ...
```

## Feature File Tagging

```gherkin
Feature: User Authentication
  # Validates: REQ-F-AUTH-001

  Scenario: Successful login
    # Validates: REQ-F-AUTH-001
    Given I am on the login page
    ...
```

## Commit Message Tagging

```
Add user authentication (REQ-F-AUTH-001)

- Implement login() with email/password validation
- Add unit tests for login scenarios
- Integrate with session management

# Implements: REQ-F-AUTH-001
# Validates: REQ-F-AUTH-001
```

## Runtime Tagging

### Logs
```python
logger.info("Login successful", extra={
    "requirement": "REQ-F-AUTH-001",
    "user_id": user.id
})
```

### Metrics
```python
metrics.increment("auth.login.success", tags=[
    "req:REQ-F-AUTH-001"
])
```

### Alerts
```yaml
alert:
  name: Login Timeout
  requirement: REQ-NFR-PERF-001
  condition: auth.latency_p95 > 500ms
```

## Validation Rules

### Before Commit
1. Scan modified code files
2. Check for `# Implements: REQ-*` tags
3. Check for `# Validates: REQ-*` in tests
4. Warn if any file lacks tags

### Traceability Matrix
Update `docs/TRACEABILITY_MATRIX.md`:
- Add implementation path
- Add test path
- Update coverage status

## Anti-Patterns

### DON'T: Generic Tags
```python
# WRONG: Too vague
# Implements: REQ-F-001
```

### DON'T: Missing Tags
```python
# WRONG: No requirement reference
def login(email, password):
    ...
```

### DON'T: Wrong Type
```python
# WRONG: Performance is NFR, not F
# Implements: REQ-F-PERF-001
```

## Remember

- Every line of production code traces to a REQ-* key
- Every test validates specific requirements
- Every commit references what it implements
- Traceability enables impact analysis
