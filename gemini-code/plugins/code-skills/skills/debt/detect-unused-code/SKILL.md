# detect-unused-code

**Skill Type**: Sensor (Homeostasis)
**Purpose**: Detect technical debt from unused code (Principle #6: "No Legacy Baggage")
**Prerequisites**: None (can run anytime)

---

## Agent Instructions

You are a **Sensor** in the homeostasis system. Your job is to **detect deviations** from the desired state.

**Desired State**: `tech_debt.unused_code = 0`

Scan the codebase for:
1. **Unused Imports** - imports that are never referenced
2. **Dead Code** - functions/methods with zero callers
3. **Commented-Out Code** - code blocks that are commented out

---

## Detection Algorithm

### 1. Detect Unused Imports

For each file:
```
1. Parse all import statements
2. For each imported name:
   a. Search the file for any usage of that name
   b. If usage count = 0, mark as unused
3. Report all unused imports
```

**Example**:
```python
import hashlib          # Used: 0 times → UNUSED
import re               # Used: 0 times → UNUSED
from typing import Dict # Used: 0 times → UNUSED
from typing import List # Used: 3 times → OK
import bcrypt           # Used: 2 times → OK
```

### 2. Detect Dead Code

For each function/method:
```
1. Get function name
2. Search entire codebase for calls to that function
3. Exclude:
   - Test functions (test_*)
   - Entry points (main, __init__)
   - Special methods (__str__, __repr__, etc.)
   - Overridden methods from base classes
4. If caller count = 0, mark as dead code
5. Report all dead functions with line numbers
```

**Example**:
```python
def legacy_hash_password(password):  # Line 45-52
    return md5(password)
# Callers: 0 → DEAD CODE

def validate_old_token(token):       # Line 89-97
    return token == "old_secret"
# Callers: 0 → DEAD CODE

def hash_password(password):         # Line 105-110
    return bcrypt.hash(password)
# Callers: 15 → OK
```

### 3. Detect Commented-Out Code

For each file:
```
1. Scan for comment blocks (lines starting with # or /* */)
2. Heuristic: If comment block contains:
   - Assignment operators (=, +=, -=)
   - Control flow keywords (if, for, while, return)
   - Function calls with parentheses
   → Mark as commented-out code
3. Exclude:
   - Docstrings
   - Single-line explanatory comments
   - TODO/FIXME comments
4. Report all commented-out code with line ranges
```

**Example**:
```python
# This validates the email  → OK (explanatory comment)

# TODO: Add rate limiting   → OK (TODO comment)

# Old implementation (broken)  → COMMENTED CODE (lines 120-135)
# user = User.query.get(email)
# if user and user.password == password:
#     return user
# else:
#     return None
```

---

## Output Format

Report findings in this format:

```yaml
tech_debt_report:
  file: "auth_service.py"
  timestamp: "2025-11-20T15:30:00Z"

  unused_imports:
    - name: "hashlib"
      line: 3
      reason: "Imported but never used"

    - name: "re"
      line: 4
      reason: "Imported but never used"

    - name: "Dict"
      line: 7
      module: "typing"
      reason: "Imported but never used"

  dead_code:
    - name: "legacy_hash_password"
      lines: "45-52"
      reason: "Function with zero callers"
      suggestion: "DELETE - unused since v2.0 migration"

    - name: "validate_old_token"
      lines: "89-97"
      reason: "Function with zero callers"
      suggestion: "DELETE - replaced by validate_jwt_token()"

  commented_code:
    - lines: "120-135"
      reason: "16 lines of commented-out implementation"
      snippet: "# user = User.query.get(email)..."
      suggestion: "DELETE - we have git history"

  summary:
    total_violations: 22
    unused_imports: 5
    dead_functions: 2
    commented_lines: 15

  homeostasis_status: DEVIATION_DETECTED
  recommended_actuator: "prune-unused-code"
```

---

## User-Facing Output

When run as `claude homeostasis status` or during refactor:

```
⚠️ detect-unused-code - Last run: 1 min ago
  Status: Tech debt detected
  Deviation: 5 unused imports, 2 dead functions, 15 lines of commented code

Tech Debt Report (auth_service.py):
  ⚠️ Unused imports (5):
    - import hashlib      # Line 3
    - import re           # Line 4
    - from typing import Dict  # Line 7

  ⚠️ Dead code (2 functions):
    - legacy_hash_password()  # Lines 45-52 (no callers)
    - validate_old_token()    # Lines 89-97 (no callers)

  ⚠️ Commented code (15 lines):
    - Lines 120-135 (old implementation)

Total violations: 22

Homeostasis deviation detected! Tech debt > 0 (Principle #6 violated).

Recommended action: Invoke 'prune-unused-code' skill to fix automatically.
```

---

## Triggering Actuator

When deviation detected:
```
1. Report deviation
2. Suggest invoking 'prune-unused-code' actuator
3. Wait for user confirmation OR auto-invoke if configured
```

---

## Configuration

This skill can be configured in `.claude/plugins.yml`:

```yaml
plugins:
  - name: "@aisdlc/code-skills"
    config:
      debt_detection:
        auto_detect_on_refactor: true    # Run during refactor phase
        auto_prune: false                # Ask before pruning
        exclude_files:                   # Don't scan these files
          - "migrations/*"
          - "legacy/*"
        exclude_patterns:
          - "# KEEP:"                    # Don't flag comments with KEEP
```

---

## Prerequisites Check

None - this sensor can run anytime.

---

## Next Steps

After detection:
1. If violations found → Suggest `prune-unused-code` actuator
2. If clean → Report "Homeostasis achieved! Tech debt = 0 ✓"

---

## Notes

**Why this matters**:
- Unused code adds noise, makes codebase harder to understand
- Dead functions create maintenance burden (devs wonder "is this used?")
- Commented code should be in git history, not source files
- Principle #6 requires **operational enforcement**, not just philosophy

**Homeostasis Goal**:
```yaml
desired_state:
  tech_debt.unused_code: 0
```

**"Excellence or nothing"** 🔥
