# ADR-203: Memory Bank for Persistent Context

## Status

Accepted

## Context

AI coding sessions often lose context between conversations. Users must repeatedly explain project goals, technology choices, and current work focus. Claude Code addresses this via CLAUDE.md auto-loading and ACTIVE_TASKS.md. Roo Code provides a **Memory Bank** feature for persistent context.

### Requirements Addressed

- REQ-NFR-CONTEXT-001: Persistent Context Across Sessions
- REQ-F-WORKSPACE-003: Session Tracking Templates

### Options Considered

1. **Memory bank only**: Use `.roo/memory-bank/` for all persistent context
2. **Workspace only**: Rely on `.ai-workspace/` structure (shared with Claude/Codex)
3. **Hybrid**: Memory bank for Roo-specific context, workspace for shared task tracking

## Decision

Use **Option 3: Hybrid approach**.

### Memory Bank (`.roo/memory-bank/`)

Roo-specific persistent context:

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `projectbrief.md` | Project goals, scope, constraints | On project changes |
| `techstack.md` | Technology decisions, architecture | On tech changes |
| `activecontext.md` | Current work focus (links to ACTIVE_TASKS.md) | Each session |
| `methodref.md` | AISDLC method reference (copied from templates) | On framework update |

### Workspace (`.ai-workspace/`)

Shared task tracking (identical to Claude/Codex):

| Location | Purpose |
|----------|---------|
| `tasks/active/ACTIVE_TASKS.md` | Current tasks with status |
| `tasks/finished/` | Completed task documentation |
| `templates/` | Document templates |
| `config/workspace_config.yml` | Coverage targets, settings |

### Context Loading Order

1. On session start: Memory bank files auto-loaded
2. On mode activation: Mode-specific rules loaded
3. On explicit request: ACTIVE_TASKS.md and workspace files

### Context Refresh Protocol

```
"Refresh context":
1. Re-read activecontext.md (memory bank)
2. Re-read ACTIVE_TASKS.md (workspace)
3. Scan for any recent changes to key files
4. Summarize current state to user
```

## Consequences

### Positive

- **Roo-native**: Uses memory bank feature as designed
- **Parity**: Workspace structure shared with Claude/Codex
- **Separation**: Roo config separate from shared task tracking
- **Portability**: Users can switch AI tools without losing task history

### Negative

- **Two locations**: Context split between memory bank and workspace
- **Sync risk**: activecontext.md might drift from ACTIVE_TASKS.md
- **Setup complexity**: More files to initialize

### Mitigations

- activecontext.md contains pointers to workspace, not duplicates
- Refresh protocol explicitly syncs both sources
- Installer creates both structures together

## References

- REQ-NFR-CONTEXT-001: Persistent Context Across Sessions
- REQ-F-WORKSPACE-003: Session Tracking Templates
- Claude CLAUDE.md auto-loading
- Roo Code memory bank documentation
