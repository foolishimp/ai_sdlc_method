# ADR-204: Workspace Safeguards and Safety Model

## Status

Accepted

## Context

AI coding tools can inadvertently cause data loss or corruption if not properly constrained. The AISDLC methodology requires safeguards to protect:
- User task data in `.ai-workspace/`
- Requirement traceability in code
- Git history integrity
- Framework configuration

Claude Code addresses this via slash command behaviors and CLAUDE.md guidelines. Roo Code needs equivalent safeguards embedded in modes and rules.

### Requirements Addressed

- REQ-F-WORKSPACE-001: Workspace Structure
- REQ-F-CMD-001: Slash Commands for Workflow (safety aspects)
- REQ-NFR-TRACE-002: Requirement Key Propagation

### Safety Principles

1. **Idempotency**: Operations can be run multiple times safely
2. **Validation First**: Always verify state before modifying
3. **No Destructive Overwrites**: Read before write, preserve user data
4. **Backup Before Modify**: For release and update operations
5. **REQ Tagging Enforcement**: Warn on missing tags

## Decision

Implement safeguards via **workspace-safeguards.md** rule file and embedded mode instructions.

### workspace-safeguards.md Content

```markdown
# Workspace Safeguards

## Before ANY Write Operation

1. **Verify directory exists**: Check target path before write
2. **Read existing content**: If file exists, read it first
3. **Preserve structure**: Don't reorganize user's workspace
4. **No silent overwrites**: Always report what changed

## Protected Locations

### Never Delete
- `.ai-workspace/tasks/finished/*` - Completed work history
- `.ai-workspace/tasks/archive/*` - Archived tasks
- `.roo/memory-bank/*` - User context (update only)

### Read Before Write
- `.ai-workspace/tasks/active/ACTIVE_TASKS.md` - Always merge, don't replace
- `docs/TRACEABILITY_MATRIX.md` - Validate before update

### Backup Before Modify
- `marketplace.json` - Version bumps need backup
- `CHANGELOG.md` - Release updates need backup

## Git Safety

- No `--force` push without explicit user request
- No `--amend` on commits not authored by current session
- No `--no-verify` to skip hooks
- Always include REQ-* tags in commit messages

## Validation Checks

Before commit:
- [ ] Code has `# Implements: REQ-*` tags
- [ ] Tests have `# Validates: REQ-*` tags
- [ ] Commit message includes REQ-* references
- [ ] Coverage hasn't dropped below threshold

## Recovery Protocol

If something goes wrong:
1. Check `/tmp/aisdlc-backup-*` for recent backups
2. Use `git reflog` to find lost commits
3. Restore from `.ai-workspace/tasks/finished/` if tasks lost
```

### Mode-Embedded Safety

Each mode includes safety checks in customInstructions:
```json
{
  "customInstructions": "@rules/workspace-safeguards.md\n\nBefore modifying any file:\n1. Read current content\n2. Validate structure\n3. Make minimal changes\n4. Report what changed"
}
```

### Command-Specific Safety

| Command | Safety Behavior |
|---------|-----------------|
| Checkpoint | Validate ACTIVE_TASKS.md structure before update |
| Finish Task | Create doc before removing from active |
| Commit | Require REQ-* tag in message |
| Release | Create backup before version bump |
| Update | Preserve user data, backup before overwrite |

## Consequences

### Positive

- **Data Safety**: User work protected from accidental loss
- **Predictability**: Operations behave consistently
- **Recoverability**: Backups enable rollback
- **Traceability**: REQ tags enforced throughout
- **Parity**: Matches Claude/Codex safety behaviors

### Negative

- **Performance**: Extra reads before writes
- **Verbosity**: More validation messages
- **Complexity**: More rules for AI to follow

### Mitigations

- Validation is fast for small files
- Messages are informative, not verbose
- Rules are clearly documented in one file

## References

- REQ-F-WORKSPACE-001: Workspace Structure
- REQ-NFR-TRACE-002: Requirement Key Propagation
- Claude `/aisdlc-*` command safety behaviors
- Git safety protocol from CLAUDE.md
