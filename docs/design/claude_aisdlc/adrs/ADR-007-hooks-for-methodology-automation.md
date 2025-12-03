# ADR-007: Hooks for Methodology Automation

**Status**: Proposed
**Date**: 2025-11-27
**Deciders**: Development Tools Team
**Requirements**: REQ-TOOL-008 (Methodology Hooks - NEW), REQ-TOOL-002 (Developer Workspace)
**Depends On**: ADR-002 (Commands for Workflow Integration)

---

## Context

The AISDLC command system (ADR-002) provides 7 explicit commands for workflow integration. However, users must remember to invoke these commands - methodology compliance depends on user discipline.

### The Problem

1. **Session context lost**: Users forget where they left off
2. **Checkpoints missed**: Work completed but not documented
3. **Traceability gaps**: Commits made without REQ-* tags
4. **Inconsistent formatting**: Code style varies without enforcement

**Root cause**: Commands are explicit - users must invoke them. For methodology compliance to be reliable, some behaviors should be **implicit**.

---

## Decision

**We will use Claude Code's lifecycle hooks to automate methodology compliance, complementing the explicit command system.**

Specifically:
- **2 lifecycle hooks** for key automation points
- **Guardrails not gates** - warn, don't block
- **Silent success** - only notify on issues
- **Complement commands** - hooks suggest, commands execute

---

## Hook Implementation

### Selected Hooks (2 of 10 available)

| Hook Event | Purpose | Behavior |
|------------|---------|----------|
| **Stop** | Checkpoint reminder | Suggest `/aisdlc-checkpoint-tasks` if uncommitted changes |
| **PreToolUse** | REQ validation | Warn on commits without REQ-* tags |

### Rejected Hooks (and Why)

| Hook Event | Rejection Reason |
|------------|------------------|
| SessionStart | Context loading unreliable in practice |
| PostToolUse | Auto-formatting adds complexity without clear benefit |
| PermissionRequest | Too intrusive for methodology |
| Notification | Not relevant to SDLC workflow |
| SubagentStop | Internal agent handling |
| PreCompact | Automatic operation |
| SessionEnd | No action needed |
| UserPromptSubmit | Considered but too noisy |

---

## Rationale

### Why Hooks + Commands (Not Just One)

```
Commands Only:              Hooks Only:
┌─────────────────┐        ┌─────────────────┐
│ User remembers  │        │ No explicit     │
│ to invoke       │        │ control         │
│                 │        │                 │
│ ❌ Often forgot │        │ ❌ Too magical  │
└─────────────────┘        └─────────────────┘

Commands + Hooks:
┌─────────────────────────────────────────┐
│ Hooks: Automatic reminders & formatting │
│ Commands: Explicit control when needed  │
│                                         │
│ ✅ Best of both: ambient + intentional  │
└─────────────────────────────────────────┘
```

### Design Principles Applied

**1. Ambient Assistance**
- SessionStart automatically shows context
- User doesn't need to run `/aisdlc-status` first thing

**2. Guardrails Not Gates**
- PreToolUse warns about missing REQ tags
- Doesn't block the commit (that would be frustrating)

**3. Silent Success**
- PostToolUse formatting happens invisibly
- Only outputs on errors

**4. Complement Commands**
- Stop hook suggests: "Run `/aisdlc-checkpoint-tasks`"
- User chooses whether to run it

---

## Configuration

### File Location

Following plugin pattern:
```
claude-code/plugins/aisdlc-methodology/
├── hooks/
│   └── settings.json    ← Hook definitions
├── commands/
│   └── *.md
└── agents/
    └── *.md
```

### Settings.json Structure

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "",
      "hooks": [{ "type": "command", "command": "..." }]
    }],
    "Stop": [...],
    "PreToolUse": [{ "matcher": "Bash", ... }],
    "PostToolUse": [{ "matcher": "Edit", ... }]
  }
}
```

### Installation

```bash
# Installer merges with existing settings
python installers/setup_hooks.py
```

---

## Consequences

### Positive

✅ **Reduced cognitive load**
- Context shown automatically
- Reminders at the right moments
- Formatting happens invisibly

✅ **Better methodology compliance**
- REQ tags prompted at commit time
- Checkpoints suggested after work
- Consistent code style

✅ **Non-intrusive**
- Guardrails not gates
- Suggestions not requirements
- Silent on success

✅ **Complementary to commands**
- Hooks automate common cases
- Commands remain for explicit control

### Negative

⚠️ **Claude Code specific**
- Hooks only work in Claude Code
- Other platforms need different automation

**Mitigation**: Hook logic is portable (shell commands)

⚠️ **Security considerations**
- Hooks run with user credentials
- Users must trust hook code

**Mitigation**: All hooks are read-only or formatting-only

⚠️ **Potential noise**
- Too many hooks could be annoying

**Mitigation**: Only 2 hooks, both focused on commit traceability

---

## Implementation Notes

### Hook Command Patterns

**Conditional execution**:
```bash
if [ -f .ai-workspace/tasks/active/ACTIVE_TASKS.md ]; then
  # Only run if AISDLC is installed
fi
```

**Silent failure**:
```bash
prettier --write "$FILE" 2>/dev/null || true
```

**Tool detection**:
```bash
command -v prettier >/dev/null 2>&1 && prettier ...
```

### Environment Variables Used

| Variable | Hook | Purpose |
|----------|------|---------|
| `CLAUDE_TOOL_INPUT` | PreToolUse | Check commit command content |
| `CLAUDE_FILE_PATH` | PostToolUse | Get edited file path |

---

## Metrics

- **Hooks implemented**: 2
- **Hook code lines**: ~30
- **Commands complemented**: 2 (checkpoint, commit)

**UX improvement**: REQ-* tag validation at commit time

---

## Validation

**Requirements coverage**:
- REQ-TOOL-002: ✅ SessionStart provides automatic workspace context
- REQ-TRACE-002: ✅ PreToolUse validates REQ key propagation
- REQ-TOOL-008: ✅ Lifecycle automation implemented (NEW - needs formalization)

---

## Related Decisions

- **ADR-001**: Claude Code as Platform (enables hooks)
- **ADR-002**: Commands for Workflow (hooks complement)
- **ADR-005**: Iterative Refinement (hooks support feedback)

---

## Review Notes

**Hook evolution** (from v0.1.0 settings.json):
- v0.1.0: Complex hooks referencing non-existent commands
- v0.5.0: Minimal hooks with real shell commands

**Lesson**: Hooks should be simple shell commands, not complex integrations.

---

**Status**: Proposed
**Next Steps**:
1. Test hooks in development
2. Create `setup_hooks.py` installer
3. Update QUICKSTART.md with hook documentation
4. Move to Accepted after validation
