# prune-unused-code

**Skill Type**: Actuator (Homeostasis)
**Purpose**: Automatically remove unused code to restore homeostasis (Principle #6: "No Legacy Baggage")
**Prerequisites**:
- `detect-unused-code` skill must have run
- Tech debt report available

---

## Agent Instructions

You are an **Actuator** in the homeostasis system. Your job is to **correct deviations** and restore the desired state.

**Desired State**: `tech_debt.unused_code = 0`

Based on the tech debt report from `detect-unused-code`, automatically:
1. **Delete Unused Imports**
2. **Remove Dead Code Functions**
3. **Delete Commented-Out Code**

---

## Pruning Algorithm

### 1. Delete Unused Imports

For each unused import in the report:
```
1. Locate the import statement by line number
2. Delete the entire line
3. If it's a "from X import A, B, C" statement where only some are unused:
   a. Keep only the used imports
   b. If all are unused, delete the entire line
4. Track the deletion
```

**Example**:
```python
# BEFORE
import hashlib          # ❌ UNUSED - DELETE
import re               # ❌ UNUSED - DELETE
from typing import Dict, List  # ⚠️ Only Dict unused
import bcrypt           # ✓ USED - KEEP

# AFTER
from typing import List  # ✓ Kept only what's used
import bcrypt           # ✓ USED - KEEP
```

**Changes**:
```
✓ Deleted: import hashlib (line 3)
✓ Deleted: import re (line 4)
✓ Updated: from typing import Dict, List → from typing import List (line 7)
```

### 2. Remove Dead Code

For each dead function in the report:
```
1. Locate function by line range (e.g., lines 45-52)
2. Delete all lines in that range
3. Delete any blank lines immediately after (cleanup)
4. Track the deletion (function name, line count)
```

**Example**:
```python
# BEFORE
def legacy_hash_password(password):  # ❌ DEAD CODE - DELETE
    """Old MD5 hashing (insecure)"""
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()


def validate_old_token(token):       # ❌ DEAD CODE - DELETE
    """Deprecated token validation"""
    return token == "old_secret"


def hash_password(password):         # ✓ USED - KEEP
    return bcrypt.hash(password)

# AFTER
def hash_password(password):         # ✓ USED - KEEP
    return bcrypt.hash(password)
```

**Changes**:
```
✓ Deleted: legacy_hash_password() (8 lines: 45-52)
✓ Deleted: validate_old_token() (9 lines: 89-97)
✓ Cleaned up: 2 blank lines
Total: 19 lines deleted
```

### 3. Delete Commented-Out Code

For each commented code block in the report:
```
1. Locate by line range (e.g., lines 120-135)
2. Verify it's actually commented-out code (not a docstring or TODO)
3. Delete all lines in that range
4. Track the deletion
```

**Example**:
```python
# BEFORE
def login(email, password):
    # Old implementation (broken)     # ❌ COMMENTED CODE - DELETE
    # user = User.query.get(email)
    # if user and user.password == password:
    #     return user
    # else:
    #     return None

    # New implementation
    user = User.get_by_email(email)
    return authenticate(user, password)

# AFTER
def login(email, password):
    # New implementation
    user = User.get_by_email(email)
    return authenticate(user, password)
```

**Changes**:
```
✓ Deleted: Lines 120-126 (7 lines of commented code)
```

---

## Safety Checks

Before pruning, verify:

1. **All tests are passing** - Don't prune if tests are failing
2. **Backup exists** - Ensure git working directory is clean OR create backup
3. **User confirmation** (if auto_prune=false) - Ask before destructive changes

After pruning:
1. **Run all tests** - Verify nothing broke
2. **If tests fail**:
   - ROLLBACK all changes
   - Report failure
   - DO NOT COMMIT

---

## Output Format

```
[Invoking: prune-unused-code skill (Actuator)]

Safety checks:
  ✓ All tests passing (47/47)
  ✓ Git working directory clean
  ✓ User confirmed pruning

Pruning auth_service.py...

Removing unused imports...
  ✓ Deleted: import hashlib (line 3)
  ✓ Deleted: import re (line 4)
  ✓ Updated: from typing import Dict, List → from typing import List (line 7)

Removing dead code...
  ✓ Deleted: legacy_hash_password() (8 lines: 45-52)
  ✓ Deleted: validate_old_token() (9 lines: 89-97)

Removing commented code...
  ✓ Deleted: Lines 120-135 (16 lines)

Summary:
  Unused imports deleted: 3
  Dead functions deleted: 2 (17 lines)
  Commented code deleted: 16 lines
  Blank lines cleaned: 5
  Total lines deleted: 38

File size: 487 lines → 449 lines (-8%)

Running tests to verify...
  ✓ All 47 tests passing

Tech debt re-checked:
  [Invoking: detect-unused-code skill]
  ✓ Unused imports: 0
  ✓ Dead code: 0 functions
  ✓ Commented code: 0 lines

Homeostasis achieved! Tech debt.unused_code = 0 ✓

Changes ready to commit.
```

---

## Error Handling

### If tests fail after pruning:

```
❌ ROLLBACK: Tests failed after pruning

Failed tests:
  - test_legacy_auth (expected legacy_hash_password to exist)

Analysis:
  Function 'legacy_hash_password' was detected as dead code,
  but test_legacy_auth still references it.

Root cause: Test file was not scanned by detect-unused-code.

Restoring original file...
  ✓ Restored: auth_service.py

Recommendation: Fix test_legacy_auth first (delete it or update it)
```

### If user cancels:

```
ℹ️ User cancelled pruning

Tech debt remains:
  ⚠️ 5 unused imports
  ⚠️ 2 dead functions
  ⚠️ 15 lines commented code

Homeostasis deviation persists (tech_debt = 22).

To prune later: Invoke 'prune-unused-code' skill
```

---

## Configuration

```yaml
plugins:
  - name: "@aisdlc/code-skills"
    config:
      debt_pruning:
        auto_prune: false               # Ask before pruning (default)
        run_tests_after: true           # Always verify (required)
        backup_before_prune: true       # Create backup if no git
        exclude_files:                  # Don't prune these files
          - "migrations/*"
          - "legacy/*"
```

---

## Prerequisites Check

Before invoking this skill, ensure:
1. `detect-unused-code` skill has run
2. Tech debt report is available
3. Tests are passing (GREEN)

If prerequisites not met, invoke:
- `detect-unused-code` (if no report available)
- Return error if tests not passing

---

## Next Steps

After pruning is complete:
1. Run `detect-complexity` sensor to check for complexity violations
2. If complexity violations → Invoke `simplify-complex-code` actuator
3. If clean → Invoke `commit-with-req-tag` to commit changes

---

## Rollback Procedure

If pruning causes test failures:
```
1. Restore file from backup OR git checkout
2. Report which deletion caused the failure
3. Suggest manual investigation
4. Do NOT commit
```

---

## Notes

**Why automatic deletion is safe**:
- Only deletes code with **zero references** (verified by sensor)
- Always runs tests after pruning
- Automatic rollback if tests fail
- User can review changes before commit

**Why this matters**:
- Enforces Principle #6 operationally (not just philosophically)
- Reduces codebase size → easier to understand
- Removes maintenance burden (no "is this used?" questions)
- Forces developers to trust git history (not commented code)

**Homeostasis Goal**:
```yaml
desired_state:
  tech_debt.unused_code: 0
```

**"Excellence or nothing"** 🔥
