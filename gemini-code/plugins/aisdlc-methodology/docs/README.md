# Development Methodology

## Baseline Practices for the AI SDLC Method

This directory contains the core development methodology, forming the foundation of how we build software.

---

## Quick Start

### The Key Principles

1.  **Test Driven Development** - "No code without tests"
2.  **Fail Fast & Root Cause** - "Break loudly, fix completely"
3.  **Modular & Maintainable** - "Single responsibility, loose coupling"
4.  **Reuse Before Build** - "Check first, create second"
5.  **Open Source First** - "Suggest alternatives, human decides"
6.  **No Legacy Baggage** - "Clean slate, no debt"
7.  **Perfectionist Excellence** - "Best of breed only"

**Ultimate Mantra**: **"Excellence or nothing"** 🔥

👉 [Read Full Principles](principles/KEY_PRINCIPLES.md)

### The TDD Workflow

```
RED → GREEN → REFACTOR → COMMIT → REPEAT
```

👉 [Read TDD Workflow](processes/TDD_WORKFLOW.md)

---

## Core Documents

### [The Key Principles](principles/KEY_PRINCIPLES.md)

The seven fundamental principles that govern all development. Read these before starting any work.

### [TDD Workflow](processes/TDD_WORKFLOW.md)

A complete guide to our Test-Driven Development process. Refer to this daily during development.

---

## Quick Reference

### Before You Code

Ask yourself these seven questions:

1.  **Have I written tests first?** (Principle #1)
2.  **Will this fail loudly if something's wrong?** (Principle #2)
3.  **Does this module have a single, clear purpose?** (Principle #3)
4.  **Did I check if this already exists?** (Principle #4)
5.  **Have I researched alternatives?** (Principle #5)
6.  **Am I avoiding technical debt?** (Principle #6)
7.  **Is this the best possible implementation?** (Principle #7)

**If you can't answer "yes" to all seven, do not write the code yet.**

---

## Philosophy

### Why These Principles?

These principles are not arbitrary. They are battle-tested practices that:

1.  **Reduce bugs** by catching issues early.
2.  **Improve design** by forcing thoughtful architecture.
3.  **Enable confidence** to refactor without fear.
4.  **Accelerate development** by providing clear patterns.
5.  **Ensure quality** by building excellence in from the start.

---

## Non-Negotiables

These practices are **requirements**, not suggestions. We reject code without tests, silent error handling, monolithic classes, and technical debt. We require excellence.

**This is how we build software.**