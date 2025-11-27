# TCS-003: /aisdlc-commit-task Command

**Status**: ✅ Implemented
**Date**: 2025-11-27
**Requirements**: REQ-F-CMD-001, REQ-NFR-TRACE-001
**ADR Reference**: [ADR-002](../adrs/ADR-002-commands-for-workflow-integration.md)
**Implementation**: `claude-code/plugins/aisdlc-methodology/commands/aisdlc-commit-task.md`

---

## Purpose

Validate that the `/aisdlc-commit-task` command creates properly formatted git commits with requirement traceability tags from finished task documents.

---

## Preconditions

- Finished task document exists for the task ID
- Git repository initialized
- Changes staged or unstaged
- User can approve/reject commit

---

## Test Scenarios

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| CM-001 | Valid task ID | Finished doc exists | Commit created with formatted message | High |
| CM-002 | With REQ tags | Task has requirement keys | Commit includes "Implements: REQ-*" | High |
| CM-003 | No finished doc | Task ID not found | Error: "Finished task document not found" | High |
| CM-004 | No changes | Nothing to commit | Warning: "Nothing to commit" | Medium |
| CM-005 | User rejects | User says no to commit | No commit made, graceful exit | Medium |
| CM-006 | Multi-task commit | Multiple tasks finished | Each task committed separately | Low |

---

## Validation Criteria

- [ ] Commit message shown to user before committing
- [ ] User approval required before git commit
- [ ] Commit message includes task ID and title
- [ ] REQ keys from task included in "Implements:" line
- [ ] "TDD: RED → GREEN → REFACTOR" line present
- [ ] Co-Author tag for Claude included
- [ ] Commit hash returned on success
- [ ] No commit on user rejection

---

## Expected Commit Message Format

```
Task #{id}: {title}

{Brief summary of problem}

{Brief summary of solution}

Tests: {test_summary}
TDD: RED → GREEN → REFACTOR

Implements: {REQ keys from task}

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Test Implementation

**File**: `claude-code/tests/commands/test_commands.py`
**Class**: `TestCommitTaskCommand`
**Tests**: 2

```python
class TestCommitTaskCommand:
    def test_commit_message_format(self):
        """CM-001: Commit message follows format."""

    def test_commit_requires_finished_doc(self, workspace_with_tasks):
        """CM-003: Commit requires finished document."""
```

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-F-CMD-001 | Command exists and executes |
| REQ-NFR-TRACE-001 | REQ-* tags included in commit message |

---

## Notes

- Always show commit message before executing
- Include all REQ keys from the finished task document
- Keep commit message concise but informative
- Commit is atomic - no partial commits on error
