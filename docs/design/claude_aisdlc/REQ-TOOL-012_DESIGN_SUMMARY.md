# REQ-TOOL-012 Design Summary - Context Snapshot and Recovery

**Requirement**: REQ-TOOL-012.0.1.0
**Solution**: claude_aisdlc
**Status**: Design Complete
**Date**: 2025-12-16

---

## Quick Reference

| Aspect | Details |
|--------|---------|
| **Command** | `/aisdlc-snapshot-context` |
| **Storage** | `.ai-workspace/context_history/` |
| **Format** | `{YYYYMMDD}_{HHMM}_{label}.md` |
| **Archival** | 30 days (configurable) |
| **Integration** | Works with `/aisdlc-checkpoint-tasks` |
| **Template** | `.ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md` |

---

## Design Deliverables

### 1. Complete Design Document
**File**: `CONTEXT_SNAPSHOT_DESIGN.md` (11 sections, ~1,200 lines)

**Contents**:
1. Overview (purpose, traceability, principles)
2. Architecture (directory structure, components, data flow)
3. Snapshot Template Design (structure, variables)
4. Command Specification (behavior, phases, output)
5. Archival Design (policy, process, configuration)
6. Usage Examples (basic, recovery, handoff)
7. Implementation Considerations (platform, performance, security)
8. Testing Strategy (unit, integration, manual)
9. Documentation Requirements
10. Acceptance Criteria Validation
11. References

**Key Sections**:
- Section 2: Architecture with detailed data flow diagrams
- Section 3: Complete snapshot template with all variables
- Section 4: 5-phase command behavior specification
- Section 5: Archival policy with 30-day retention
- Section 8: BDD scenarios for testing

### 2. Snapshot Template
**File**: `.ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md`

**Template Variables** (27 total):
- Metadata: timestamp, snapshot ID, project name, git branch
- Tasks: counts by status, task tables (in-progress, pending, blocked)
- Work Context: current work, activities, next steps
- Conversation: decisions, questions, blockers, command history
- Files: modified, staged, untracked, git status
- Metadata: previous/next snapshots, metrics, retention policy
- Related: finished tasks, solution name, work summary

**Format**: Human-readable Markdown with clear sections for recovery

### 3. Command Specification
**File**: `claude-code/.claude-plugin/plugins/aisdlc-methodology/commands/aisdlc-snapshot-context.md`

**Command Behavior** (5 phases):
1. **Validation**: Check workspace, create directories, verify template
2. **Context Gathering**: Read tasks, analyze conversation, run git, collect metadata
3. **Snapshot Generation**: Load template, substitute variables, handle missing data
4. **Persistence**: Write snapshot, set permissions, update index
5. **Reporting**: Display success message with recovery instructions

**Error Handling**: 6 error conditions with graceful degradation
**Integration**: Works with `/aisdlc-checkpoint-tasks` for complete session save

### 4. Integration Diagram
**File**: `CONTEXT_SNAPSHOT_INTEGRATION_DIAGRAM.md`

**Diagrams Include**:
- Work session flow (start → checkpoint → snapshot → end)
- Data flow between commands (checkpoint updates tasks → snapshot reads tasks)
- Directory structure integration (new context_history/ directory)
- Command interaction matrix (reads/writes for each command)
- Workflow examples (end-of-day save, morning recovery, team handoff)
- Archival process flow (create → retain → archive after 30 days)
- Error handling integration (graceful degradation)
- Performance considerations (2-5s typical, 10s max)
- Security considerations (sanitization, permissions, git ignore)

### 5. Main Design Updates
**File**: `AISDLC_IMPLEMENTATION_DESIGN.md`

**Updates Made**:
- Added "Context Snapshot" row to Component Overview table (Section 1.2)
- Updated Command System from 8 to 9 commands (Section 2.4)
- Added `/aisdlc-snapshot-context` to command list
- Updated Workspace System with context_history/ directory (Section 2.5)
- Added CONTEXT_SNAPSHOT_TEMPLATE.md to templates list
- Added REQ-TOOL-012 to requirements coverage

---

## Directory Structure

### New Directories Created
```
.ai-workspace/
├── context_history/              # NEW (REQ-TOOL-012)
│   ├── {YYYYMMDD}_{HHMM}_{label}.md  # Context snapshots
│   └── README.md                 # Directory documentation
└── templates/
    └── CONTEXT_SNAPSHOT_TEMPLATE.md  # NEW
```

### Template File Created
**File**: `.ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md`
- 27 template variables
- 10 major sections (tasks, work, conversation, files, recovery, metadata, related)
- Human-readable recovery guidance
- Archival notice

### Command File Created
**File**: `claude-code/.claude-plugin/plugins/aisdlc-methodology/commands/aisdlc-snapshot-context.md`
- 5-phase execution flow
- 27 variable substitution rules
- 6 error conditions
- Integration with checkpoint command
- 3 usage examples
- Filename format: `{YYYYMMDD}_{HHMM}_{label}.md` (follows finished task convention)

---

## Snapshot Content

### What's Captured
✅ **Active Tasks Summary** - Count and status of all active tasks
✅ **Current Work Context** - What developer is working on right now
✅ **Recent Activities** - What was done in current session
✅ **Key Decisions** - Architectural/design decisions made
✅ **Open Questions** - Unresolved questions from conversation
✅ **Blockers/Issues** - Things preventing progress
✅ **File Changes** - Modified, staged, untracked files from git
✅ **Next Steps** - Planned work from conversation
✅ **Recovery Guidance** - How to restore this context
✅ **Metadata** - Timestamps, metrics, related snapshots

### What's NOT Captured
❌ **Full conversation replay** - Only key markers (decisions, questions, blockers)
❌ **File contents** - Only file paths and change types
❌ **Sensitive data** - API keys, tokens, passwords sanitized
❌ **Complete git history** - Only last 5 commits
❌ **Binary data** - Text-based markdown only

### Data Sources
1. **ACTIVE_TASKS.md** - Task status, titles, REQ tags
2. **Conversation history** - Recent 20-50 messages for context
3. **git status** - Modified/staged/untracked files
4. **git branch** - Current branch name
5. **git log** - Recent commits (last 5)
6. **finished/*.md** - Recently completed tasks
7. **Workspace config** - Project name, retention settings

---

## Command Workflow

### Basic Usage
```bash
# End of work session
/aisdlc-checkpoint-tasks      # Update task status
/aisdlc-snapshot-context      # Capture full context

# Next session
"Restore context from 20251216_1430_implementing_auth_service"
```

### Output Format
```
╔══════════════════════════════════════════════════════════════╗
║             Context Snapshot Created Successfully            ║
╚══════════════════════════════════════════════════════════════╝

📸 Snapshot: 20251216_1430_implementing_auth_service
📁 Location: .ai-workspace/context_history/20251216_1430_implementing_auth_service.md

📊 Snapshot Contents:
   ✓ Active Tasks: 3 (2 in-progress, 1 pending)
   ✓ File Changes: 5 modified, 1 staged
   ✓ Conversation Markers: 2 decisions, 1 open question
   ✓ Recovery Guidance: Included

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 To restore this context later:
   Read: cat .ai-workspace/context_history/20251216_1430_implementing_auth_service.md
   Then: "Restore context from 20251216_1430_implementing_auth_service"

📋 Total Snapshots: 8
```

---

## Integration Points

### With /aisdlc-checkpoint-tasks
**Relationship**: Complementary
- Checkpoint updates task status → Snapshot reads updated status
- Checkpoint creates finished docs → Snapshot references recent finished
- Recommended: Run checkpoint BEFORE snapshot

**Data Flow**:
```
/aisdlc-checkpoint-tasks
    ↓ (writes)
ACTIVE_TASKS.md
    ↓ (reads)
/aisdlc-snapshot-context
    ↓ (creates)
{YYYYMMDD}_{HHMM}_{label}.md (includes task status)
```

### With /aisdlc-status
**Relationship**: Discovery
- Status can suggest creating snapshot (e.g., "Before ending session, run /aisdlc-snapshot-context")
- Status can suggest restoring from snapshot (e.g., "Detected context loss, restore from snapshot-{timestamp}")

### With Workspace System
**Relationship**: Storage
- Snapshots stored in `.ai-workspace/context_history/`
- Template loaded from `.ai-workspace/templates/`
- Workspace config provides retention settings

---

## Archival Policy

### Default Settings
- **Retention**: 30 days in active snapshots
- **Archive Location**: `.ai-workspace/context_history/archive/{YYYY-MM}/`
- **Trigger**: Manual command or automatic (future)
- **Organization**: Year-month subdirectories

### Configuration
**File**: `.ai-workspace/config/workspace_config.yml`
```yaml
context_snapshots:
  retention_days: 30           # Days before archival
  archive_enabled: true        # Enable automatic archival
  max_active_snapshots: 50     # Max in snapshots/ before force archive
  archive_location: ".ai-workspace/context_history/archive"
```

### Archival Process
1. Snapshot created in `context_history/`
2. After 30 days: Developer can manually archive or delete
3. No automatic archival implemented in initial version

---

## Testing Strategy

### Unit Tests
- Snapshot filename format validation
- Template variable substitution
- Directory creation
- File writing and permissions
- Graceful handling of missing files

### Integration Tests (BDD)
```gherkin
Feature: Context Snapshot and Recovery
  Scenario: Create basic snapshot
    Given I have an initialized workspace
    And I have active tasks in ACTIVE_TASKS.md
    When I run /aisdlc-snapshot-context
    Then a snapshot file is created
    And the filename matches pattern {YYYYMMDD}_{HHMM}_{label}.md
    And the snapshot contains all required sections

  Scenario: Restore context from snapshot
    Given I have a snapshot file
    And I have lost conversation history
    When I ask Claude to restore from snapshot
    Then Claude summarizes the snapshot contents
    And Claude suggests next steps
```

### Manual Testing Checklist
- [ ] Create snapshot in empty workspace
- [ ] Create snapshot with active tasks
- [ ] Create snapshot with git changes
- [ ] Create snapshot without git available
- [ ] Restore context (manually read and tell Claude)
- [ ] Create 10 snapshots, verify chronological listing
- [ ] Verify snapshot is human-readable
- [ ] Test team handoff scenario

---

## Acceptance Criteria Validation

| Requirement | Design Element | Status |
|-------------|---------------|--------|
| Command available: `/aisdlc-snapshot-context` | Command spec file created | ✅ Complete |
| Snapshots stored in `.ai-workspace/context_history/` | Directory structure defined | ✅ Complete |
| Snapshot includes: timestamp, tasks, work context, conversation markers | Template with all sections | ✅ Complete |
| Snapshots are immutable (append-only) | Read-only permissions after creation | ✅ Complete |
| Filename format: `{YYYYMMDD}_{HHMM}_{label}.md` | Filename generation spec | ✅ Complete |
| Recovery guidance included | Recovery section in template | ✅ Complete |
| Integrates with `/aisdlc-checkpoint-tasks` | Integration workflow defined | ✅ Complete |
| Archival after 30 days | Archival policy defined | ✅ Complete |

**ALL ACCEPTANCE CRITERIA MET** ✅

---

## Performance Targets

| Operation | Typical | Max | Notes |
|-----------|---------|-----|-------|
| Context gathering | 1-3s | 5s | Limited to recent messages |
| Snapshot generation | 1-2s | 3s | Template rendering |
| File writing | <100ms | 500ms | Small file (~20-50 KB) |
| **Total** | **2-5s** | **10s** | Acceptable for end-of-session |

**Optimization**:
- Limit conversation analysis to last 20-50 messages
- Parallel execution (git, file reads)
- Template caching

---

## Security Considerations

### Data Sanitization
- Pattern matching to detect/remove API keys, tokens, passwords
- Sanitize conversation markers for obvious secrets
- File paths only (no content)

### File Permissions
- Set snapshots to read-only after creation (platform-permitting)
- Prevent accidental modification

### Git Ignore
- Recommend adding `.ai-workspace/context_history/` to `.gitignore`
- Prevents accidental commit to public repos

### Team Handoff
- Share snapshots via secure channels
- Not via public chat, email

---

## Next Steps

### Implementation Phase
1. **Create directories**: Implement directory creation in `/aisdlc-init` command
2. **Implement command**: Create `/aisdlc-snapshot-context` command logic
3. **Template rendering**: Implement variable substitution engine
4. **Conversation analysis**: Implement conversation parsing logic
5. **Testing**: Write unit and integration tests

### Future Enhancements
1. **Snapshot search**: Search by keyword, date, task ID
2. **Snapshot diff**: Compare two snapshots
3. **One-command restore**: Automatic context restoration (vs. manual reading)
4. **Snapshot export**: PDF, HTML for sharing
5. **Auto-snapshot**: Automatic snapshots at intervals or on events
6. **Snapshot compression**: Compress archived snapshots
7. **Snapshot tagging**: Tag snapshots (milestone, release, handoff)

---

## References

### Design Documents
- [CONTEXT_SNAPSHOT_DESIGN.md](CONTEXT_SNAPSHOT_DESIGN.md) - Complete design (11 sections)
- [CONTEXT_SNAPSHOT_INTEGRATION_DIAGRAM.md](CONTEXT_SNAPSHOT_INTEGRATION_DIAGRAM.md) - Integration diagrams
- [AISDLC_IMPLEMENTATION_DESIGN.md](AISDLC_IMPLEMENTATION_DESIGN.md) - Main design (updated)

### Requirements
- [REQ-TOOL-012.0.1.0](../../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md#req-tool-012010-context-snapshot-and-recovery)

### Related Requirements
- REQ-TOOL-002 - Developer Workspace
- REQ-TOOL-003 - Workflow Commands

### Template and Command Files
- `.ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md` - Snapshot template
- `claude-code/.claude-plugin/plugins/aisdlc-methodology/commands/aisdlc-snapshot-context.md` - Command spec

---

## Summary

**Design Status**: ✅ Complete

**Deliverables Created**:
1. Complete design document (CONTEXT_SNAPSHOT_DESIGN.md - 11 sections)
2. Snapshot template (CONTEXT_SNAPSHOT_TEMPLATE.md - 27 variables)
3. Command specification (aisdlc-snapshot-context.md - 5 phases)
4. Integration diagram (CONTEXT_SNAPSHOT_INTEGRATION_DIAGRAM.md)
5. Main design updates (AISDLC_IMPLEMENTATION_DESIGN.md)
6. This summary document

**All Acceptance Criteria Met**: ✅ 8/8

**Ready for**: Implementation phase (Code stage)

**Estimated Implementation Effort**:
- Command logic: 4-6 hours
- Template rendering: 2-3 hours
- Conversation analysis: 3-4 hours
- Testing: 3-4 hours
- Total: 12-17 hours

---

**Document Status**: Complete (v1.0)
**Last Updated**: 2025-12-16

---

**"Excellence or nothing"**
