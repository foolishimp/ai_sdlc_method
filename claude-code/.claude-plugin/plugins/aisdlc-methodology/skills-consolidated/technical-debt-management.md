---
name: technical-debt-management
description: Detect and eliminate technical debt - unused code, complexity, duplication. Consolidates detect-complexity, detect-unused-code, prune-unused-code, simplify-complex-code.
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
---

# Technical Debt Management

**Skill Type**: Quality Gate (Code Stage)
**Purpose**: Detect and eliminate technical debt (Principle #6: No Legacy Baggage)
**Consolidates**: detect-complexity, detect-unused-code, prune-unused-code, simplify-complex-code

---

## When to Use This Skill

Use this skill when:
- REFACTOR phase of TDD/BDD workflow
- Code review identifies debt
- Codebase maintenance/cleanup
- Before major releases
- Technical debt threshold exceeded

---

## Technical Debt Categories

### 1. Unused Code

**What to look for**:
- Unused imports
- Dead functions (zero callers)
- Unused variables
- Commented-out code
- Orphaned test files

**Detection** (Python):
```bash
# Unused imports
pylint --disable=all --enable=W0611 src/

# Unused variables
pylint --disable=all --enable=W0612 src/

# Dead code (comprehensive)
vulture src/ --min-confidence 80
```

**Detection** (TypeScript):
```bash
# Unused code
npx ts-prune src/

# Dead exports
npx unimported
```

**Pruning Strategy**:
```
1. BACKUP: Ensure git commit before pruning
2. DETECT: Run detection tools
3. VERIFY: Confirm code is truly unused
4. DELETE: Remove unused code (don't comment)
5. TEST: Run full test suite
6. COMMIT: "REFACTOR: Remove dead code"
```

---

### 2. High Complexity

**Metrics**:
- **Cyclomatic Complexity**: Number of decision points
  - 1-10: Simple, low risk
  - 11-20: Moderate complexity
  - 21-50: High complexity, refactor
  - 50+: Critical, must refactor

- **Cognitive Complexity**: Mental effort to understand
  - Sonar standard: max 15

**Detection** (Python):
```bash
# Cyclomatic complexity
radon cc src/ -a -s

# Show functions with complexity > 10
radon cc src/ -a -s --min C

# Cognitive complexity
flake8 --max-cognitive-complexity 15 src/
```

**Detection** (TypeScript):
```bash
# Using ESLint
npx eslint src/ --rule 'complexity: ["error", 10]'
```

**Simplification Patterns**:

**Pattern 1: Extract Method**
```python
# BEFORE: Complex function
def process_order(order):
    # 50+ lines of code
    # Multiple responsibilities
    pass

# AFTER: Extracted methods
def process_order(order):
    validated = validate_order(order)
    priced = calculate_pricing(validated)
    return submit_order(priced)

def validate_order(order):
    # Single responsibility
    pass

def calculate_pricing(order):
    # Single responsibility
    pass

def submit_order(order):
    # Single responsibility
    pass
```

**Pattern 2: Replace Conditionals with Polymorphism**
```python
# BEFORE: Complex if/else
def calculate_discount(customer_type, amount):
    if customer_type == 'gold':
        return amount * 0.20
    elif customer_type == 'silver':
        return amount * 0.10
    elif customer_type == 'bronze':
        return amount * 0.05
    else:
        return 0

# AFTER: Strategy pattern
class DiscountStrategy:
    def calculate(self, amount): raise NotImplementedError

class GoldDiscount(DiscountStrategy):
    def calculate(self, amount): return amount * 0.20

class SilverDiscount(DiscountStrategy):
    def calculate(self, amount): return amount * 0.10

STRATEGIES = {
    'gold': GoldDiscount(),
    'silver': SilverDiscount(),
    'bronze': BronzeDiscount(),
}

def calculate_discount(customer_type, amount):
    strategy = STRATEGIES.get(customer_type, NoDiscount())
    return strategy.calculate(amount)
```

**Pattern 3: Early Return**
```python
# BEFORE: Deep nesting
def process(data):
    if data:
        if data.is_valid:
            if data.has_permission:
                # actual logic here
                return result
            else:
                return error_no_permission
        else:
            return error_invalid
    else:
        return error_no_data

# AFTER: Guard clauses
def process(data):
    if not data:
        return error_no_data
    if not data.is_valid:
        return error_invalid
    if not data.has_permission:
        return error_no_permission

    # actual logic here
    return result
```

---

### 3. Code Duplication

**Detection**:
```bash
# Python
pylint --disable=all --enable=R0801 src/

# TypeScript
npx jscpd src/ --min-lines 5 --min-tokens 50
```

**Deduplication Patterns**:

**Pattern 1: Extract Common Function**
```python
# BEFORE: Duplicated validation
def create_user(email, password):
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise ValueError("Invalid email")
    # ...

def update_user(user_id, email):
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise ValueError("Invalid email")
    # ...

# AFTER: Extracted function
def validate_email(email: str) -> str:
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise ValueError("Invalid email")
    return email

def create_user(email, password):
    email = validate_email(email)
    # ...

def update_user(user_id, email):
    email = validate_email(email)
    # ...
```

**Pattern 2: Template Method**
```python
# BEFORE: Duplicated workflow
def process_credit_card(payment):
    validate(payment)
    # credit card specific logic
    log(payment)
    notify(payment)

def process_paypal(payment):
    validate(payment)
    # paypal specific logic
    log(payment)
    notify(payment)

# AFTER: Template method
class PaymentProcessor:
    def process(self, payment):
        self.validate(payment)
        self.execute(payment)  # Override in subclass
        self.log(payment)
        self.notify(payment)

    def execute(self, payment):
        raise NotImplementedError

class CreditCardProcessor(PaymentProcessor):
    def execute(self, payment):
        # credit card specific logic
        pass
```

---

### 4. Outdated Dependencies

**Detection**:
```bash
# Python
pip list --outdated
pip-audit  # Security vulnerabilities

# Node.js
npm outdated
npm audit

# Security vulnerabilities
safety check  # Python
```

**Update Strategy**:
```
1. LIST: Check outdated dependencies
2. REVIEW: Read changelogs for breaking changes
3. UPDATE: One dependency at a time
4. TEST: Run full test suite
5. COMMIT: "chore: Update dependency X to v2.0"
```

---

## Complete Debt Scan Workflow

```bash
# 1. Unused code
echo "=== Unused Code ==="
vulture src/ --min-confidence 80

# 2. Complexity
echo "=== High Complexity ==="
radon cc src/ -a -s --min C

# 3. Duplication
echo "=== Code Duplication ==="
pylint --disable=all --enable=R0801 src/

# 4. Outdated deps
echo "=== Outdated Dependencies ==="
pip list --outdated

# 5. Security
echo "=== Security Vulnerabilities ==="
pip-audit
```

---

## Output Format

```
[TECHNICAL DEBT SCAN]

Scan Date: 2025-12-03
Codebase: src/

=== Unused Code ===
Found: 15 items

  Dead Functions (5):
    - src/utils/helpers.py:45 - format_legacy() (0 callers)
    - src/auth/validators.py:120 - validate_v1() (0 callers)
    ...

  Unused Imports (8):
    - src/main.py:3 - import os (never used)
    - src/services/payment.py:5 - from decimal import *
    ...

  Commented Code (2):
    - src/api/routes.py:78-95 - Old endpoint
    - src/models/user.py:34-40 - Deprecated field

=== High Complexity ===
Found: 3 functions above threshold

  Critical (CC > 20):
    - src/services/order.py:process_order() - CC=32

  High (CC 11-20):
    - src/auth/login.py:authenticate() - CC=15
    - src/api/handlers.py:handle_request() - CC=12

=== Code Duplication ===
Found: 2 duplicated blocks

  Block 1: 15 lines (3 locations)
    - src/validators/email.py:10-25
    - src/validators/user.py:20-35
    - src/api/schemas.py:45-60

  Block 2: 8 lines (2 locations)
    - src/services/auth.py:50-58
    - src/services/session.py:30-38

=== Summary ===
Total Debt Items: 20
  - Unused Code: 15 (Delete)
  - High Complexity: 3 (Refactor)
  - Duplication: 2 (Extract)

Estimated Cleanup: 2-3 hours

Recommendation: Address before next release
```

---

## Pruning Workflow

**Step 1: Detect**
```bash
# Run full scan
./scripts/debt-scan.sh
```

**Step 2: Prioritize**
```
Priority 1: Security vulnerabilities
Priority 2: Critical complexity (CC > 20)
Priority 3: Dead code (zero callers)
Priority 4: High complexity (CC 11-20)
Priority 5: Duplication
Priority 6: Outdated dependencies
```

**Step 3: Prune**
```bash
# Delete dead code
git rm src/utils/helpers.py  # If entire file unused

# Or edit to remove specific functions
# Edit file, remove dead functions, run tests

# Commit
git commit -m "REFACTOR: Remove dead code

Deleted:
- format_legacy() - no callers since v2.0
- validate_v1() - replaced by validate_v2()

Tests: All passing
"
```

**Step 4: Verify**
```bash
# Run full test suite
pytest tests/ -v

# Run debt scan again
./scripts/debt-scan.sh
# Should show reduced debt
```

---

## Configuration

```yaml
# .claude/plugins.yml
plugins:
  - name: "@aisdlc/aisdlc-methodology"
    config:
      technical_debt:
        complexity_threshold: 10
        cognitive_complexity_threshold: 15
        duplication_min_lines: 5
        unused_code_confidence: 80
        block_on_critical: true  # Block deploy if CC > 20
        scan_on_commit: true
        scan_on_pr: true
```

---

## Homeostasis Behavior

**If debt exceeds threshold**:
- Detect: CC > 20 or security vulnerability
- Signal: "Technical debt critical"
- Action: Block deployment until fixed
- Require: Cleanup before proceeding

**If debt accumulating**:
- Detect: Debt increasing over sprints
- Signal: "Allocate cleanup time"
- Action: Add debt cleanup to sprint

---

## Key Principles Applied

- **No Legacy Baggage**: Delete, don't comment
- **Fail Fast**: Detect debt early
- **Perfectionist Excellence**: Zero tolerance for critical debt

**"Excellence or nothing"**
