# Context History - Session Snapshots

<!-- Implements: REQ-TOOL-012.0.1.0 (Context Snapshot and Recovery) -->

## Purpose

This directory stores context snapshots created by `/aisdlc-snapshot-context` command. Snapshots enable:
- Session continuity after conversation history loss
- Team member handoffs with full context
- Recovery points for complex work sessions
- Historical audit trail of project evolution

## Directory Structure

```
context_history/
├── {YYYYMMDD}_{HHMM}_{label}.md   # Context snapshots
└── README.md                       # This file
```

## Snapshot Filename Format

Follows the finished task convention:
```
{YYYYMMDD}_{HHMM}_{label}.md

Examples:
- 20251216_1430_implementing_auth_service.md
- 20251215_0915_fixing_payment_tests.md
- 20251214_1700_context_snapshot.md  (default label)
```

**Label**: Derived from current work focus (snake_case, max 50 chars)

## Snapshot Contents

Each snapshot includes:
- **Active Tasks Summary** - Current task status and counts
- **Current Work Context** - What's being worked on
- **Conversation State Markers** - Decisions, questions, blockers
- **File Changes** - Modified, staged, untracked files
- **Recovery Guidance** - How to restore this context
- **Metadata** - Timestamps, metrics, related snapshots

## Usage

### Create Snapshot

```bash
# End of work session
/aisdlc-checkpoint-tasks      # Update task status first
/aisdlc-snapshot-context      # Capture full context
```

### Restore from Snapshot

```bash
# Read snapshot
cat .ai-workspace/context_history/20251216_1430_implementing_auth_service.md

# Tell Claude
"Restore context from 20251216_1430_implementing_auth_service"
```

### List Snapshots

```bash
# Recent snapshots
ls -lt .ai-workspace/context_history/*.md | head -10

# All snapshots
ls -1 .ai-workspace/context_history/*.md
```

## Archival Policy

**Default Retention**: 30 days

**After 30 days**: Snapshots can be manually archived or deleted

**Configuration**: `.ai-workspace/config/workspace_config.yml`
```yaml
context_snapshots:
  retention_days: 30           # Days before archival
```

## Snapshot Properties

### Immutability
- Snapshots are **append-only** - never modified after creation
- Files may be set to read-only (platform-dependent)
- Preserves historical accuracy

### Human-Readable
- Markdown format for easy inspection
- Clear section headers and formatting
- No special tools needed to read

### Self-Contained
- Each snapshot includes all information needed for recovery
- No dependencies on external files (except ACTIVE_TASKS.md reference)
- Can be shared with team members

## Integration

### With /aisdlc-checkpoint-tasks
```
/aisdlc-checkpoint-tasks
    ↓ (updates)
ACTIVE_TASKS.md
    ↓ (reads)
/aisdlc-snapshot-context
    ↓ (creates)
{YYYYMMDD}_{HHMM}_{label}.md
```

**Recommended**: Run checkpoint BEFORE snapshot for accurate task status

### With Version Control
- Add `.ai-workspace/context_history/` to `.gitignore` (optional)
- Snapshots are local, personal context
- Share via secure channels for team handoffs

## Use Cases

1. **End of Day Save**
   - Checkpoint tasks
   - Create snapshot
   - Safe to close session

2. **Team Handoff**
   - Create snapshot before handoff
   - Share snapshot file with team member
   - They restore context in new session

3. **Context Loss Recovery**
   - Conversation history cleared
   - Read most recent snapshot
   - Tell Claude to restore context

4. **Weekly Milestone**
   - Create snapshot at end of week
   - Documents weekly progress
   - Audit trail of project evolution

5. **Before Risky Changes**
   - Snapshot before major refactor
   - Recovery point if things go wrong
   - Can compare before/after state

## Troubleshooting

### Snapshot Creation Fails

```bash
# Check workspace initialized
/aisdlc-init

# Verify directory exists
ls -la .ai-workspace/context_history/

# Check write permissions
ls -ld .ai-workspace/context_history/
```

### Cannot Find Snapshot

```bash
# Search by date
ls -1 .ai-workspace/context_history/*.md | grep 20251216

# Search by label
ls -1 .ai-workspace/context_history/*.md | grep auth
```

## Reference

**Requirement**: REQ-TOOL-012.0.1.0 - Context Snapshot and Recovery
**Design**: `docs/design/claude_aisdlc/CONTEXT_SNAPSHOT_DESIGN.md`
**Command**: `claude-code/.claude-plugin/plugins/aisdlc-methodology/commands/aisdlc-snapshot-context.md`
**Template**: `.ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md`

---

**"Excellence or nothing"**
