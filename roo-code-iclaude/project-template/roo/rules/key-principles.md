# Key Principles

The 7 foundational principles for the Code stage (Stage 4) of the AI SDLC methodology.

## The 7 Principles

### 1. Test Driven Development
**"No code without tests"**

- Write failing test FIRST (RED)
- Write minimal code to pass (GREEN)
- Improve code quality (REFACTOR)
- Commit with clear message (COMMIT)
- Repeat for every feature

**Never skip TDD. Ever.**

### 2. Fail Fast & Root Cause
**"Break loudly, fix completely"**

- Errors should be visible immediately
- No silent failures or swallowed exceptions
- Fix the root cause, not symptoms
- Add regression tests for every bug fix
- Prefer explicit errors over undefined behavior

### 3. Modular & Maintainable
**"Single responsibility, loose coupling"**

- Each module does one thing well
- Dependencies are explicit and minimal
- Code is readable without comments
- Functions are small and focused
- Avoid deep nesting and complex conditionals

### 4. Reuse Before Build
**"Check first, create second"**

- Search codebase before writing new code
- Check for existing libraries/patterns
- Don't reinvent the wheel
- Consolidate duplicate code when found
- Document why new code is necessary

### 5. Open Source First
**"Suggest alternatives, human decides"**

- Prefer battle-tested libraries
- Research before recommending
- Present options with trade-offs
- Let human make final decision
- Document chosen approach and rationale

### 6. No Legacy Baggage
**"Clean slate, no debt"**

- Don't carry forward bad patterns
- Refactor technical debt when encountered
- Don't add backwards-compatibility hacks
- Remove dead code immediately
- Each commit leaves codebase better

### 7. Perfectionist Excellence
**"Best of breed only"**

- Good enough is not good enough
- Quality over speed
- Excellence in every detail
- Pride in craftsmanship
- Continuous improvement

## Ultimate Mantra

**"Excellence or nothing"**

## Before You Code

Ask these seven questions:

1. Have I written tests first? (Principle #1)
2. Will this fail loudly if wrong? (Principle #2)
3. Is this module focused? (Principle #3)
4. Did I check if this exists? (Principle #4)
5. Have I researched alternatives? (Principle #5)
6. Am I avoiding tech debt? (Principle #6)
7. Is this excellent? (Principle #7)

**If not "yes" to all seven, don't code yet.**

## Application

These principles apply to ALL code written during the Code stage:
- Production code
- Test code
- Configuration
- Documentation
- Scripts and tools

No exceptions. No shortcuts.
