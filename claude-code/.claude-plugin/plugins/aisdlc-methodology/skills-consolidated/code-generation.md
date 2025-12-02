---
name: code-generation
description: Auto-generate code from business rules, constraints, formulas, and validators. Consolidates autogenerate-constraints, autogenerate-formulas, autogenerate-from-business-rules, autogenerate-validators.
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
---

# Code Generation

**Skill Type**: Actuator (Code Stage)
**Purpose**: Auto-generate implementation code from structured specifications
**Consolidates**: autogenerate-constraints, autogenerate-formulas, autogenerate-from-business-rules, autogenerate-validators

---

## When to Use This Skill

Use this skill when:
- Requirements have BR-*, C-*, F-* specifications
- Need to generate validators from constraints
- Need to implement business rule logic
- Need to implement calculation formulas
- Want consistent, traceable code generation

---

## Code Generation Types

### 1. Generate from Business Rules (BR-*)

**Input**:
```yaml
REQ-F-AUTH-001:
  BR-001: Email must be valid format (regex: ^[^@]+@[^@]+\.[^@]+$)
  BR-002: Password minimum 12 characters
  BR-003: Max 3 login attempts, then 15-minute lockout
```

**Output** (Python):
```python
# validators/auth_validators.py

# Generated from: REQ-F-AUTH-001
# Business Rules: BR-001, BR-002, BR-003

import re
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

# BR-001: Email validation
EMAIL_PATTERN = re.compile(r'^[^@]+@[^@]+\.[^@]+$')

def validate_email(email: str) -> bool:
    """Validate email format.

    Implements: BR-001 (Email must be valid format)
    Requirement: REQ-F-AUTH-001
    """
    if not email:
        return False
    return bool(EMAIL_PATTERN.match(email))


# BR-002: Password minimum length
PASSWORD_MIN_LENGTH = 12

def validate_password_length(password: str) -> bool:
    """Validate password meets minimum length.

    Implements: BR-002 (Password minimum 12 characters)
    Requirement: REQ-F-AUTH-001
    """
    return len(password) >= PASSWORD_MIN_LENGTH


# BR-003: Account lockout
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_DURATION_MINUTES = 15

@dataclass
class LockoutStatus:
    is_locked: bool
    locked_until: Optional[datetime] = None
    attempts_remaining: int = MAX_LOGIN_ATTEMPTS

def check_account_lockout(
    login_attempts: int,
    locked_until: Optional[datetime]
) -> LockoutStatus:
    """Check if account is locked due to failed attempts.

    Implements: BR-003 (Max 3 attempts, 15-minute lockout)
    Requirement: REQ-F-AUTH-001
    """
    now = datetime.utcnow()

    # Check if currently locked
    if locked_until and locked_until > now:
        return LockoutStatus(
            is_locked=True,
            locked_until=locked_until,
            attempts_remaining=0
        )

    # Check if should be locked
    if login_attempts >= MAX_LOGIN_ATTEMPTS:
        new_locked_until = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        return LockoutStatus(
            is_locked=True,
            locked_until=new_locked_until,
            attempts_remaining=0
        )

    return LockoutStatus(
        is_locked=False,
        attempts_remaining=MAX_LOGIN_ATTEMPTS - login_attempts
    )
```

---

### 2. Generate from Constraints (C-*)

**Input**:
```yaml
REQ-F-AUTH-001:
  C-001: Response time < 500ms
  C-002: Must use HTTPS
  C-003: Password must be hashed (bcrypt, cost factor 12)
  C-004: Must support 10,000+ concurrent users
```

**Output** (Python):
```python
# constraints/auth_constraints.py

# Generated from: REQ-F-AUTH-001
# Constraints: C-001, C-002, C-003, C-004

import bcrypt
import functools
import time
from typing import Callable, TypeVar, Any

T = TypeVar('T')

# C-001: Response time constraint
MAX_RESPONSE_TIME_MS = 500

def enforce_response_time(max_ms: int = MAX_RESPONSE_TIME_MS):
    """Decorator to enforce response time constraint.

    Implements: C-001 (Response time < 500ms)
    Requirement: REQ-F-AUTH-001
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000

            if elapsed_ms > max_ms:
                # Log warning but don't fail
                import logging
                logging.warning(
                    f"C-001 violation: {func.__name__} took {elapsed_ms:.2f}ms "
                    f"(max: {max_ms}ms)"
                )
            return result
        return wrapper
    return decorator


# C-002: HTTPS enforcement
def require_https(url: str) -> str:
    """Ensure URL uses HTTPS.

    Implements: C-002 (Must use HTTPS)
    Requirement: REQ-F-AUTH-001
    """
    if url.startswith('http://'):
        return url.replace('http://', 'https://', 1)
    if not url.startswith('https://'):
        return f'https://{url}'
    return url


# C-003: Password hashing
BCRYPT_COST_FACTOR = 12

def hash_password(password: str) -> str:
    """Hash password using bcrypt.

    Implements: C-003 (bcrypt, cost factor 12)
    Requirement: REQ-F-AUTH-001
    """
    salt = bcrypt.gensalt(rounds=BCRYPT_COST_FACTOR)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash.

    Implements: C-003 (bcrypt verification)
    Requirement: REQ-F-AUTH-001
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# C-004: Concurrency constraint (design note)
# Note: 10,000+ concurrent users requires:
# - Stateless design (JWT tokens)
# - Connection pooling
# - Horizontal scaling
# This is enforced at architecture level, not code level.
```

---

### 3. Generate from Formulas (F-*)

**Input**:
```yaml
REQ-F-PORTAL-001: View Balance
  F-001: available_balance = total_balance - pending_holds
  F-002: display_format = currency_symbol + format(amount, 2 decimals)

REQ-F-PAYMENT-001: Calculate Tax
  F-003: tax_amount = subtotal * tax_rate
  F-004: total = subtotal + tax_amount + shipping
  F-005: discount = min(subtotal * discount_percent, max_discount)
```

**Output** (Python):
```python
# calculations/financial_formulas.py

# Generated from: REQ-F-PORTAL-001, REQ-F-PAYMENT-001
# Formulas: F-001, F-002, F-003, F-004, F-005

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

# F-001: Available balance calculation
def calculate_available_balance(
    total_balance: Decimal,
    pending_holds: Decimal
) -> Decimal:
    """Calculate available balance.

    Formula: available_balance = total_balance - pending_holds
    Implements: F-001
    Requirement: REQ-F-PORTAL-001
    """
    return total_balance - pending_holds


# F-002: Currency display formatting
def format_currency(
    amount: Decimal,
    currency_symbol: str = '$',
    decimal_places: int = 2
) -> str:
    """Format amount as currency string.

    Formula: currency_symbol + format(amount, 2 decimals)
    Implements: F-002
    Requirement: REQ-F-PORTAL-001
    """
    quantized = amount.quantize(
        Decimal(f'0.{"0" * decimal_places}'),
        rounding=ROUND_HALF_UP
    )
    return f'{currency_symbol}{quantized:,.{decimal_places}f}'


# F-003: Tax calculation
def calculate_tax(
    subtotal: Decimal,
    tax_rate: Decimal
) -> Decimal:
    """Calculate tax amount.

    Formula: tax_amount = subtotal * tax_rate
    Implements: F-003
    Requirement: REQ-F-PAYMENT-001
    """
    return (subtotal * tax_rate).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )


# F-004: Order total calculation
def calculate_order_total(
    subtotal: Decimal,
    tax_amount: Decimal,
    shipping: Decimal
) -> Decimal:
    """Calculate order total.

    Formula: total = subtotal + tax_amount + shipping
    Implements: F-004
    Requirement: REQ-F-PAYMENT-001
    """
    return subtotal + tax_amount + shipping


# F-005: Discount calculation with cap
def calculate_discount(
    subtotal: Decimal,
    discount_percent: Decimal,
    max_discount: Optional[Decimal] = None
) -> Decimal:
    """Calculate discount with optional maximum cap.

    Formula: discount = min(subtotal * discount_percent, max_discount)
    Implements: F-005
    Requirement: REQ-F-PAYMENT-001
    """
    calculated_discount = subtotal * discount_percent

    if max_discount is not None:
        return min(calculated_discount, max_discount)

    return calculated_discount.quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )
```

---

### 4. Generate Validators (Combined)

**Input**:
```yaml
REQ-DATA-VAL-001: Email Validation
  Pattern: ^[^@]+@[^@]+\.[^@]+$
  Max Length: 255
  Required: true

REQ-DATA-VAL-002: Password Validation
  Min Length: 12
  Max Length: 128
  Requires: uppercase, lowercase, digit, special
  Required: true
```

**Output** (Python with Pydantic):
```python
# validators/input_validators.py

# Generated from: REQ-DATA-VAL-001, REQ-DATA-VAL-002

import re
from pydantic import BaseModel, field_validator, Field
from typing import Annotated

# REQ-DATA-VAL-001: Email validation
EMAIL_PATTERN = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
EMAIL_MAX_LENGTH = 255

# REQ-DATA-VAL-002: Password validation
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
PASSWORD_REQUIRES_UPPERCASE = True
PASSWORD_REQUIRES_LOWERCASE = True
PASSWORD_REQUIRES_DIGIT = True
PASSWORD_REQUIRES_SPECIAL = True


class LoginRequest(BaseModel):
    """Login request with validated email and password.

    Validates: REQ-DATA-VAL-001, REQ-DATA-VAL-002
    """

    email: Annotated[str, Field(
        max_length=EMAIL_MAX_LENGTH,
        description="User email address"
    )]

    password: Annotated[str, Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        description="User password"
    )]

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Validate email format.

        Implements: REQ-DATA-VAL-001
        """
        if not EMAIL_PATTERN.match(v):
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password complexity.

        Implements: REQ-DATA-VAL-002
        """
        errors = []

        if PASSWORD_REQUIRES_UPPERCASE and not any(c.isupper() for c in v):
            errors.append('must contain uppercase letter')

        if PASSWORD_REQUIRES_LOWERCASE and not any(c.islower() for c in v):
            errors.append('must contain lowercase letter')

        if PASSWORD_REQUIRES_DIGIT and not any(c.isdigit() for c in v):
            errors.append('must contain digit')

        if PASSWORD_REQUIRES_SPECIAL:
            special_chars = set('!@#$%^&*()_+-=[]{}|;:,.<>?')
            if not any(c in special_chars for c in v):
                errors.append('must contain special character')

        if errors:
            raise ValueError(f'Password {", ".join(errors)}')

        return v
```

---

## Output Format

```
[CODE GENERATION - REQ-F-AUTH-001]

Generated from:
  Business Rules: BR-001, BR-002, BR-003
  Constraints: C-001, C-002, C-003, C-004
  Formulas: (none for this requirement)

Files Created:
  + validators/auth_validators.py
    - validate_email() → BR-001
    - validate_password_length() → BR-002
    - check_account_lockout() → BR-003

  + constraints/auth_constraints.py
    - enforce_response_time() → C-001
    - require_https() → C-002
    - hash_password() → C-003
    - verify_password() → C-003

Traceability:
  All functions tagged with REQ-* and BR-*/C-*/F-*

Code Generation Complete!
  Next: Run TDD workflow to add tests
```

---

## Usage Patterns

### Generate All at Once
```
"Generate code for REQ-F-AUTH-001 including all BR-*, C-*, and F-*"
```

### Generate Specific Type
```
"Generate validators from BR-001 and BR-002"
"Generate calculation functions from F-001, F-002, F-003"
```

### Generate with Tests
```
"Generate code for BR-001 with corresponding unit tests"
```

---

## Configuration

```yaml
# .claude/plugins.yml
plugins:
  - name: "@aisdlc/aisdlc-methodology"
    config:
      code_generation:
        include_docstrings: true
        include_type_hints: true
        include_traceability_comments: true
        validation_framework: "pydantic"  # pydantic | marshmallow | custom
        test_framework: "pytest"
        generate_tests: true
```

---

## Homeostasis Behavior

**If BR-*/C-*/F-* incomplete**:
- Detect: Missing specifications
- Signal: "Need disambiguation"
- Action: Use `requirements-extraction` skill first

**If generated code fails tests**:
- Detect: Test failures
- Signal: "Generated code needs adjustment"
- Action: Fix implementation to match specification

---

## Key Principles Applied

- **Test Driven Development**: Generate tests alongside code
- **Modular & Maintainable**: Single responsibility per function
- **No Legacy Baggage**: Clean, typed, documented code

**"Excellence or nothing"**
