# principles-key Plugin

**Enforce the 7 Key Principles During Development**

Version: 1.0.0

---

## Overview

The `principles-key` plugin enforces the **7 Key Principles** as operational quality gates during development. Includes the Seven Questions Checklist (sensor) and principles validation (sensor).

**The 7 Key Principles**:
1. **Test Driven Development** - "No code without tests"
2. **Fail Fast & Root Cause** - "Break loudly, fix completely"
3. **Modular & Maintainable** - "Single responsibility, loose coupling"
4. **Reuse Before Build** - "Check first, create second"
5. **Open Source First** - "Suggest alternatives, human decides"
6. **No Legacy Baggage** - "Clean slate, no debt"
7. **Perfectionist Excellence** - "Best of breed only"

**Ultimate Mantra**: **"Excellence or nothing"** 🔥

---

## Capabilities

### 1. Seven Questions Checklist (Quality Gate)

**Skill**: `seven-questions-checklist`

**Purpose**: Pre-coding quality gate enforcing all 7 principles

**The 7 Questions**:
1. Have I written tests first? (Principle #1)
2. Will this fail loudly if wrong? (Principle #2)
3. Is this module focused? (Principle #3)
4. Did I check if this exists? (Principle #4)
5. Have I researched alternatives? (Principle #5)
6. Am I avoiding tech debt? (Principle #6)
7. Is this excellent? (Principle #7)

**ALL must be "yes"** before coding proceeds.

**Usage**:
```
Before coding → Run checklist → Answer 7 questions
  → If all "yes" → Proceed
  → If any "no" → Fix issue first, then retry
```

---

### 2. Principles Validation

**Skill**: `apply-key-principles`

**Purpose**: Validate existing code against all 7 principles

**Checks**:
- #1: Tests exist, coverage >= 80%
- #2: Exceptions raised, specific errors, logging present
- #3: Small files/functions, low complexity, single responsibility
- #4: No duplicate code
- #5: Open source libraries used (documented in ADRs)
- #6: Zero tech debt (no unused code, complexity <= 10)
- #7: Clear naming, docs, type hints, style compliance

**Usage**:
```
Validate code → Run principle checks → Report violations
  → If violations → Suggest fixes
  → If all pass → Approve ✅
```

---

## Installation

```bash
/plugin marketplace add foolishimp/ai_sdlc_method
/plugin install @aisdlc/principles-key
```

---

## Usage Examples

### Example 1: Seven Questions Before Coding

```
You: "Implement user authentication"

Claude: (invokes seven-questions-checklist automatically)

Before we code, let's run the Seven Questions:

1. Tests first? → Using TDD ✅
2. Fail loud? → Will add assertions ✅
3. Module focused? → Separate auth module ✅
4. Checked if exists? → Searching...
   Found: Existing auth in src/auth/ ⚠️
   → Should we reuse or replace?

You: "Improve existing"

Claude: ✅ Reusing existing (Principle #4)

5. Researched alternatives? → Use Passport.js?
You: "No, keep custom"
Claude: ✅

6. Avoiding tech debt? → Yes ✅
7. Is this excellent? → Yes ✅

7/7 Questions "Yes" ✅
Proceeding with implementation...
```

---

### Example 2: Validate Existing Code

```
You: "Check if src/auth.py follows Key Principles"

Claude: (invokes apply-key-principles)

Validating src/auth.py against 7 Key Principles...

✅ #1 TDD: tests/test_auth.py exists, 95% coverage
✅ #2 Fail Fast: Exceptions raised, specific errors
✅ #3 Modular: 142 lines, complexity 6, focused
✅ #4 Reuse: No duplicates found
✅ #5 Open Source: Using bcrypt (standard library)
❌ #6 No Debt: 3 violations:
   - Unused import: hashlib (line 5)
   - Dead function: legacy_validate() (lines 89-97)
   - Commented code: lines 120-135
✅ #7 Excellence: Clear naming, docs, type hints

Result: 6/7 Principles ⚠️

Violations: 3 (all Principle #6)
Recommendation: Invoke 'prune-unused-code' to fix
```

---

## Integration with Code Workflows

**TDD Workflow Integration**:
```
TDD workflow automatically:
  1. Runs seven-questions-checklist before RED phase
  2. Validates Principle #1 (tests first)
  3. Enforces Principle #6 during REFACTOR phase (tech debt elimination)
  4. Validates Principle #7 before commit (excellence check)
```

**REFACTOR Phase Integration**:
```
REFACTOR phase automatically:
  - Enforces Principle #6 (prune tech debt)
  - Validates Principle #7 (code quality)
  - Before commit: apply-key-principles validation
```

---

## Configuration

```yaml
plugins:
  - name: "@aisdlc/principles-key"
    config:
      principles:
        enforce_all: true
        block_on_violation: true

      seven_questions:
        ask_before_coding: true
        require_all_yes: true

      validation:
        max_file_lines: 300
        max_function_lines: 50
        max_complexity: 10
        min_coverage: 80
```

---

## Dependencies

- **Required**: `@aisdlc/aisdlc-core` (^3.0.0)

**Works With**:
- `@aisdlc/code-skills` - TDD/BDD enforce Principle #1
- `@aisdlc/testing-skills` - Coverage validation (Principle #1)

---

## Skills Status

| Skill | Status | Type | Lines |
|-------|--------|------|-------|
| seven-questions-checklist | ✅ | Sensor/Gate | 246 |
| apply-key-principles | ✅ | Validator | 302 |
| **TOTAL** | **✅ 100%** | **-** | **548** |

---

**"Excellence or nothing"** 🔥
