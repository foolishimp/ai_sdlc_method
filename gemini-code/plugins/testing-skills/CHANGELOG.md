# Changelog - testing-skills

All notable changes to the `testing-skills` plugin.

---

## [1.0.0] - 2025-11-20

### Added

**Testing Skills** (4/4 complete):

- `validate-test-coverage` (291 lines) - Homeostatic sensor
  - Calculate overall coverage percentage
  - Coverage per requirement (REQ-*)
  - Critical path coverage validation
  - Detect requirements without tests
  - Signal deviations if < threshold

- `generate-missing-tests` (363 lines) - Homeostatic actuator
  - Auto-generate tests for coverage gaps
  - Happy path, edge cases, error cases, boundary tests
  - Test generation from BR-* business rules
  - Test generation from uncovered code lines
  - Verify generated tests pass

- `run-integration-tests` (270 lines) - Test runner
  - Run BDD scenarios (Given/When/Then)
  - Run API integration tests
  - Run database integration tests
  - Run end-to-end tests
  - Aggregate results and map to requirements

- `create-coverage-report` (254 lines) - Reporter
  - Comprehensive coverage report with REQ-* mapping
  - Multiple formats (console, HTML, JSON, markdown)
  - Coverage gaps and recommendations
  - Coverage trends over time
  - Test statistics (unit, integration, E2E)

**Plugin Infrastructure**:
- plugin.json with homeostasis capabilities
- README.md with usage examples
- CHANGELOG.md (this file)

### Configuration

**Coverage Validation**:
- Minimum coverage: 80%
- Critical paths: 100%
- Per-requirement validation

**Test Generation**:
- Auto-generate on gap (configurable)
- Edge cases, error cases, boundary tests
- Framework support (pytest, jest, junit)

**Integration Testing**:
- Auto-run on commit (configurable)
- Parallel execution
- Timeout: 300 seconds

**Reporting**:
- HTML format with REQ-* navigation
- Gap analysis and recommendations
- Historical trends

### Status

**Completion**: 100% (4/4 skills)
**Total Lines**: 1,178 lines

---

**"Excellence or nothing"** 🔥
