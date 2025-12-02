# TCS-001: /aisdlc-status Command

**Status**: ✅ Implemented
**Date**: 2025-11-27
**Requirements**: REQ-F-CMD-001, REQ-F-TODO-003
**ADR Reference**: [ADR-002](../adrs/ADR-002-commands-for-workflow-integration.md)
**Implementation**: `claude-code/plugins/aisdlc-methodology/commands/aisdlc-status.md`

---

## Purpose

Validate that the `/aisdlc-status` command correctly displays the current task queue status, providing users with a quick snapshot of active tasks, finished tasks, and TODOs.

---

## Preconditions

- `.ai-workspace/` directory exists
- `ACTIVE_TASKS.md` file exists (may be empty)
- User has Claude Code with AISDLC plugins installed

---

## Test Scenarios

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| ST-001 | Empty workspace | No tasks in ACTIVE_TASKS.md | Shows "0 Active Tasks", "(No tasks in progress)" | High |
| ST-002 | Single active task | 1 task in ACTIVE_TASKS.md | Shows "1 Active Task", lists task title | High |
| ST-003 | Multiple active tasks | 3 tasks in ACTIVE_TASKS.md | Shows "3 Active Tasks", lists all titles | High |
| ST-004 | With finished tasks | 2 finished task files in finished/ | Shows "2 Recently Finished", lists names | Medium |
| ST-005 | No workspace | Missing .ai-workspace/ | Error message with setup instructions | High |
| ST-006 | Malformed ACTIVE_TASKS.md | Invalid markdown structure | Graceful handling, shows what's parseable | Low |

---

## Validation Criteria

- [ ] Output contains "AI SDLC Task Status" header box
- [ ] Active task count matches actual `## Task #` headers in file
- [ ] Task titles are correctly extracted from headers
- [ ] Recently finished tasks listed (maximum 5, most recent first)
- [ ] Suggestion provided based on current state
- [ ] Command is read-only (no file modifications)

---

## Expected Output Format

```
╔══════════════════════════════════════════════════════════════╗
║                    AI SDLC Task Status                       ║
╚══════════════════════════════════════════════════════════════╝

📋 Active Tasks: {count}
   {list task titles or "(No tasks in progress)"}

✅ Recently Finished: {count}
   {list last 5 finished tasks or "(No finished tasks yet)"}

📝 TODO List: {count} items
   {list todos or "(Empty)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Next: {suggestion based on state}
```

---

## Test Implementation

**File**: `claude-code/tests/commands/test_commands.py`
**Class**: `TestStatusCommand`
**Tests**: 4

```python
class TestStatusCommand:
    def test_status_empty_workspace(self, empty_workspace):
        """ST-001: Status shows zero tasks for empty workspace."""

    def test_status_with_tasks(self, workspace_with_tasks):
        """ST-002/003: Status correctly counts tasks."""

    def test_status_lists_finished_tasks(self, workspace_with_tasks):
        """ST-004: Status can find finished task files."""

    def test_status_no_workspace_error(self, temp_project):
        """ST-005: Error when .ai-workspace missing."""
```

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-F-CMD-001 | Command exists and executes |
| REQ-F-TODO-003 | TODO list displayed in output |

---

## Notes

- This is a read-only command - no files should be modified
- Task counting uses `## Task #` header pattern
- Finished tasks sorted by modification time (most recent first)
