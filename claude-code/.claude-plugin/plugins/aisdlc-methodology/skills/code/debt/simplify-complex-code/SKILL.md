# simplify-complex-code

**Skill Type**: Actuator (Homeostasis)
**Purpose**: Automatically refactor complex code to restore homeostasis (Principle #3: "Modular & Maintainable")
**Prerequisites**:
- `detect-complexity` skill must have run
- Complexity report available
- All tests passing (GREEN)

---

## Agent Instructions

You are an **Actuator** in the homeostasis system. Your job is to **correct deviations** and restore the desired state.

**Desired State**: `max_cyclomatic_complexity ≤ 10`

Based on the complexity report from `detect-complexity`, automatically refactor complex code using proven techniques.

---

## Simplification Techniques

### 1. Extract Functions (Complexity Reduction)

**Pattern**: High cyclomatic complexity (> 10)
**Solution**: Extract logical blocks to separate functions

**Example**:
```python
# BEFORE (Complexity: 18)
def login(email, password):
    if email is None:
        return error("Email required")
    if not is_valid_email(email):
        return error("Invalid email")
    if not User.exists(email):
        return error("User not found")
    user = User.get(email)
    if user.is_locked:
        if not user.lockout_expired():
            return error("Account locked")
        else:
            user.unlock()
    if not user.check_password(password):
        user.increment_attempts()
        if user.attempts >= 3:
            user.lock()
        return error("Invalid password")
    if user.needs_2fa:
        if not verify_2fa(user):
            return error("2FA failed")
    return success(user)

# AFTER (Complexity: 6)
def login(email, password):
    validation_error = validate_login_input(email, password)
    if validation_error:
        return validation_error

    user = get_user_or_fail(email)

    if user.is_locked and not user.lockout_expired():
        return error("Account locked")

    if not authenticate_user(user, password):
        return error("Authentication failed")

    if not verify_2fa_if_required(user):
        return error("2FA failed")

    return success(user)

# Extracted functions (each complexity < 5)
def validate_login_input(email, password):
    """Validates email and password format (Complexity: 3)"""
    if not email:
        return error("Email required")
    if not is_valid_email(email):
        return error("Invalid email")
    return None

def get_user_or_fail(email):
    """Gets user or raises error (Complexity: 2)"""
    if not User.exists(email):
        raise UserNotFoundError(email)
    user = User.get(email)
    if user.is_locked and user.lockout_expired():
        user.unlock()
    return user

def authenticate_user(user, password):
    """Authenticates user with password (Complexity: 3)"""
    if not user.check_password(password):
        user.increment_attempts()
        if user.attempts >= 3:
            user.lock()
        return False
    return True

def verify_2fa_if_required(user):
    """Verifies 2FA if user requires it (Complexity: 2)"""
    if not user.needs_2fa:
        return True
    return verify_2fa(user)
```

**Complexity Reduction**: 18 → 6 (67% reduction)

---

### 2. Early Returns (Nesting Reduction)

**Pattern**: Deep nesting (> 3 levels)
**Solution**: Invert conditions and use early returns (guard clauses)

**Example**:
```python
# BEFORE (Nesting: 6 levels)
def process_payment(amount, card):
    if amount > 0:                          # Level 1
        if card.is_valid():                 # Level 2
            if card.balance >= amount:      # Level 3
                if not card.is_expired():   # Level 4
                    if card.cvv_valid():    # Level 5
                        if rate_limit_ok(): # Level 6
                            return charge(card, amount)
                        else:
                            return error("Rate limit")
                    else:
                        return error("Invalid CVV")
                else:
                    return error("Card expired")
            else:
                return error("Insufficient funds")
        else:
            return error("Invalid card")
    else:
        return error("Invalid amount")

# AFTER (Nesting: 1 level)
def process_payment(amount, card):
    # Guard clauses (fail fast)
    if amount <= 0:
        return error("Invalid amount")
    if not card.is_valid():
        return error("Invalid card")
    if card.balance < amount:
        return error("Insufficient funds")
    if card.is_expired():
        return error("Card expired")
    if not card.cvv_valid():
        return error("Invalid CVV")
    if not rate_limit_ok():
        return error("Rate limit")

    # Happy path (single level)
    return charge(card, amount)
```

**Nesting Reduction**: 6 → 1 (83% reduction)

---

### 3. Extract Conditional Logic (Readability)

**Pattern**: Complex boolean conditions
**Solution**: Extract to named boolean variables

**Example**:
```python
# BEFORE
if user.role == 'admin' and not user.is_suspended and user.email_verified and (user.last_login is None or (datetime.now() - user.last_login).days < 90):
    grant_access()

# AFTER
is_admin = user.role == 'admin'
is_active = not user.is_suspended
is_verified = user.email_verified
is_recent_login = user.last_login and (datetime.now() - user.last_login).days < 90

if is_admin and is_active and is_verified and is_recent_login:
    grant_access()
```

---

### 4. Replace Type Checking with Polymorphism

**Pattern**: Multiple if/elif type checks
**Solution**: Use polymorphism (strategy pattern)

**Example**:
```python
# BEFORE (Complexity: 8)
def process_payment(payment_type, amount, details):
    if payment_type == 'credit_card':
        if validate_card(details):
            charge_card(details, amount)
    elif payment_type == 'paypal':
        if validate_paypal(details):
            charge_paypal(details, amount)
    elif payment_type == 'bank_transfer':
        if validate_bank(details):
            initiate_transfer(details, amount)
    elif payment_type == 'cryptocurrency':
        if validate_crypto(details):
            send_crypto(details, amount)

# AFTER (Complexity: 2)
def process_payment(payment_method, amount):
    """Uses polymorphism instead of type checking"""
    payment_method.validate()  # Polymorphic call
    payment_method.charge(amount)  # Polymorphic call

# Each payment type implements validate() and charge()
class CreditCardPayment:
    def validate(self): ...
    def charge(self, amount): ...

class PayPalPayment:
    def validate(self): ...
    def charge(self, amount): ...
```

---

### 5. Split Long Functions

**Pattern**: Function > 50 lines
**Solution**: Split by logical responsibility

**Example**:
```python
# BEFORE (76 lines)
def register_user(email, password, profile_data):
    # Email validation (10 lines)
    # Password validation (15 lines)
    # Profile validation (12 lines)
    # Create user record (8 lines)
    # Send welcome email (10 lines)
    # Setup user preferences (8 lines)
    # Log registration (5 lines)
    # Return result (8 lines)

# AFTER (5 functions × ~15 lines each)
def register_user(email, password, profile_data):
    validate_registration_data(email, password, profile_data)
    user = create_user_record(email, password, profile_data)
    setup_user_account(user)
    notify_user(user)
    return registration_success(user)

def validate_registration_data(email, password, profile_data): ...
def create_user_record(email, password, profile_data): ...
def setup_user_account(user): ...
def notify_user(user): ...
def registration_success(user): ...
```

---

## Refactoring Algorithm

For each violation in the complexity report:

```
1. Identify the refactoring technique:
   - Complexity > 10 → Extract functions
   - Nesting > 3 → Early returns
   - Complex conditions → Extract to named booleans
   - Type checking → Polymorphism
   - Length > 50 → Split function

2. Apply refactoring:
   a. Create new extracted functions
   b. Update original function to call extracted functions
   c. Ensure all logic preserved

3. Verify:
   a. Run all tests
   b. If tests fail → ROLLBACK
   c. If tests pass → Re-check complexity
   d. If complexity still > 10 → Apply next technique

4. Repeat until complexity ≤ 10
```

---

## Output Format

```
[Invoking: simplify-complex-code skill (Actuator)]

Safety checks:
  ✓ All tests passing (47/47)
  ✓ Complexity report available
  ✓ User confirmed refactoring

Refactoring auth_service.py...

Target: login() - Complexity 18 → 6

Step 1: Extracting validation logic...
  ✓ Created: validate_login_input() (complexity: 3)
  ✓ Created: get_user_or_fail() (complexity: 2)

Step 2: Extracting authentication logic...
  ✓ Created: authenticate_user() (complexity: 3)
  ✓ Created: verify_2fa_if_required() (complexity: 2)

Step 3: Refactoring login()...
  ✓ Replaced nested ifs with function calls
  ✓ Reduced complexity: 18 → 6

Running tests to verify...
  ✓ All 47 tests passing

Re-checking complexity...
  [Invoking: detect-complexity skill]
  ✓ login() complexity: 6 (threshold: 10) ✓
  ✓ Max complexity: 6
  ✓ All functions ≤ 10

Target: process_payment() - Nesting 6 → 1

Step 1: Applying early returns pattern...
  ✓ Inverted conditions to guard clauses
  ✓ Reduced nesting: 6 levels → 1 level
  ✓ Complexity: 12 → 7

Running tests to verify...
  ✓ All 51 tests passing

Summary:
  Functions refactored: 2
  Complexity reduced: Max 18 → 7 (61% reduction)
  Nesting reduced: Max 6 → 1 (83% reduction)
  New functions extracted: 4
  Lines changed: 95

Homeostasis achieved! Max complexity ≤ 10 ✓

Changes ready to commit.
```

---

## Safety Checks

Before refactoring:
1. **All tests passing** - Don't refactor if tests failing
2. **Backup exists** - Ensure git working directory clean
3. **User confirmation** (if auto_simplify=false)

After **EACH** refactoring step:
1. **Run all tests**
2. **If tests fail**:
   - ROLLBACK the change
   - Try different refactoring technique
   - If all techniques fail → Report manual intervention needed

---

## Error Handling

### If tests fail after refactoring:

```
❌ ROLLBACK: Tests failed after refactoring

Failed tests:
  - test_login_with_locked_account

Analysis:
  Extracted function 'get_user_or_fail()' doesn't handle lockout expiry correctly.

Root cause: Logic error in extraction

Restoring original function...
  ✓ Restored: login()

Trying alternative refactoring...
  [Applying early returns pattern instead]
  ✓ Tests passing

Recommendation: Manual review of lockout logic
```

---

## Configuration

```yaml
plugins:
  - name: "@aisdlc/code-skills"
    config:
      complexity_simplification:
        auto_simplify: false             # Ask before refactoring (default)
        run_tests_after: true            # Always verify (required)
        complexity_threshold: 10
        max_refactoring_attempts: 3     # Try 3 different techniques
        prefer_technique:                # Preferred order
          - "extract_functions"
          - "early_returns"
          - "extract_conditionals"
```

---

## Prerequisites Check

Before invoking this skill, ensure:
1. `detect-complexity` skill has run
2. Complexity report is available
3. Tests are passing (GREEN)

If prerequisites not met, invoke:
- `detect-complexity` (if no report available)
- Return error if tests not passing

---

## Next Steps

After simplification is complete:
1. Re-run `detect-complexity` to verify homeostasis
2. If clean → Invoke `commit-with-req-tag` to commit refactoring
3. If still violations → Report manual intervention needed

---

## Notes

**Why automatic refactoring is safe**:
- Only applies proven, well-understood refactoring techniques
- Always runs tests after each step
- Automatic rollback if tests fail
- User can review changes before commit

**Why complexity matters**:
- Complexity 18 → ~262,000 possible paths (2^18)
- Complexity 6 → ~64 possible paths (2^6)
- 99.98% reduction in test case combinations needed

**Principle #3**: "Modular & Maintainable"
- Single responsibility per function → Low complexity
- Focused functions → Easy to test
- Simple logic → Easy to understand

**Homeostasis Goal**:
```yaml
desired_state:
  max_cyclomatic_complexity: 10
```

**"Excellence or nothing"** 🔥
