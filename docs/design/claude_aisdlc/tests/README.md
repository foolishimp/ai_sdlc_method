# AISDLC Test Case Registry

**Version**: 1.0.0
**Date**: 2025-11-27
**Status**: Active

---

## Overview

This directory contains **Test Case Specifications (TCS)** for validating AISDLC implementation. Test cases follow the same traceability pattern as ADRs - each traces to requirements and implementation.

```
Requirements (REQ-*)
    ↓
Design (ADRs)
    ↓
Implementation (Commands, Hooks, Installers)
    ↓
Test Cases (TCS-*) ← This directory
```

---

## Test Case Index

| ID | Title | Requirements | Status |
|----|-------|--------------|--------|
| [TCS-001](TCS-001-command-status.md) | /aisdlc-status Command | REQ-F-CMD-001, REQ-F-TODO-003 | ✅ Implemented |
| [TCS-002](TCS-002-command-checkpoint.md) | /aisdlc-checkpoint-tasks Command | REQ-F-WORKSPACE-002, REQ-NFR-CONTEXT-001 | ✅ Implemented |
| [TCS-003](TCS-003-command-commit.md) | /aisdlc-commit-task Command | REQ-F-CMD-001, REQ-NFR-TRACE-001 | ✅ Implemented |
| [TCS-004](TCS-004-command-finish.md) | /aisdlc-finish-task Command | REQ-F-CMD-001, REQ-F-WORKSPACE-002 | ✅ Implemented |
| [TCS-005](TCS-005-command-refresh.md) | /aisdlc-refresh-context Command | REQ-F-CMD-001, REQ-NFR-CONTEXT-001 | ✅ Implemented |
| [TCS-006](TCS-006-command-release.md) | /aisdlc-release Command | REQ-F-CMD-003 | ✅ Implemented |
| [TCS-007](TCS-007-command-update.md) | /aisdlc-update Command | REQ-F-UPDATE-001 | ✅ Implemented |
| [TCS-008](TCS-008-hooks-lifecycle.md) | Lifecycle Hooks | REQ-F-HOOKS-001, REQ-NFR-CONTEXT-001 | 📋 Specified |
| [TCS-009](TCS-009-installer-setup.md) | aisdlc-setup.py Installer | REQ-F-WORKSPACE-001, REQ-F-PLUGIN-001 | 📋 Specified |
| [TCS-010](TCS-010-skill-tcs.md) | TCS Creation Skill | REQ-NFR-TRACE-001, REQ-NFR-QUALITY-001 | ✅ Implemented |

---

## Test Case Summary

**Total Test Cases**: 10
**Status**: 8 Implemented ✅, 2 Specified 📋
**Coverage**: All 7 commands + hooks + installer + TCS skill

### Coverage by Component

| Component | Test Cases | Status |
|-----------|-----------|--------|
| Commands (7) | TCS-001 to TCS-007 | ✅ All implemented |
| Hooks (4) | TCS-008 | 📋 Specified |
| Installer | TCS-009 | 📋 Specified |
| Skills | TCS-010 | ✅ Implemented |

---

## Traceability Matrix

### Requirements → Test Cases

| Requirement | Test Cases | Coverage |
|-------------|-----------|----------|
| REQ-F-CMD-001 | TCS-001, TCS-002, TCS-003, TCS-004, TCS-005 | ✅ Full |
| REQ-F-CMD-003 | TCS-006 | ✅ Full |
| REQ-F-WORKSPACE-001 | TCS-009 | 📋 Specified |
| REQ-F-WORKSPACE-002 | TCS-002, TCS-004 | ✅ Full |
| REQ-F-TODO-003 | TCS-001 | ✅ Full |
| REQ-F-UPDATE-001 | TCS-007 | ✅ Full |
| REQ-F-HOOKS-001 | TCS-008 | 📋 Specified |
| REQ-F-PLUGIN-001 | TCS-009 | 📋 Specified |
| REQ-NFR-CONTEXT-001 | TCS-002, TCS-005, TCS-008 | ✅ Partial |
| REQ-NFR-TRACE-001 | TCS-003, TCS-010 | ✅ Full |
| REQ-NFR-QUALITY-001 | TCS-010 | ✅ Implemented |

### ADRs → Test Cases

| ADR | Validates | Test Cases |
|-----|-----------|-----------|
| ADR-001 | Claude Code Platform | All (platform dependency) |
| ADR-002 | Commands | TCS-001 to TCS-007 |
| ADR-007 | Hooks | TCS-008 |
| ADR-006 | Plugin Discovery | TCS-009 |

---

## Test Execution

### Run All Command Tests
```bash
pytest claude-code/tests/commands/test_commands.py -v
```

### Run Specific Test Case
```bash
# TCS-001: Status command
pytest claude-code/tests/commands/test_commands.py -k "TestStatusCommand" -v

# TCS-006: Release command
pytest claude-code/tests/commands/test_commands.py -k "TestReleaseCommand" -v
```

### Run Integration Tests
```bash
pytest claude-code/tests/commands/test_commands.py -k "TestIntegration" -v
```

---

## Test Case Template

Each TCS document follows this structure:

```markdown
# TCS-XXX: {Title}

**Status**: Implemented | Specified | Deprecated
**Date**: YYYY-MM-DD
**Requirements**: REQ-F-*, REQ-NFR-*
**ADR Reference**: ADR-XXX
**Implementation**: Path to implementation file

---

## Purpose
What this test case validates.

## Preconditions
Required state before test execution.

## Test Scenarios

| ID | Scenario | Input | Expected Output |
|----|----------|-------|-----------------|
| XXX-001 | ... | ... | ... |

## Validation Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Test Implementation
Link to actual test code.
```

---

## Adding New Test Cases

1. Create `TCS-XXX-{slug}.md` in this directory
2. Add entry to Test Case Index above
3. Update Traceability Matrix
4. Implement tests in `claude-code/tests/`
5. Update status when implemented

---

**Last Updated**: 2025-11-27
**Next Review**: After each command/hook addition
