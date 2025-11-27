# TCS-005: /aisdlc-refresh-context Command

**Status**: ✅ Implemented
**Date**: 2025-11-27
**Requirements**: REQ-F-CMD-001, REQ-NFR-CONTEXT-001
**ADR Reference**: [ADR-002](../adrs/ADR-002-commands-for-workflow-integration.md)
**Implementation**: `claude-code/plugins/aisdlc-methodology/commands/aisdlc-refresh-context.md`

---

## Purpose

Validate that the `/aisdlc-refresh-context` command correctly reloads AI SDLC methodology context, workspace structure, and critical rules into Claude's working memory.

---

## Preconditions

- `.ai-workspace/` directory exists
- Method reference file exists at `templates/AISDLC_METHOD_REFERENCE.md`

---

## Test Scenarios

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| RC-001 | Full workspace | All files present | Full context refresh, ready message | High |
| RC-002 | Missing method ref | No AISDLC_METHOD_REFERENCE.md | Warning with setup instructions | High |
| RC-003 | Active tasks exist | Tasks in progress | Lists active tasks, asks which to work on | Medium |
| RC-004 | Empty active tasks | No current work | Suggests /aisdlc-start-session | Medium |
| RC-005 | Corrupted files | Invalid markdown | Graceful error handling | Low |

---

## Validation Criteria

- [ ] Output contains "Context Refreshed" header box
- [ ] Workspace structure confirmed (todos, active, finished)
- [ ] Workflow steps listed correctly
- [ ] Critical rules listed
- [ ] 7-Stage SDLC mentioned
- [ ] "Ready to Begin!" prompt shown
- [ ] Active tasks listed if present
- [ ] Suggestion based on state provided

---

## Expected Output Format

```
╔══════════════════════════════════════════════════════════════╗
║         AI SDLC Context Refreshed - Ready to Work            ║
╚══════════════════════════════════════════════════════════════╝

✅ Workspace Structure Loaded
   - Todos: .ai-workspace/tasks/todo/
   - Active: .ai-workspace/tasks/active/
   - Finished: .ai-workspace/tasks/finished/

✅ Workflow Loaded
   1. /aisdlc-start-session (begin)
   2. Use TodoWrite tool (track progress)
   3. /aisdlc-checkpoint-tasks (after work)
   4. /aisdlc-commit-task (commit)

✅ Critical Rules Loaded
   - NEVER put finished tasks outside .ai-workspace/
   - ALWAYS use TodoWrite tool during work
   - ALWAYS checkpoint after completing work
   - ASK if unsure about anything

✅ 7-Stage SDLC Loaded
   Current stage: {detect from context or ask}

📚 Full Method Reference:
   .ai-workspace/templates/AISDLC_METHOD_REFERENCE.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 Ready to Begin!

What would you like to work on?
```

---

## Test Implementation

**File**: `claude-code/tests/commands/test_commands.py`
**Class**: `TestRefreshContextCommand`
**Tests**: 2

```python
class TestRefreshContextCommand:
    def test_refresh_verifies_workspace_structure(self, workspace_with_tasks):
        """RC-001: Refresh verifies workspace structure."""

    def test_refresh_checks_method_reference(self, workspace_with_tasks):
        """RC-002: Refresh checks for method reference."""
```

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-F-CMD-001 | Command exists and executes |
| REQ-NFR-CONTEXT-001 | Persistent context loaded correctly |

---

## When to Use

- Start of every session
- After context loss (long conversations)
- After making methodology violations
- When feeling unsure about workflow
- Before starting any significant work

---

## Notes

- This is a "context refresh" command, not a "session start" command
- Read-only command - no file modifications
- Helps recover from context loss in long conversations
