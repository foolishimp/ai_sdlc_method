# Hooks System Design (v0.5)

**Version**: 0.5.0
**Date**: 2025-11-27
**Status**: Proposed
**ADR Reference**: [ADR-007-hooks-for-methodology-automation](adrs/ADR-007-hooks-for-methodology-automation.md)

---

## Overview

The AISDLC hooks system provides **implicit automation** that complements the explicit command system. Hooks execute automatically at Claude Code lifecycle points, enforcing methodology compliance without user intervention.

**Philosophy**: Commands are what users invoke. Hooks are what the methodology does for them.

```
┌─────────────────────────────────────────────────────────────┐
│                    AISDLC Interaction Model                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Commands (7)  ──► User-initiated workflow actions         │
│        +                                                    │
│   Hooks (5)     ──► Automatic methodology automation        │
│        =                                                    │
│   Seamless UX   ──► Methodology compliance without friction │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Principles

### 1. Ambient Assistance
Hooks provide context and reminders without requiring user action.
- **Good**: SessionStart shows current task automatically
- **Bad**: Requiring user to run `/aisdlc-status` every session

### 2. Guardrails Not Gates
Hooks warn and suggest, they don't block workflow.
- **Good**: "Missing REQ tag in commit message" (warning)
- **Bad**: Blocking commit entirely (frustrating)

### 3. Progressive Disclosure
Light touch for simple tasks, full methodology for complex work.
- **Good**: Short status for quick sessions, detailed for long work
- **Bad**: Always showing full methodology dump

### 4. Invisible When Working
Hooks should not interrupt flow state.
- **Good**: PostToolUse formatting happens silently
- **Bad**: Popups or confirmations during coding

### 5. Complement Commands
Hooks automate what commands would do manually.
- **Good**: Stop hook suggests checkpoint (user can ignore or run `/aisdlc-checkpoint-tasks`)
- **Bad**: Duplicating command functionality

---

## Claude Code Hook Events

Claude Code provides 10 hook event types. AISDLC uses 5 key lifecycle hooks:

| Hook Event | AISDLC Usage | Priority |
|------------|--------------|----------|
| **SessionStart** | Load context, show status | High |
| **Stop** | Checkpoint reminder | High |
| **PreToolUse** | REQ tag validation | Medium |
| **PostToolUse** | Auto-formatting | Medium |
| **UserPromptSubmit** | Task detection | Low |

### Hooks Not Used (and Why)

| Hook Event | Reason Not Used |
|------------|-----------------|
| PermissionRequest | Too intrusive for methodology |
| Notification | Not relevant to SDLC workflow |
| SubagentStop | Subagent handling is internal |
| PreCompact | Compaction is automatic |
| SessionEnd | No action needed on exit |

---

## Hook Specifications

### 1. SessionStart - Context Loading

**Purpose**: Provide ambient awareness of current work state.

**Trigger**: When Claude Code session starts or resumes.

**Behavior**:
1. Check if `.ai-workspace/tasks/active/ACTIVE_TASKS.md` exists
2. If exists: Show summary (active count, current task, last updated)
3. If not exists: Show AISDLC not installed message

**Output Format**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AISDLC Context Loaded
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Active Tasks: 4 | In Progress: #18 Gemini Parity
Last Updated: 2025-11-27 12:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Implementation**:
```json
{
  "matcher": "",
  "hooks": [{
    "type": "command",
    "command": "if [ -f .ai-workspace/tasks/active/ACTIVE_TASKS.md ]; then echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'; echo 'AISDLC Context Loaded'; echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'; grep -E '^(\\*Last Updated|## Task #|\\*\\*Status\\*\\*: In Progress)' .ai-workspace/tasks/active/ACTIVE_TASKS.md | head -5; echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'; fi"
  }]
}
```

**Design Rationale**:
- Replaces need for manual `/aisdlc-refresh-context` at session start
- Non-blocking (just echo, no interaction required)
- Graceful degradation if workspace not present

---

### 2. Stop - Checkpoint Reminder

**Purpose**: Remind user to checkpoint after significant work.

**Trigger**: When Claude Code finishes responding (after each turn).

**Behavior**:
1. Check if response involved file modifications (Edit/Write tools)
2. If significant work detected: Suggest checkpoint
3. Track file modification count in session

**Output Format**:
```
💡 Checkpoint? Modified 3 files. Run /aisdlc-checkpoint-tasks
```

**Implementation**:
```json
{
  "matcher": "",
  "hooks": [{
    "type": "command",
    "command": "if [ -f .ai-workspace/tasks/active/ACTIVE_TASKS.md ]; then MODIFIED=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' '); if [ \"$MODIFIED\" -gt 0 ]; then echo \"💡 Checkpoint? $MODIFIED uncommitted changes. Run /aisdlc-checkpoint-tasks\"; fi; fi"
  }]
}
```

**Design Rationale**:
- Gentle reminder, not blocking
- Only triggers when there's actual work to checkpoint
- Uses git status as proxy for "significant work"

---

### 3. PreToolUse (Bash/commit) - REQ Tag Validation

**Purpose**: Validate commit messages include requirement traceability.

**Trigger**: Before `git commit` commands.

**Behavior**:
1. Check if commit message contains REQ-* pattern
2. If missing: Warn (don't block)
3. Suggest using `/aisdlc-commit-task` for proper format

**Output Format**:
```
⚠️  Commit missing REQ tag. Consider /aisdlc-commit-task for traceability.
```

**Implementation**:
```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'git commit'; then if ! echo \"$CLAUDE_TOOL_INPUT\" | grep -qE 'REQ-[A-Z]+-[A-Z]+-[0-9]+'; then echo '⚠️  Commit may be missing REQ tag. Consider /aisdlc-commit-task for traceability.'; fi; fi"
  }]
}
```

**Design Rationale**:
- Guardrail not gate (warns, doesn't block)
- Only fires on commit commands
- Reminds of proper workflow command

---

### 4. PostToolUse (Edit) - Auto-Formatting

**Purpose**: Automatically format code after edits.

**Trigger**: After Edit tool completes.

**Behavior**:
1. Detect file type from path
2. Run appropriate formatter (prettier, black, gofmt, etc.)
3. Silent unless error

**Implementation**:
```json
{
  "matcher": "Edit",
  "hooks": [{
    "type": "command",
    "command": "FILE=\"$CLAUDE_FILE_PATH\"; if [ -n \"$FILE\" ]; then case \"$FILE\" in *.js|*.ts|*.jsx|*.tsx|*.json|*.md) prettier --write \"$FILE\" 2>/dev/null || true ;; *.py) black \"$FILE\" 2>/dev/null || true ;; *.go) gofmt -w \"$FILE\" 2>/dev/null || true ;; esac; fi"
  }]
}
```

**Design Rationale**:
- Invisible operation (no output on success)
- Fails silently if formatter not installed
- Respects project's formatting preferences

---

### 5. UserPromptSubmit - Task Detection

**Purpose**: Detect when user prompt relates to active task.

**Trigger**: When user submits a prompt.

**Behavior**:
1. Scan prompt for task references (#N, Task N)
2. Scan prompt for requirement references (REQ-*)
3. If detected: Show relevant task context

**Output Format**:
```
📌 Related: Task #18 (Gemini Implementation Parity) - In Progress
```

**Implementation**:
```json
{
  "matcher": "",
  "hooks": [{
    "type": "command",
    "command": "if echo \"$CLAUDE_USER_INPUT\" | grep -qE '(Task #?[0-9]+|REQ-[A-Z]+-[A-Z]+-[0-9]+)'; then TASK=$(echo \"$CLAUDE_USER_INPUT\" | grep -oE 'Task #?[0-9]+' | head -1); if [ -n \"$TASK\" ]; then echo \"📌 Related: $TASK\"; fi; fi"
  }]
}
```

**Design Rationale**:
- Lightweight context linking
- Only triggers when task reference detected
- Non-intrusive

---

## Hook Configuration

### File Location

Following the plugin pattern:
```
claude-code/plugins/aisdlc-methodology/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── settings.json      # ← Hook configuration
├── commands/
│   └── *.md
└── agents/
    └── *.md
```

### Installation

Hooks are installed via `setup_hooks.py` installer:
```python
# installers/setup_hooks.py
# Copies hooks/settings.json → ~/.claude/settings.json
# Merges with existing settings (doesn't overwrite)
```

### Settings.json Structure

```json
{
  "hooks": {
    "SessionStart": [...],
    "Stop": [...],
    "PreToolUse": [...],
    "PostToolUse": [...],
    "UserPromptSubmit": [...]
  }
}
```

---

## Relationship to Commands

| Command | Related Hook | Relationship |
|---------|--------------|--------------|
| `/aisdlc-status` | SessionStart | Hook auto-shows what command would show |
| `/aisdlc-checkpoint-tasks` | Stop | Hook reminds, command executes |
| `/aisdlc-commit-task` | PreToolUse | Hook warns, command provides proper flow |
| `/aisdlc-refresh-context` | SessionStart | Hook replaces need for command |

**Key Insight**: Hooks make commands **optional** for common cases, but commands remain for **explicit control**.

---

## Security Considerations

Per Claude Code documentation:
> "Hooks run automatically during the agent loop with your current environment's credentials."

**Mitigations**:
1. All hook commands are read-only or formatting-only
2. No network access in hooks
3. No credential handling
4. All commands fail silently on error
5. User can review hooks in settings.json before installation

---

## Metrics

- **Hooks implemented**: 5 (of 10 available event types)
- **Lines per hook**: ~1-3 (shell one-liners)
- **Total hook code**: ~50 lines
- **Installer code**: ~30 lines

**Simplicity maintained**: Hooks are minimal shell commands, not complex scripts.

---

## Requirement Traceability

| Hook | Requirement |
|------|-------------|
| SessionStart | REQ-NFR-CONTEXT-001 (Persistent Context) |
| Stop | REQ-F-WORKSPACE-002 (Task Management) |
| PreToolUse | REQ-NFR-TRACE-001 (Requirement Tagging) |
| PostToolUse | REQ-NFR-QUALITY-001 (Code Quality) - NEW |
| UserPromptSubmit | REQ-NFR-CONTEXT-001 (Persistent Context) |

**New Requirement**: REQ-F-HOOKS-001 (Lifecycle Hooks for Methodology Automation)

---

## Future Considerations

### Potential Additional Hooks

| Hook | Use Case | Priority |
|------|----------|----------|
| PreToolUse (Write) | Validate new files have REQ comments | Low |
| PermissionRequest | Custom permission policies | Low |
| SubagentStop | Agent task completion tracking | Medium |

### Hook Customization

Future versions may support:
- Project-specific hook overrides
- Hook enable/disable toggles
- Custom hook scripts directory

---

## References

- [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide)
- [COMMAND_SYSTEM.md](COMMAND_SYSTEM.md) - Command specifications
- [ADR-002: Commands for Workflow Integration](adrs/ADR-002-commands-for-workflow-integration.md)
- [ADR-007: Hooks for Methodology Automation](adrs/ADR-007-hooks-for-methodology-automation.md)
