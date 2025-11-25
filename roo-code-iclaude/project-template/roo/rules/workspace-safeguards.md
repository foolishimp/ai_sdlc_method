# Workspace Safeguards

Safety rules to prevent data loss and maintain consistency.

## Core Principles

1. **Idempotency**: Operations can be run multiple times safely
2. **Validation First**: Always verify state before modifying
3. **No Destructive Overwrites**: Read before write, preserve user data
4. **Backup Before Modify**: For release and update operations
5. **REQ Tagging Enforcement**: Warn on missing tags

## Before ANY Write Operation

1. **Verify directory exists**
   ```python
   if not target_dir.exists():
       raise Error("Target directory does not exist")
   ```

2. **Read existing content**
   ```python
   if file.exists():
       existing = file.read_text()
       # Merge, don't replace
   ```

3. **Preserve structure**
   - Don't reorganize user's workspace
   - Don't rename existing files
   - Don't change directory layout

4. **No silent overwrites**
   - Always report what changed
   - Show diff if possible
   - Confirm destructive operations

## Protected Locations

### Never Delete
```
.ai-workspace/tasks/finished/*   # Completed work history
.ai-workspace/tasks/archive/*    # Archived tasks
.roo/memory-bank/*               # User context (update only)
```

### Read Before Write
```
.ai-workspace/tasks/active/ACTIVE_TASKS.md  # Always merge
docs/TRACEABILITY_MATRIX.md                  # Validate before update
```

### Backup Before Modify
```
marketplace.json    # Version bumps need backup
CHANGELOG.md        # Release updates need backup
*.json configs      # Any config change needs backup
```

## Git Safety

### Never Do
- `git push --force` without explicit user request
- `git commit --amend` on commits not authored by current session
- `git reset --hard` without explicit user request
- `--no-verify` to skip hooks

### Always Do
- Include REQ-* tags in commit messages
- Check `git status` before operations
- Verify branch before push
- Check authorship before amend

## Validation Checks

### Before Commit
```
[ ] Code has '# Implements: REQ-*' tags
[ ] Tests have '# Validates: REQ-*' tags
[ ] Commit message includes REQ-* references
[ ] Coverage hasn't dropped below threshold
[ ] All tests pass
```

### Before Release
```
[ ] Backup created
[ ] Version format valid (SemVer)
[ ] CHANGELOG updated
[ ] Tests passing
[ ] Coverage meets minimum
```

### Before Framework Update
```
[ ] Backup of .ai-workspace/
[ ] Backup of .roo/
[ ] User data locations identified
[ ] Merge strategy for conflicts
```

## Recovery Protocol

### If Something Goes Wrong

1. **Check backups**
   ```bash
   ls -la /tmp/aisdlc-backup-*
   ```

2. **Use git reflog**
   ```bash
   git reflog
   git checkout HEAD@{1}
   ```

3. **Restore from finished/**
   - Task documentation preserved
   - Can reconstruct from history

4. **Check memory bank**
   - Context preserved in .roo/memory-bank/
   - Can rebuild from activecontext.md

### Backup Locations

| Operation | Backup Location |
|-----------|----------------|
| Release | `/tmp/aisdlc-backup-<project>-<timestamp>` |
| Update | `/tmp/aisdlc-backup-<project>-<timestamp>` |
| Reset | `/tmp/aisdlc-backup-<project>-<timestamp>` |

## Workspace Structure Validation

Before any workspace operation:

```python
def validate_workspace():
    required = [
        ".ai-workspace/tasks/active",
        ".ai-workspace/tasks/finished",
        ".ai-workspace/templates",
        ".ai-workspace/config"
    ]
    for path in required:
        if not Path(path).exists():
            raise Error(f"Missing required: {path}")
```

## Error Handling

### On Validation Failure
1. Report what's wrong
2. Don't proceed with operation
3. Suggest fix or recovery

### On Write Failure
1. Don't leave partial state
2. Restore from backup if available
3. Report what happened

### On Unexpected State
1. Stop and report
2. Don't try to "fix" automatically
3. Ask user for guidance

## Remember

- User data is sacred
- Backups are cheap, data loss is expensive
- Validation is faster than recovery
- Explicit is better than implicit
