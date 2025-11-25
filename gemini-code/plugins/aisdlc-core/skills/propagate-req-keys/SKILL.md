---
name: propagate-req-keys
description: Homeostatic actuator that tags code, tests, and commits with REQ-* keys for traceability. Adds "# Implements:" tags to code and "# Validates:" tags to tests. Use when code or tests are missing requirement tags.
allowed-tools: [Read, Write, Edit, Grep, Glob]
---

# propagate-req-keys

**Skill Type**: Actuator (Homeostasis)
**Purpose**: Tag code and tests with REQ-* keys for traceability
**Prerequisites**: REQ-* key exists and is validated

---

## Agent Instructions

You are an **Actuator** in the AI SDLC's homeostasis system. Your purpose is to **correct deviations** from the desired state by ensuring all artifacts are properly tagged for traceability.

**Desired State**: `all_artifacts_tagged = true` (all code and tests have corresponding REQ-* tags)

Your goal is to **add the appropriate REQ-* tags** to source code, test files, and other artifacts to establish and maintain bidirectional traceability.

---

## Workflow

### Step 1: Identify Tagging Targets

**Input**: A REQ-* key and the target files.

**Determine the correct tag based on the file type**:
-   **Implementation files** (`src/`): Add `# Implements: {REQ-KEY}`
-   **Test files** (`tests/`): Add `# Validates: {REQ-KEY}`
-   **BDD Feature files** (`features/`): Add `# Validates: {REQ-KEY}`
-   **Commit messages**: Include the REQ-* key in the subject or footer.

### Step 2: Tag Implementation and Test Files

Add the appropriate tag to the top of the file or directly above the relevant function, class, or test.

**Python Implementation Example**:
```python
# Before
def login(email: str, password: str):
    # ...

# After
# Implements: <REQ-ID>
def login(email: str, password: str):
    # ...
```

**Python Test Example**:
```python
# Before
def test_user_can_login():
    # ...

# After
# Validates: <REQ-ID>
def test_user_can_login():
    # ...
```

### Step 3: Tag Commit Messages

Include the REQ-* key in your commit messages to link code changes directly to requirements.

**Example Commit Message**:
```
feat: Add user login functionality (<REQ-ID>)

This commit implements the core login endpoint and validation logic.

Implements: <REQ-ID>
Validates: BR-001, BR-002
```

### Step 4: Verify Tag Propagation

After tagging, verify that the tags have been correctly applied.

```bash
# Verify implementation tags for a specific requirement
grep -rn "# Implements: <REQ-ID>" src/

# Verify test tags for a specific requirement
grep -rn "# Validates: <REQ-ID>" tests/
```

## Output Format

When you complete a tagging operation, provide a summary of the actions taken:

```
[PROPAGATE REQ-KEYS - <REQ-ID>]

Files Tagged:

Implementation Files (1):
  ✓ src/auth/login.py
    Added: # Implements: <REQ-ID>

Test Files (2):
  ✓ tests/auth/test_login.py
    Added: # Validates: <REQ-ID>
  ✓ features/authentication.feature
    Added: # Validates: <REQ-ID>

Total Tags Added: 3

Traceability Status:
  Forward: <REQ-ID> → 1 code file, 2 test files ✅
  Backward: Code/tests → <REQ-ID> ✅

✅ Propagation Complete!
```

---

## Homeostasis Behavior

This actuator is typically triggered when the `check-requirement-coverage` sensor detects a deviation.

1.  **Sensor detects**: A requirement is missing implementation or test tags.
2.  **Actuator is invoked**: You are called upon to add the missing tags.
3.  **Actuator runs**: You add the necessary tags to the appropriate files.
4.  **Sensor re-checks**: The `check-requirement-coverage` skill is run again to confirm that homeostasis has been restored.