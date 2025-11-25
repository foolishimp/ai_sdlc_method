# Changelog - code-skills

All notable changes to the `code-skills` plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-11-20

### Added

**Tech Debt Management Skills** (4/4 complete):
- `detect-unused-code` - Sensor skill detecting unused imports, dead code, commented code
- `prune-unused-code` - Actuator skill auto-deleting unused code
- `detect-complexity` - Sensor skill detecting over-complex logic (cyclomatic complexity > 10)
- `simplify-complex-code` - Actuator skill simplifying complex logic by extracting functions

**TDD Skills** (1/5 complete):
- `refactor-phase` - Comprehensive refactor phase with Principle #6 enforcement
  - Improves code quality (type hints, docstrings, naming)
  - Deletes unused imports
  - Removes dead code
  - Deletes commented code
  - Simplifies over-complex logic
  - Removes code duplication
  - Before-commit checklist validation

**Plugin Infrastructure**:
- `.claude-plugin/plugin.json` - Plugin manifest with metadata, capabilities, configuration
- `README.md` - Comprehensive documentation with examples
- `CHANGELOG.md` - Version history (this file)

**Configuration Options**:
- TDD configuration (minimum_coverage, enforce_red_green_refactor)
- Tech debt configuration (auto_detect_on_refactor, max_complexity, exclude_patterns)
- BDD configuration (gherkin_style, require_scenarios_for_requirements)
- Code generation configuration (auto_generate_from_br, require_tests_for_generated_code)

### Status

**Completion**: 23% (5/18 skills)

**Skills Complete**:
- ✅ Tech Debt Management (4/4 skills)
- ✅ TDD refactor-phase (1/5 skills)

**Skills Pending**:
- ⏳ TDD Workflow (4 remaining: tdd-workflow, red-phase, green-phase, commit-with-req-tag)
- ⏳ BDD Workflow (5 skills: bdd-workflow, write-scenario, implement-step-definitions, implement-feature, refactor-bdd)
- ⏳ Code Generation (4 skills: autogenerate-from-business-rules, autogenerate-validators, autogenerate-constraints, autogenerate-formulas)

---

## [Unreleased]

### To Add (v1.1.0)

**TDD Skills**:
- `tdd-workflow` - Orchestrator skill coordinating RED → GREEN → REFACTOR → COMMIT
- `red-phase` - Write failing tests with templates for Python/TypeScript/Java
- `green-phase` - Implement minimal code to pass tests
- `commit-with-req-tag` - Git commits tagged with REQ-* keys

**BDD Skills**:
- `bdd-workflow` - Orchestrator skill coordinating Given/When/Then workflow
- `write-scenario` - Create Gherkin scenarios from requirements
- `implement-step-definitions` - Implement step definitions for scenarios
- `implement-feature` - Implement feature code for scenarios
- `refactor-bdd` - Refactor BDD implementation

**Code Generation Skills**:
- `autogenerate-from-business-rules` - Generate code from BR-* business rules
- `autogenerate-validators` - Generate validation code from BR-*
- `autogenerate-constraints` - Generate constraint checks from C-*
- `autogenerate-formulas` - Generate formula implementations from F-*

**Templates**:
- Test templates for Python, TypeScript, Java
- Gherkin scenario templates

### To Add (v1.2.0)

**REPL-Driven Workflow** (for data science):
- `repl-workflow` - Interactive development workflow
- `notebook-to-module` - Extract Jupyter notebooks to Python modules

**Property-Based Testing**:
- `property-based-testing` - Generate property-based tests

**Mutation Testing**:
- `mutation-testing` - Test the tests with mutation testing

---

## Version History Summary

| Version | Date | Skills | Completion | Status |
|---------|------|--------|------------|--------|
| 1.0.0 | 2025-11-20 | 5/18 | 23% | Initial release (tech debt + refactor) |
| 1.1.0 | TBD | 18/18 | 100% | Complete TDD, BDD, generation skills |
| 1.2.0 | TBD | TBD | TBD | REPL, property-based, mutation testing |

---

**"Excellence or nothing"** 🔥
