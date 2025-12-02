# refactor-phase

**Skill Type**: Actuator (TDD Workflow)
**Purpose**: Improve code quality and enforce Principle #6 ("No Legacy Baggage") by refactoring and pruning technical debt
**Prerequisites**:
- Tests are GREEN (all passing)
- Code implements the requirement

---

## Agent Instructions

You are in the **REFACTOR** phase of TDD (RED → GREEN → REFACTOR).

Your goal is to improve code quality **and eliminate technical debt** before committing.

### Workflow

#### 1. Improve Code Quality

- Add type hints
- Improve variable names
- Extract complex expressions to named variables
- Add docstrings to public methods
- Improve error messages
- Optimize performance (only if needed)

#### 2. **Prune Technical Debt** ⭐ (Principle #6 Enforcement)

**CRITICAL**: Before committing, you **MUST** perform these checks and pruning actions:

##### 2.1 Delete Unused Imports
- Analyze the file for all import statements
- Check if each import is actually used in the code
- **DELETE** any unused imports immediately
- Example:
  ```python
  # BEFORE
  import hashlib  # ❌ Not used anywhere
  import re       # ❌ Not used anywhere
  from typing import Dict, List  # ✓ Only List is used

  # AFTER
  from typing import List  # ✓ Kept only what's used
  ```

##### 2.2 Remove Dead Code
- Scan for variables defined but never read
- Scan for functions/methods with **zero callers**
- **DELETE** all dead code immediately
- Example:
  ```python
  # BEFORE
  def legacy_hash_password(password):  # ❌ No callers
      return md5(password)

  def hash_password(password):  # ✓ Used
      return bcrypt.hash(password)

  # AFTER
  def hash_password(password):  # ✓ Kept only what's used
      return bcrypt.hash(password)
  ```

##### 2.3 Delete Commented-Out Code
- Find all commented-out code blocks
- **DELETE** all commented-out code (we have git history)
- Example:
  ```python
  # BEFORE
  def login(email, password):
      # Old implementation (broken)
      # user = User.query.get(email)
      # if user and user.password == password:
      #     return user

      # New implementation
      user = User.get_by_email(email)
      return authenticate(user, password)

  # AFTER
  def login(email, password):
      user = User.get_by_email(email)
      return authenticate(user, password)
  ```

##### 2.4 Simplify Over-Complex Logic
- Calculate cyclomatic complexity for each function
- If complexity > 10, **SIMPLIFY** by extracting functions
- Example:
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
      return success(user)

  # AFTER (Complexity: 6)
  def login(email, password):
      validation_error = validate_login_input(email, password)
      if validation_error:
          return validation_error

      user = get_user_or_fail(email)

      if user.is_locked and not user.lockout_expired():
          return error("Account locked")

      return authenticate_user(user, password)

  # Extracted functions (each < 10 lines, complexity < 5)
  def validate_login_input(email, password):
      if not email:
          return error("Email required")
      if not is_valid_email(email):
          return error("Invalid email")
      return None

  def get_user_or_fail(email):
      if not User.exists(email):
          raise UserNotFoundError(email)
      return User.get(email)

  def authenticate_user(user, password):
      if not user.check_password(password):
          handle_failed_login(user)
          return error("Invalid password")
      return success(user)

  def handle_failed_login(user):
      user.increment_attempts()
      if user.attempts >= 3:
          user.lock()
  ```

##### 2.5 Remove Duplication
- Identify duplicated code blocks (DRY principle)
- Extract to shared functions
- Example:
  ```python
  # BEFORE
  def create_user(email):
      if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
          return error("Invalid email")
      # ...

  def update_user(email):
      if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
          return error("Invalid email")
      # ...

  # AFTER
  def validate_email(email):
      pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
      return re.match(pattern, email) is not None

  def create_user(email):
      if not validate_email(email):
          return error("Invalid email")
      # ...

  def update_user(email):
      if not validate_email(email):
          return error("Invalid email")
      # ...
  ```

#### 3. Verify Tests Still Pass

After **EVERY** refactoring change:
- Run all tests
- Ensure tests are still GREEN
- If tests fail, undo the change and try a different approach

#### 4. Before Committing Checklist

You **MUST** verify:
- ✅ All tests passing (GREEN)
- ✅ No unused imports
- ✅ No dead code (0 functions with zero callers)
- ✅ No commented-out code
- ✅ Max cyclomatic complexity ≤ 10
- ✅ No duplicated code blocks
- ✅ Code follows language style guide (PEP 8 for Python, etc.)

**If ANY checklist item fails, DO NOT COMMIT. Fix it first.**

---

## Output Format

When you complete the REFACTOR phase, show:

```
[REFACTOR Phase]

Code Quality Improvements:
  ✓ Added type hints to 5 functions
  ✓ Improved variable names (3 changes)
  ✓ Added docstrings to 2 public methods

Tech Debt Pruning (Principle #6):
  ✓ Deleted 5 unused imports
  ✓ Removed 2 dead functions (17 lines deleted)
  ✓ Deleted 15 lines of commented code
  ✓ Simplified login() - complexity 18 → 6
  ✓ Extracted 4 helper functions
  ✓ Removed code duplication (2 occurrences)

File size: 487 lines → 312 lines (-36%)

Running tests...
  ✓ All 47 tests passing

Before Commit Checklist:
  ✓ All tests passing (GREEN)
  ✓ No unused imports
  ✓ No dead code
  ✓ No commented-out code
  ✓ Max complexity ≤ 10 (current max: 6)
  ✓ No duplicated code
  ✓ Code follows style guide

Ready to commit!
```

---

## Prerequisites Check

Before invoking this skill, ensure:
1. Tests are GREEN (all passing)
2. Code implements the requirement
3. No syntax errors

If prerequisites not met, invoke:
- `green-phase` (if tests not passing)
- `red-phase` (if no tests exist)

---

## Next Steps

After refactoring is complete:
1. Invoke `commit-with-req-tag` skill to create git commit
2. Move to next requirement (invoke `tdd-workflow` for next REQ-*)

---

## Notes

**Why explicit pruning?**
- LLMs have "addition bias" - naturally prefer adding code over deleting
- Without explicit enforcement, Principle #6 becomes aspirational, not operational
- This skill makes "No Legacy Baggage" **enforceable** and **measurable**

**Homeostasis Goal**:
```yaml
desired_state:
  tech_debt: 0
  max_complexity: 10
  code_duplication: 0
```

**"Excellence or nothing"** 🔥
