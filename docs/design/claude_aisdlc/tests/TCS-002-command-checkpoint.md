# TCS-002: /aisdlc-checkpoint-tasks Command

**Status**: ✅ Implemented
**Date**: 2025-11-27
**Requirements**: REQ-F-WORKSPACE-002, REQ-NFR-CONTEXT-001
**ADR Reference**: [ADR-002](../adrs/ADR-002-commands-for-workflow-integration.md)
**Implementation**: `claude-code/plugins/aisdlc-methodology/commands/aisdlc-checkpoint-tasks.md`

---

## Purpose

Validate that the `/aisdlc-checkpoint-tasks` command correctly evaluates active tasks against conversation context and updates task statuses appropriately.

---

## Preconditions

- `.ai-workspace/tasks/active/ACTIVE_TASKS.md` exists
- Conversation context available with work history
- `.ai-workspace/templates/FINISHED_TASK_TEMPLATE.md` exists

---

## Test Scenarios

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| CP-001 | No work done | Tasks exist, no relevant context | All tasks remain unchanged | High |
| CP-002 | Task completed | Work matches acceptance criteria | Task archived, finished doc created | High |
| CP-003 | Task in progress | Partial work done | Status updated to "In Progress" | High |
| CP-004 | Task blocked | Blocker discovered in context | Status updated to "Blocked" | Medium |
| CP-005 | Multiple updates | Various work on multiple tasks | Each task updated appropriately | High |
| CP-006 | Empty workspace | No active tasks | Message: "No active tasks to checkpoint" | Medium |

---

## Validation Criteria

- [ ] ACTIVE_TASKS.md timestamp updated on any change
- [ ] Completed tasks create finished document in `tasks/finished/`
- [ ] Finished document follows `FINISHED_TASK_TEMPLATE.md` format
- [ ] Finished document filename: `{YYYYMMDD_HHMM}_{task_slug}.md`
- [ ] Completed task removed from ACTIVE_TASKS.md
- [ ] Completed task added to "Recently Completed" section
- [ ] Summary report shows all status changes
- [ ] "Files Updated" section lists all modified files

---

## Expected Output Format

```
╔══════════════════════════════════════════════════════════════╗
║              Task Checkpoint - {YYYY-MM-DD HH:MM}            ║
╚══════════════════════════════════════════════════════════════╝

📊 Evaluation Summary:
   ✅ Completed: {count} task(s)
   🔄 In Progress: {count} task(s)
   🚫 Blocked: {count} task(s)
   ⏸️  Not Started: {count} task(s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Completed Tasks:
   {list with archive paths}

🔄 In Progress:
   {list with progress notes}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💾 Files Updated:
   - .ai-workspace/tasks/active/ACTIVE_TASKS.md
   {- .ai-workspace/tasks/finished/... for each completed}

💡 Next Steps:
   {suggestion}
```

---

## Test Implementation

**File**: `claude-code/tests/commands/test_commands.py`
**Class**: `TestCheckpointCommand`
**Tests**: 3

```python
class TestCheckpointCommand:
    def test_checkpoint_updates_timestamp(self, workspace_with_tasks):
        """CP-001: Checkpoint updates ACTIVE_TASKS.md timestamp."""

    def test_checkpoint_creates_finished_document(self, workspace_with_tasks):
        """CP-002: Completed tasks create finished documents."""

    def test_finished_document_filename_format(self, workspace_with_tasks):
        """CP-003: Finished document filename follows format."""
```

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-F-WORKSPACE-002 | Task management templates used correctly |
| REQ-NFR-CONTEXT-001 | Context from conversation used for evaluation |

---

## Notes

- Command uses conversation context - relevant work must be visible
- For ambiguous cases, command should ask for clarification
- Use before `/aisdlc-status` to ensure accurate status display
