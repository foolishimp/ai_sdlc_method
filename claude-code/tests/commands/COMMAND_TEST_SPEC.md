# AISDLC Command Test Specification

**Version**: 1.0.0
**Date**: 2025-11-27
**Status**: Active

<!-- Implements: REQ-NFR-QUALITY-001 (Code Quality Standards) -->

---

## Overview

This document specifies test cases for validating the 7 AISDLC slash commands. Each command has:
- **Preconditions**: Required state before command execution
- **Test Cases**: Specific scenarios to validate
- **Expected Outcomes**: What should happen
- **Validation Criteria**: How to verify success

---

## Command 1: /aisdlc-status

**Purpose**: Display current task queue status.

### Preconditions
- `.ai-workspace/` directory exists
- ACTIVE_TASKS.md file exists (may be empty)

### Test Cases

| ID | Scenario | Input State | Expected Output |
|----|----------|-------------|-----------------|
| ST-001 | Empty workspace | No tasks in ACTIVE_TASKS.md | Shows "0 Active Tasks", "(No tasks in progress)" |
| ST-002 | Single active task | 1 task in ACTIVE_TASKS.md | Shows "1 Active Task", lists task title |
| ST-003 | Multiple active tasks | 3 tasks in ACTIVE_TASKS.md | Shows "3 Active Tasks", lists all titles |
| ST-004 | With finished tasks | 2 finished task files | Shows "2 Recently Finished", lists names |
| ST-005 | No workspace | Missing .ai-workspace/ | Error message with setup instructions |
| ST-006 | Malformed ACTIVE_TASKS.md | Invalid markdown | Graceful handling, shows what's parseable |

### Validation Criteria
- [ ] Output contains "AI SDLC Task Status" header
- [ ] Active task count matches actual tasks in file
- [ ] Task titles are correctly extracted
- [ ] Recently finished tasks are listed (max 5)
- [ ] Suggestion provided based on state

---

## Command 2: /aisdlc-checkpoint-tasks

**Purpose**: Checkpoint active tasks against conversation context.

### Preconditions
- `.ai-workspace/tasks/active/ACTIVE_TASKS.md` exists
- Conversation context available

### Test Cases

| ID | Scenario | Input State | Expected Output |
|----|----------|-------------|-----------------|
| CP-001 | No work done | Tasks exist, no context | All tasks remain unchanged |
| CP-002 | Task completed | Work matches acceptance criteria | Task moved to finished, archive created |
| CP-003 | Task in progress | Partial work done | Status updated to "In Progress" |
| CP-004 | Task blocked | Blocker discovered | Status updated to "Blocked", reason noted |
| CP-005 | Multiple updates | Various work on multiple tasks | Each task updated appropriately |
| CP-006 | Empty workspace | No active tasks | Message: "No active tasks to checkpoint" |

### Validation Criteria
- [ ] ACTIVE_TASKS.md timestamp updated
- [ ] Completed tasks create finished document
- [ ] Finished document follows template format
- [ ] Summary report shows all status changes
- [ ] Files Updated section lists all modified files

### File Validation
```bash
# Verify finished task created
ls .ai-workspace/tasks/finished/*.md | wc -l

# Verify timestamp updated
grep "Last Updated" .ai-workspace/tasks/active/ACTIVE_TASKS.md
```

---

## Command 3: /aisdlc-commit-task

**Purpose**: Commit completed task with proper formatting.

### Preconditions
- Finished task document exists
- Git repository initialized
- Changes staged or unstaged

### Test Cases

| ID | Scenario | Input State | Expected Output |
|----|----------|-------------|-----------------|
| CM-001 | Valid task ID | Finished doc exists | Commit created with formatted message |
| CM-002 | With REQ tags | Task has requirement keys | Commit includes "Implements: REQ-*" |
| CM-003 | No finished doc | Task ID not found | Error: "Finished task document not found" |
| CM-004 | No changes | Nothing to commit | Warning: "Nothing to commit" |
| CM-005 | User rejects | User says no to commit | No commit made |
| CM-006 | Multi-task commit | Multiple tasks finished | Each task committed separately |

### Validation Criteria
- [ ] Commit message shows to user before committing
- [ ] Commit message includes task ID and title
- [ ] REQ keys included if present
- [ ] TDD: RED → GREEN → REFACTOR line present
- [ ] Co-Author tag included
- [ ] Commit hash returned on success

### Commit Message Format
```
Task #{id}: {title}

{Brief summary of problem}

{Brief summary of solution}

Tests: {test_summary}
TDD: RED → GREEN → REFACTOR

Implements: {REQ keys}

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Command 4: /aisdlc-finish-task

**Purpose**: Complete task and create finished document.

### Preconditions
- Task exists in ACTIVE_TASKS.md
- Work is complete (tests passing, criteria met)

### Test Cases

| ID | Scenario | Input State | Expected Output |
|----|----------|-------------|-----------------|
| FT-001 | Valid completion | Task fully complete | Finished doc created, task removed from active |
| FT-002 | Task not found | Invalid task ID | Error: "Task #{id} not found" |
| FT-003 | Incomplete task | Tests failing | Warning: "Task may not be complete" |
| FT-004 | All fields filled | Complete task info | All template sections populated |
| FT-005 | Missing info | Partial task info | Sections marked as "Not documented" |

### Validation Criteria
- [ ] Finished document created at correct path
- [ ] Filename format: `{YYYYMMDD_HHMM}_{task_slug}.md`
- [ ] All template sections present
- [ ] Task removed from ACTIVE_TASKS.md
- [ ] Confirmation message with file path

### Template Sections
- Problem
- Investigation
- Solution
- TDD Process
- Files Modified
- Test Coverage
- Result
- Side Effects
- Future Considerations
- Lessons Learned
- Traceability
- Metrics

---

## Command 5: /aisdlc-refresh-context

**Purpose**: Refresh Claude's AI SDLC methodology context.

### Preconditions
- `.ai-workspace/` directory exists
- Method reference file exists

### Test Cases

| ID | Scenario | Input State | Expected Output |
|----|----------|-------------|-----------------|
| RC-001 | Full workspace | All files present | Full context refresh, ready message |
| RC-002 | Missing method ref | No AISDLC_METHOD_REFERENCE.md | Warning with setup instructions |
| RC-003 | Active tasks exist | Tasks in progress | Lists active tasks, asks which to work on |
| RC-004 | Empty active tasks | No current work | Suggests /aisdlc-start-session |
| RC-005 | Corrupted files | Invalid markdown | Graceful error handling |

### Validation Criteria
- [ ] Output contains "Context Refreshed" header
- [ ] Workspace structure confirmed
- [ ] Workflow steps listed
- [ ] Critical rules listed
- [ ] 7-Stage SDLC mentioned
- [ ] Ready to begin prompt shown

### Expected Sections in Output
```
✅ Workspace Structure Loaded
✅ Workflow Loaded
✅ Critical Rules Loaded
✅ 7-Stage SDLC Loaded
📚 Full Method Reference
🚀 Ready to Begin!
```

---

## Command 6: /aisdlc-release

**Purpose**: Create project release with version bump.

### Preconditions
- Git repository initialized
- At least one commit exists
- On main branch (or acknowledged warning)

### Test Cases

| ID | Scenario | Input State | Expected Output |
|----|----------|-------------|-----------------|
| RL-001 | Clean state | No uncommitted changes, on main | Release created, tag incremented |
| RL-002 | Uncommitted changes | Modified files not committed | Error: "Uncommitted changes detected" |
| RL-003 | Not on main | On feature branch | Warning: "Not on main branch" |
| RL-004 | First release | No existing tags | Creates v0.0.1 |
| RL-005 | Build bump | v0.4.0 exists | Creates v0.4.1 |
| RL-006 | Dry run | --dry-run flag | Shows what would happen, no changes |
| RL-007 | No commits since tag | Tag is HEAD | Warning: "No changes since last release" |

### Validation Criteria
- [ ] Pre-release checks executed (git status, branch)
- [ ] Version correctly incremented (patch only)
- [ ] Changelog generated from commits
- [ ] Annotated tag created locally
- [ ] Next steps provided (push instructions)
- [ ] No automatic push to remote

### Version Format
```
v{MAJOR}.{MINOR}.{PATCH}
Example: v0.4.0 → v0.4.1
```

---

## Command 7: /aisdlc-update

**Purpose**: Update AI SDLC framework from GitHub.

### Preconditions
- Internet connectivity
- Write access to project directory

### Test Cases

| ID | Scenario | Input State | Expected Output |
|----|----------|-------------|-----------------|
| UP-001 | Standard update | Latest tag available | Framework files updated |
| UP-002 | Specific tag | --tag v0.4.0 | That version installed |
| UP-003 | Dry run | --dry-run flag | Preview shown, no changes |
| UP-004 | No network | Offline | Error: "Cannot fetch from GitHub" |
| UP-005 | Invalid tag | --tag v99.99.99 | Error: "Tag not found" |
| UP-006 | Preserve active work | Tasks in progress | ACTIVE_TASKS.md unchanged |
| UP-007 | Backup creation | Any update | Backup created in /tmp/ |

### Validation Criteria
- [ ] Backup created before changes
- [ ] Templates updated
- [ ] Commands updated
- [ ] Agents updated
- [ ] Active work preserved
- [ ] Project-specific CLAUDE.md sections preserved
- [ ] Validation checks pass
- [ ] Summary report provided

### Preserved Files
- `.ai-workspace/tasks/active/ACTIVE_TASKS.md`
- `.ai-workspace/tasks/finished/*`
- `.ai-workspace/session/*`
- `config/config.yml`
- `.claude/settings.local.json`
- Project-specific CLAUDE.md sections

### Updated Files
- `.ai-workspace/templates/*`
- `.ai-workspace/config/*`
- `.ai-workspace/README.md`
- `.claude/commands/*`
- `.claude/agents/*`
- `CLAUDE.md` (framework sections only)

---

## Integration Test Scenarios

### Scenario INT-001: Full Workflow
1. `/aisdlc-refresh-context` - Initialize context
2. Create task in ACTIVE_TASKS.md manually
3. `/aisdlc-status` - Verify task shows
4. Do work (create files, run tests)
5. `/aisdlc-checkpoint-tasks` - Update status
6. `/aisdlc-finish-task #{id}` - Complete task
7. `/aisdlc-commit-task #{id}` - Commit changes
8. `/aisdlc-release` - Create release

### Scenario INT-002: Context Recovery
1. Lose context (long conversation)
2. `/aisdlc-refresh-context` - Recover
3. `/aisdlc-status` - Verify state preserved

### Scenario INT-003: Update After Work
1. Have active tasks
2. `/aisdlc-update` - Update framework
3. `/aisdlc-status` - Verify tasks preserved
4. Continue work normally

---

## Test Fixtures

### Fixture: Empty Workspace
```bash
mkdir -p .ai-workspace/tasks/active
mkdir -p .ai-workspace/tasks/finished
echo "# Active Tasks\n\n*Last Updated: 2025-11-27*\n" > .ai-workspace/tasks/active/ACTIVE_TASKS.md
```

### Fixture: Single Task
```markdown
# Active Tasks

*Last Updated: 2025-11-27 12:00*

---

## Task #1: Test Task

**Priority**: Medium
**Status**: In Progress
**Requirements**: REQ-F-TEST-001

**Description**: A test task for validation.

**Acceptance Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2
```

### Fixture: Finished Task Document
```markdown
# Task: Test Task Completed

**Status**: Completed
**Date**: 2025-11-27
**Time**: 14:00
**Task ID**: #1
**Requirements**: REQ-F-TEST-001

## Problem
Test problem description.

## Solution
Test solution description.

## Result
✅ Task completed successfully
```

---

## Automation

Tests can be automated using:
1. **Python pytest** - For file state validation
2. **Shell scripts** - For command output capture
3. **Claude Code** - For semantic behavior validation

See `test_commands.py` for implementation.

---

**Last Updated**: 2025-11-27
