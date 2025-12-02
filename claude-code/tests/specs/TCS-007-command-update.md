# TCS-007: /aisdlc-update Command

**Status**: ✅ Implemented
**Date**: 2025-11-27
**Requirements**: REQ-F-UPDATE-001
**ADR Reference**: [ADR-002](../adrs/ADR-002-commands-for-workflow-integration.md)
**Implementation**: `claude-code/plugins/aisdlc-methodology/commands/aisdlc-update.md`

---

## Purpose

Validate that the `/aisdlc-update` command correctly updates AI SDLC framework files from GitHub while preserving project-specific content and active work.

---

## Preconditions

- Internet connectivity (for GitHub fetch)
- Write access to project directory
- `.ai-workspace/` exists (or will be created)

---

## Test Scenarios

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| UP-001 | Standard update | Latest tag available | Framework files updated | High |
| UP-002 | Specific tag | --tag v0.4.0 | That specific version installed | Medium |
| UP-003 | Dry run | --dry-run flag | Preview shown, no changes | Medium |
| UP-004 | No network | Offline | Error: "Cannot fetch from GitHub" | High |
| UP-005 | Invalid tag | --tag v99.99.99 | Error: "Tag not found" | Medium |
| UP-006 | Preserve active work | Tasks in progress | ACTIVE_TASKS.md unchanged | High |
| UP-007 | Backup creation | Any update | Backup created in /tmp/ | High |

---

## Validation Criteria

- [ ] Backup created before any changes
- [ ] Templates directory updated
- [ ] Commands directory updated
- [ ] Agents directory updated
- [ ] Active tasks preserved (not modified)
- [ ] Finished tasks preserved (not modified)
- [ ] Project-specific CLAUDE.md sections preserved
- [ ] Validation checks pass after update
- [ ] Summary report provided

---

## Preserved Files (Never Modified)

| File/Directory | Reason |
|----------------|--------|
| `.ai-workspace/tasks/active/ACTIVE_TASKS.md` | Active work |
| `.ai-workspace/tasks/finished/*` | Completed work history |
| `.ai-workspace/session/*` | Session state |
| `config/config.yml` | Project-specific config |
| `.claude/settings.local.json` | Local Claude settings |
| Project-specific CLAUDE.md sections | Custom documentation |

---

## Updated Files (Replaced with Latest)

| File/Directory | Action |
|----------------|--------|
| `.ai-workspace/templates/*` | Replaced |
| `.ai-workspace/config/*` | Merged (new files added) |
| `.ai-workspace/README.md` | Replaced |
| `.claude/commands/*` | Replaced |
| `.claude/agents/*` | Replaced |
| `CLAUDE.md` | Framework sections only |

---

## Expected Output Format

```
╔══════════════════════════════════════════════════════════════╗
║           AI SDLC Framework Update Complete                  ║
╚══════════════════════════════════════════════════════════════╝

📦 Version: v0.4.0 → v0.4.1
🔗 Source: https://github.com/foolishimp/ai_sdlc_method
🏷️  Tag: v0.4.1

✅ Updated:
   - .ai-workspace/templates/
   - .ai-workspace/config/
   - .claude/commands/
   - .claude/agents/

🔒 Preserved:
   - .ai-workspace/tasks/active/ACTIVE_TASKS.md
   - .ai-workspace/tasks/finished/*

💾 Backup Location: /tmp/aisdlc-backup-project-20251127_140000

📝 Next Steps:
   1. Review changes: git diff
   2. Test commands: /aisdlc-status
   3. Commit if satisfied
```

---

## Test Implementation

**File**: `claude-code/tests/commands/test_commands.py`
**Class**: `TestUpdateCommand`
**Tests**: 2

```python
class TestUpdateCommand:
    def test_update_preserves_active_tasks(self, workspace_with_tasks):
        """UP-006: Update preserves active work."""

    def test_update_creates_backup(self, workspace_with_tasks):
        """UP-007: Update creates backup."""
```

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-F-UPDATE-001 | Framework updates from GitHub work correctly |

---

## Rollback Procedure

```bash
# Find backup
ls -la /tmp/aisdlc-backup-*/

# Restore from backup
BACKUP="/tmp/aisdlc-backup-project-20251127_140000"
cp -r "$BACKUP/.ai-workspace" .
cp -r "$BACKUP/.claude" .
cp "$BACKUP/CLAUDE.md" .

echo "Rollback complete"
```

---

## Notes

- Always creates backup before making changes
- Uses rsync for intelligent file merging
- Project-specific content identified by markers in CLAUDE.md
- Dry-run mode recommended before actual update
