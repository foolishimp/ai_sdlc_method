# detect-complexity

**Skill Type**: Sensor (Homeostasis)
**Purpose**: Detect over-complex code that violates Principle #3 ("Modular & Maintainable")
**Prerequisites**: None (can run anytime)

---

## Agent Instructions

You are a **Sensor** in the homeostasis system. Your job is to **detect deviations** from the desired state.

**Desired State**: `max_cyclomatic_complexity ≤ 10`

Scan the codebase for:
1. **Cyclomatic Complexity** - too many branches/paths
2. **Function Length** - functions that are too long
3. **Nesting Depth** - deeply nested code

---

## Detection Algorithm

### 1. Calculate Cyclomatic Complexity

For each function/method:
```
Cyclomatic Complexity = 1 (base)
  + 1 for each if/elif
  + 1 for each while/for loop
  + 1 for each and/or in conditions
  + 1 for each except clause
  + 1 for each case in match/switch
  + 1 for each ternary operator (? :)

Threshold: 10 (industry standard)

If complexity > 10 → Flag as violation
```

**Example**:
```python
def login(email, password):          # Complexity: 18
    if email is None:                # +1 = 2
        return error("Email required")
    if not is_valid_email(email):    # +1 = 3
        return error("Invalid email")
    if not User.exists(email):       # +1 = 4
        return error("User not found")
    user = User.get(email)
    if user.is_locked:               # +1 = 5
        if not user.lockout_expired():  # +1 = 6
            return error("Account locked")
        else:
            user.unlock()
    try:                             # +0 (try doesn't count)
        if not user.check_password(password):  # +1 = 7
            user.increment_attempts()
            if user.attempts >= 3:   # +1 = 8
                user.lock()
            return error("Invalid password")
    except Exception:                # +1 = 9
        log.error("Auth error")
    if user.needs_2fa:               # +1 = 10
        if not verify_2fa(user):     # +1 = 11
            return error("2FA failed")
    if user.password_expired:        # +1 = 12
        if days_since(user.password_updated) > 90:  # +1 = 13
            return error("Password expired")
    if rate_limit_exceeded(user):    # +1 = 14
        return error("Too many requests")
    if user.account_suspended:       # +1 = 15
        return error("Account suspended")
    if not user.email_verified:      # +1 = 16
        return error("Email not verified")
    if user.role == 'admin' and not from_internal_ip():  # +1 (and) = 17
        return error("Admin must use VPN")
    return success(user)             # Total: 18
```

### 2. Measure Function Length

For each function/method:
```
Count lines of code (exclude blank lines, comments, docstrings)

Thresholds:
  - Warning: > 50 lines
  - Critical: > 100 lines

If LOC > 50 → Flag as warning
If LOC > 100 → Flag as critical violation
```

### 3. Measure Nesting Depth

For each function/method:
```
Track maximum nesting level of control structures

Thresholds:
  - Warning: > 3 levels
  - Critical: > 5 levels

If nesting > 3 → Flag as warning
If nesting > 5 → Flag as critical violation
```

**Example**:
```python
def process_payment(amount, card):
    if amount > 0:                          # Nesting: 1
        if card.is_valid():                 # Nesting: 2
            if card.balance >= amount:      # Nesting: 3
                if not card.is_expired():   # Nesting: 4
                    if card.cvv_valid():    # Nesting: 5 ⚠️
                        if rate_limit_ok(): # Nesting: 6 ❌ CRITICAL
                            charge(card, amount)
```

---

## Output Format

Report findings in this format:

```yaml
complexity_report:
  file: "auth_service.py"
  timestamp: "2025-11-20T15:30:00Z"

  complexity_violations:
    - function: "login"
      lines: "105-180"
      complexity: 18
      threshold: 10
      severity: "critical"
      reason: "8 violations above threshold"
      suggestion: "Extract validation logic to separate functions"
      branches:
        - "email validation" (3 branches)
        - "account status checks" (5 branches)
        - "2FA verification" (2 branches)
        - "password validation" (3 branches)

    - function: "process_payment"
      lines: "220-250"
      complexity: 12
      threshold: 10
      severity: "warning"
      reason: "2 violations above threshold"
      suggestion: "Extract card validation logic"

  length_violations:
    - function: "login"
      lines: "105-180"
      loc: 76
      threshold: 50
      severity: "warning"
      suggestion: "Split into smaller functions"

  nesting_violations:
    - function: "process_payment"
      lines: "220-250"
      max_nesting: 6
      threshold: 3
      severity: "critical"
      location: "Line 235 (6 levels deep)"
      suggestion: "Use early returns to reduce nesting"

  summary:
    total_violations: 4
    complexity_critical: 1
    complexity_warning: 1
    length_warning: 1
    nesting_critical: 1
    max_complexity: 18
    avg_complexity: 6.4

  homeostasis_status: DEVIATION_DETECTED
  recommended_actuator: "simplify-complex-code"
```

---

## User-Facing Output

When run as `claude homeostasis status` or during refactor:

```
⚠️ detect-complexity - Last run: 1 min ago
  Status: Complexity violations
  Deviation: login() complexity 18 (threshold: 10)

Complexity Report (auth_service.py):
  ❌ login() - Cyclomatic complexity: 18 (threshold: 10)
    Lines: 105-180
    Violations: 8 above threshold
    Issues:
      - 6 nested if statements
      - 4 try/except blocks
      - 76 lines of code (threshold: 50)
    Recommendation: Extract validation logic to separate functions

  ⚠️ process_payment() - Cyclomatic complexity: 12 (threshold: 10)
    Lines: 220-250
    Violations: 2 above threshold
    Issues:
      - 6 levels of nesting (threshold: 3)
    Recommendation: Use early returns to reduce nesting

Summary:
  Functions scanned: 24
  Violations: 4
  Max complexity: 18
  Avg complexity: 6.4

Homeostasis deviation detected! Max complexity > 10 (Principle #3 violated).

Recommended action: Invoke 'simplify-complex-code' skill to refactor automatically.
```

---

## Complexity Refactoring Suggestions

For each violation, suggest specific refactoring:

**High Complexity**:
- Extract validation logic to separate functions
- Replace nested ifs with early returns (guard clauses)
- Extract conditional logic to named boolean variables
- Replace complex conditions with strategy pattern

**Long Functions**:
- Extract logical blocks to separate functions
- Move related functionality to helper methods
- Consider splitting into multiple smaller functions

**Deep Nesting**:
- Use early returns (fail fast)
- Invert conditions to reduce nesting
- Extract nested blocks to separate functions
- Use polymorphism instead of type checking

---

## Triggering Actuator

When deviation detected:
```
1. Report deviation with specific suggestions
2. Suggest invoking 'simplify-complex-code' actuator
3. Wait for user confirmation OR auto-invoke if configured
```

---

## Configuration

```yaml
plugins:
  - name: "@aisdlc/code-skills"
    config:
      complexity_detection:
        auto_detect_on_refactor: true     # Run during refactor phase
        auto_simplify: false              # Ask before refactoring
        complexity_threshold: 10          # Default: 10
        length_threshold: 50              # Default: 50 lines
        nesting_threshold: 3              # Default: 3 levels
        exclude_files:
          - "tests/*"                     # Don't check test files
          - "migrations/*"
```

---

## Prerequisites Check

None - this sensor can run anytime.

---

## Next Steps

After detection:
1. If violations found → Suggest `simplify-complex-code` actuator
2. If clean → Report "Homeostasis achieved! Max complexity ≤ 10 ✓"

---

## Notes

**Why complexity matters**:
- High complexity = more bugs (proven correlation)
- Hard to test (exponential growth in test cases)
- Hard to understand (cognitive load)
- Hard to maintain (more defects introduced during changes)

**Industry thresholds**:
- Complexity 1-10: Simple, low risk
- Complexity 11-20: Moderate, medium risk
- Complexity 21-50: Complex, high risk
- Complexity 50+: Untestable, very high risk

**Principle #3**: "Modular & Maintainable"
- Single responsibility → Low complexity
- Focused functions → Easy to test
- Simple logic → Easy to understand

**Homeostasis Goal**:
```yaml
desired_state:
  max_cyclomatic_complexity: 10
  max_function_length: 50
  max_nesting_depth: 3
```

**"Excellence or nothing"** 🔥
