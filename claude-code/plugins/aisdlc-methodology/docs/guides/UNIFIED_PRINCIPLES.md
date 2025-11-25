# Unified Development Principles - No Conflicts

## 🎯 Core Hierarchy of Principles

When in doubt, follow this priority order (references Key Principles principles):

1. **Test First** (Principle #1) - TDD before implementation, no exceptions
2. **Fail Fast** (Principle #2) - Root cause over workarounds
3. **Reuse Before Build** (Principle #4) - Check existing code first
4. **Open Source First** (Principle #5) - AI suggests, human decides
5. **Quality Excellence** (Principle #7) - Perfectionist standard
6. **No Tech Debt** (Principle #6) - Clean slate, no legacy baggage
7. **Modular Design** (Principle #3) - Decoupled, maintainable code

---

## ✅ Resolved Principle Clarifications

### 1. Quality vs Pace
**Principle:** We are perfectionist developers who work at a sustainable pace
- ✅ High quality code with >80% test coverage
- ✅ Take breaks every 45-60 minutes
- ✅ No rushing - better to do it right
- ✅ Celebrate progress to maintain morale

### 2. Decision Making
**Principle:** AI suggests, human decides
- ✅ AI SUGGESTS open source alternatives
- ✅ AI PROPOSES architectural approaches
- ✅ Human MAKES final decisions
- ✅ Human APPROVES before major changes

### 3. Documentation Timing
**Principle:** Document continuously, formalize at completion
- ✅ During: Document decisions in comments/chat
- ✅ During: Update TodoWrite for progress tracking
- ✅ After: Create formal finished task file
- ✅ After: Update active tasks

### 4. Testing Philosophy
**Principle:** Fail fast to find problems, then fix properly
- ✅ RED: Write tests that fail (expose problems)
- ✅ GREEN: Minimal code to pass (quick validation)
- ✅ REFACTOR: Improve to production quality
- ✅ No workarounds - fix root causes

### 5. Code Changes
**Principle:** Small, safe, reversible changes
- ✅ Feature flags for new features (where appropriate)
- ✅ Keep old code until new is proven
- ✅ Small incremental commits
- ✅ One task = one commit

### 6. Communication
**Principle:** Over-communicate rather than assume
- ✅ AI explains BEFORE implementing
- ✅ Human provides feedback DURING work
- ✅ Both check in every 10-15 minutes
- ✅ Ask when uncertain

### 7. Architecture
**Principle:** Design for clarity, not cleverness
- ✅ Clear over clever
- ✅ Show errors clearly, don't degrade silently
- ✅ Explicit over implicit
- ✅ Simple over complex

### 8. Refactoring
**Principle:** Refactor with purpose, not perfectionism
- ✅ Only refactor with clear goal
- ✅ Keep working code working
- ✅ Test before and after
- ✅ Document why refactoring was needed

---

## 🚫 Anti-Principles (What We DON'T Do)

1. **NO Quick Fixes** - Even if faster
2. **NO Assumptions** - Ask if unsure
3. **NO Big Bang Changes** - Incremental only
4. **NO Silent Failures** - Fail loudly
5. **NO Tech Debt** - Fix it right first time
6. **NO Backwards Compatibility** - This is new development
7. **NO Implementation Before Tests** - TDD always

---

## 🎓 When Principles Seem to Conflict

Use this decision tree:

```
Is it a safety issue?
├── YES → Safety first (don't break working code)
└── NO → Continue
    │
    Is it a quality issue?
    ├── YES → Quality over speed
    └── NO → Continue
        │
        Is it an architectural decision?
        ├── YES → Human decides
        └── NO → Continue
            │
            Is it about approach?
            ├── YES → Follow TDD process
            └── NO → Ask for clarification
```

---

## 📋 Quick Reference Card

### Every Task
1. Write tests first (RED)
2. Minimal implementation (GREEN)
3. Refactor for quality (REFACTOR)
4. Document everything
5. Commit with details

### Every Session
1. Review methodologies
2. Check active tasks
3. Align on goals
4. Work in small increments
5. Commit completed work

### Every Decision
1. Is it tested?
2. Is it documented?
3. Is it approved?
4. Is it reversible?
5. Is it the right fix?

---

## 🤝 The Agreement

**AI and Human agree:**
- Quality is non-negotiable
- Tests come first
- Communication is continuous
- Documentation is mandatory
- We're building something great together

No conflicts, only clarity!

---

## 🔍 Principle Application Examples

### Example 1: Adding a New Feature
```
✅ Correct Flow:
1. Human: "We need user authentication"
2. AI: "I'll start with tests for login/logout. Should we use JWT?"
3. Human: "Yes, JWT is fine"
4. AI: "Writing failing test for login..."
5. [RED → GREEN → REFACTOR cycle]
6. AI: "Feature complete, all tests passing, ready for review"
7. Human: "Approved, commit it"

❌ Wrong Flow:
1. Human: "We need user authentication"
2. AI: [Implements entire auth system without tests]
3. AI: "Done! Here's 1000 lines of code"
4. [No tests, no review, no communication]
```

### Example 2: Fixing a Bug
```
✅ Correct Flow:
1. AI: "Found a bug in the payment processor"
2. AI: "Writing test to reproduce the bug..." [RED]
3. AI: "Test failing as expected, investigating root cause..."
4. AI: "Root cause: null check missing. Fixing..." [GREEN]
5. AI: "Refactoring for clarity..." [REFACTOR]
6. AI: "All tests passing, bug fixed properly"

❌ Wrong Flow:
1. AI: "Found a bug, adding try-catch to hide it"
2. [Workaround that doesn't fix root cause]
```

---

## 💡 Remember

These principles work together, not against each other. When you understand the "why" behind each principle, conflicts disappear and development flows smoothly.

**Ultimate Mantra: "Excellence or nothing"**
