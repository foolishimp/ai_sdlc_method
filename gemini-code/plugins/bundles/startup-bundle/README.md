# Startup Bundle

**Quick-start AI SDLC for startups and solo developers**

Version: 1.0.0

---

## What's Included

- ✅ **aisdlc-core** - Requirement traceability foundation
- ✅ **code-skills** - TDD/BDD workflows, code generation, tech debt management
- ✅ **principles-key** - Seven Questions quality gate, Key Principles enforcement

**Total**: 23 skills across 3 plugins

---

## Why This Bundle?

**For**: Startups, solo developers, MVPs, prototypes
**Goal**: Ship fast without sacrificing quality
**Philosophy**: Minimal overhead, maximum quality

**You get**:
- ✅ TDD workflow enforcement (no code without tests)
- ✅ Requirement traceability (REQ-* keys)
- ✅ Tech debt elimination (Principle #6)
- ✅ Quality gates (Seven Questions)
- ✅ Code generation from business rules

**You skip**:
- Formal requirements extraction (just use REQ-* keys directly)
- Design stage (optional for MVPs)
- Integration testing (unit tests sufficient for start)
- Runtime feedback (add later when deployed)

---

## Installation

```bash
/plugin marketplace add foolishimp/ai_sdlc_method
/plugin install startup-bundle
```

This automatically installs: aisdlc-core, code-skills, principles-key

---

## Quick Start

```
You: "Implement user login"

Claude: Before we code, Seven Questions:
  1. Tests first? → Using TDD ✅
  2-7. ... all yes ✅

  Starting TDD for <REQ-ID>...

[RED] Tests created ✓
[GREEN] Code implemented ✓
[REFACTOR] Tech debt eliminated ✓
[COMMIT] Tagged with <REQ-ID> ✓

Done! 100% coverage, zero tech debt 🔥
```

---

**"Excellence or nothing"** 🔥
