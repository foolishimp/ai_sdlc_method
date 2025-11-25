# Changelog - principles-key

All notable changes to the `principles-key` plugin.

---

## [1.0.0] - 2025-11-20

### Added

**Principles Skills** (2/2 complete):

- `seven-questions-checklist` (246 lines) - Pre-coding quality gate
  - Ask 7 questions before any coding
  - Each question maps to one Key Principle
  - Block coding if any question answered "no"
  - Integrated with TDD/BDD workflows
  - Teaching tool for principle adoption

- `apply-key-principles` (302 lines) - Code validation sensor
  - Validate existing code against all 7 principles
  - Check TDD compliance (tests exist, coverage)
  - Check fail-fast (exceptions, error handling)
  - Check modularity (file size, complexity, SRP)
  - Check reuse (no duplication)
  - Check open source usage (library decisions)
  - Check tech debt (Principle #6)
  - Check excellence (naming, docs, types, style)
  - Report violations with fix recommendations

**Plugin Infrastructure**:
- plugin.json with principles configuration
- README.md with principles documentation
- CHANGELOG.md (this file)

### Configuration

**Principles Enforcement**:
- All 7 principles enforced by default
- Block on violation (quality gate)
- Configurable thresholds (max lines, complexity, coverage)

**Seven Questions**:
- Ask before coding
- Require all "yes" answers
- Skip for trivial changes (optional)

### Status

**Completion**: 100% (2/2 skills)
**Total Lines**: 548 lines

---

**"Excellence or nothing"** 🔥
