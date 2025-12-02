# TCS-008: Lifecycle Hooks

**Status**: 📋 Specified
**Date**: 2025-11-27
**Requirements**: REQ-F-HOOKS-001, REQ-NFR-CONTEXT-001
**ADR Reference**: [ADR-007](../adrs/ADR-007-hooks-for-methodology-automation.md)
**Implementation**: `claude-code/plugins/aisdlc-methodology/hooks/settings.json`

---

## Purpose

Validate that the 4 lifecycle hooks provide implicit methodology automation, complementing the explicit command system.

---

## Hooks Under Test

| Hook | Event | Purpose |
|------|-------|---------|
| SessionStart | Session opens | Show active tasks, last updated |
| Stop | After response | Suggest checkpoint if uncommitted changes |
| PreToolUse (Bash) | Before git commit | Warn if missing REQ-* tag |
| PostToolUse (Edit) | After file edit | Auto-format edited files |

---

## Preconditions

- Hooks installed via `setup_hooks.py` or `aisdlc-setup.py --hooks`
- `.ai-workspace/tasks/active/ACTIVE_TASKS.md` exists
- Git repository initialized (for PreToolUse)
- Formatters installed (for PostToolUse): prettier, black, gofmt

---

## Test Scenarios

### SessionStart Hook

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| HK-SS-001 | Workspace exists | ACTIVE_TASKS.md present | Shows task count and last updated | High |
| HK-SS-002 | No workspace | .ai-workspace/ missing | No output (graceful skip) | High |
| HK-SS-003 | Empty tasks | Zero tasks | Shows "0 Active Tasks" | Medium |

### Stop Hook

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| HK-ST-001 | Uncommitted changes | >2 modified files | Suggests checkpoint command | High |
| HK-ST-002 | Clean state | No uncommitted changes | No output | High |
| HK-ST-003 | No workspace | .ai-workspace/ missing | No output (graceful skip) | Medium |

### PreToolUse Hook (Bash/git commit)

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| HK-PT-001 | Missing REQ tag | git commit without REQ-* | Warning message shown | High |
| HK-PT-002 | Has REQ tag | git commit with REQ-F-* | No warning | High |
| HK-PT-003 | Has Implements: | git commit with "Implements:" | No warning | High |
| HK-PT-004 | Non-commit command | Any other bash command | No action | Medium |

### PostToolUse Hook (Edit)

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| HK-PU-001 | Python file | .py file edited | black runs silently | Medium |
| HK-PU-002 | JavaScript file | .js/.ts file edited | prettier runs silently | Medium |
| HK-PU-003 | Go file | .go file edited | gofmt runs silently | Medium |
| HK-PU-004 | No formatter | Formatter not installed | Silent failure (no error) | Medium |
| HK-PU-005 | Unknown type | .xyz file edited | No action | Low |

---

## Validation Criteria

### SessionStart
- [ ] Only fires when .ai-workspace exists
- [ ] Shows task count correctly
- [ ] Shows last updated timestamp
- [ ] Output formatted with box drawing characters

### Stop
- [ ] Only fires when uncommitted changes > 2
- [ ] Suggests `/aisdlc-checkpoint-tasks` command
- [ ] Silent when no changes

### PreToolUse
- [ ] Only fires on git commit commands
- [ ] Checks for REQ-* pattern in commit message
- [ ] Checks for "Implements:" in commit message
- [ ] Shows warning (doesn't block)

### PostToolUse
- [ ] Runs appropriate formatter for file type
- [ ] Silent on success
- [ ] Silent on failure (formatter missing)
- [ ] Only runs on supported file types

---

## Hook Configuration

**File**: `claude-code/plugins/aisdlc-methodology/hooks/settings.json`

```json
{
  "hooks": {
    "SessionStart": [...],
    "Stop": [...],
    "PreToolUse": [{ "matcher": "Bash", ... }],
    "PostToolUse": [{ "matcher": "Edit", ... }]
  }
}
```

---

## Test Implementation

**Status**: 📋 Not yet implemented

Hooks require Claude Code integration testing. Manual validation steps:

1. **SessionStart**: Start new Claude session, observe context output
2. **Stop**: Complete work, observe checkpoint suggestion
3. **PreToolUse**: Commit without REQ tag, observe warning
4. **PostToolUse**: Edit Python file, verify black formatting applied

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-F-HOOKS-001 | Lifecycle hooks fire at correct events |
| REQ-NFR-CONTEXT-001 | SessionStart provides automatic context |

---

## Design Principles Validated

1. **Ambient Assistance** - SessionStart auto-shows context
2. **Guardrails Not Gates** - PreToolUse warns, doesn't block
3. **Invisible When Working** - PostToolUse silent on success
4. **Complement Commands** - Stop suggests checkpoint command

---

## Notes

- Hooks run with user credentials - security considerations apply
- All hooks fail silently on error - don't break workflow
- Hooks are optional - methodology works without them
- Install with: `python aisdlc-setup.py --hooks`
