# TCS-004: /aisdlc-finish-task Command

**Status**: ✅ Implemented
**Date**: 2025-11-27
**Requirements**: REQ-F-CMD-001, REQ-F-WORKSPACE-002
**ADR Reference**: [ADR-002](../adrs/ADR-002-commands-for-workflow-integration.md)
**Implementation**: `claude-code/plugins/aisdlc-methodology/commands/aisdlc-finish-task.md`

---

## Purpose

Validate that the `/aisdlc-finish-task` command correctly completes a task by creating a comprehensive finished task document and removing the task from active tasks.

---

## Preconditions

- Task exists in `ACTIVE_TASKS.md`
- Work is complete (tests passing, acceptance criteria met)
- `FINISHED_TASK_TEMPLATE.md` exists in templates/

---

## Test Scenarios

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| FT-001 | Valid completion | Task fully complete | Finished doc created, task removed from active | High |
| FT-002 | Task not found | Invalid task ID | Error: "Task #{id} not found" | High |
| FT-003 | Incomplete task | Tests failing | Warning: "Task may not be complete" | Medium |
| FT-004 | All fields filled | Complete task information | All template sections populated | High |
| FT-005 | Missing info | Partial task information | Sections marked as "Not documented" | Low |

---

## Validation Criteria

- [ ] Finished document created at correct path
- [ ] Filename format: `{YYYYMMDD_HHMM}_{task_slug}.md`
- [ ] All template sections present in finished document
- [ ] Task removed from ACTIVE_TASKS.md
- [ ] Confirmation message with file path shown
- [ ] Template sections filled from conversation context

---

## Required Template Sections

1. **Problem** - What was the issue?
2. **Investigation** - What was discovered?
3. **Solution** - How was it solved?
4. **TDD Process** - RED/GREEN/REFACTOR phases
5. **Files Modified** - List of changed files
6. **Test Coverage** - Before/after metrics
7. **Result** - Outcome and metrics
8. **Side Effects** - Positive and considerations
9. **Future Considerations** - Follow-up tasks
10. **Lessons Learned** - What was learned
11. **Traceability** - Requirements coverage
12. **Metrics** - Lines, tests, coverage

---

## Test Implementation

**File**: `claude-code/tests/commands/test_commands.py`
**Class**: `TestFinishTaskCommand`
**Tests**: 1

```python
class TestFinishTaskCommand:
    def test_finish_task_creates_document(self, workspace_with_tasks):
        """FT-001: Finish task creates document."""
```

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-F-CMD-001 | Command exists and executes |
| REQ-F-WORKSPACE-002 | Task management templates used correctly |

---

## Notes

- Finished task document is valuable documentation - fill thoroughly
- Document should capture the full story of the task
- REQ keys from task should flow to finished document
