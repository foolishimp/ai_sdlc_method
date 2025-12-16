# Context Snapshot and Recovery Design

**Document Type**: Design Document
**Requirement**: REQ-TOOL-012.0.1.0
**Solution**: claude_aisdlc
**Version**: 1.0
**Date**: 2025-12-16
**Status**: Draft

---

## 1. Overview

### 1.1 Purpose

This design document specifies the Context Snapshot and Recovery feature, which enables developers to capture and restore session state across interruptions, facilitating:
- Session continuity after conversation history loss
- Team member handoffs with full context
- Recovery points for complex work sessions
- Historical audit trail of project evolution

### 1.2 Requirement Traceability

**Implements**: REQ-TOOL-012.0.1.0 (Context Snapshot and Recovery)
**Depends On**:
- REQ-TOOL-002 (Developer Workspace)
- REQ-TOOL-003 (Workflow Commands)

**Integrates With**:
- `/aisdlc-checkpoint-tasks` - Task state management
- `.ai-workspace/tasks/active/ACTIVE_TASKS.md` - Active tasks
- Conversation history (platform-provided)

### 1.3 Design Principles

1. **Immutability** - Snapshots are append-only, never modified after creation
2. **Self-Contained** - Each snapshot includes all information needed for recovery
3. **Human-Readable** - Markdown format for easy inspection and sharing
4. **Lightweight** - Focus on essential context, not full conversation replay
5. **Integration-First** - Complements existing checkpoint mechanism

---

## 2. Architecture

### 2.1 Directory Structure

```
.ai-workspace/
├── context_history/              # Snapshot storage
│   ├── {YYYYMMDD}_{HHMM}_{label}.md  # Context snapshots
│   └── README.md                 # Directory documentation
├── tasks/
│   └── active/
│       └── ACTIVE_TASKS.md       # Referenced by snapshots
└── templates/
    └── CONTEXT_SNAPSHOT_TEMPLATE.md  # Template for snapshots
```

**Design Rationale**:
- Flat directory for simplicity
- Filename format follows finished task convention for consistency
- Label derived from current work focus
- README.md provides usage documentation
- Template ensures consistency across snapshots

### 2.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    /aisdlc-snapshot-context                     │
│                         (Command)                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Snapshot Generator                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Phase 1: Gather Context                                 │   │
│  │  ├─ Read ACTIVE_TASKS.md                                 │   │
│  │  ├─ Analyze conversation history (last N messages)       │   │
│  │  ├─ Check git status                                     │   │
│  │  └─ Identify recent file modifications                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Phase 2: Synthesize Snapshot                            │   │
│  │  ├─ Summarize active tasks (from ACTIVE_TASKS.md)        │   │
│  │  ├─ Extract work context (what's being worked on)        │   │
│  │  ├─ Capture conversation markers (decision points)       │   │
│  │  └─ Generate recovery guidance                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Phase 3: Persist Snapshot                               │   │
│  │  ├─ Generate timestamp-based filename                    │   │
│  │  ├─ Apply template                                       │   │
│  │  ├─ Write to .ai-workspace/context_history/snapshots/    │   │
│  │  └─ Update index (if enabled)                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Snapshot File (Immutable)                          │
│  ├─ Timestamp & Metadata                                        │
│  ├─ Active Tasks Summary                                        │
│  ├─ Current Work Context                                        │
│  ├─ Conversation State Markers                                  │
│  ├─ Recovery Guidance                                           │
│  └─ Related Files & Commands                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Data Flow

```
User triggers:
  /aisdlc-snapshot-context
         ↓
Command reads:
  - .ai-workspace/tasks/active/ACTIVE_TASKS.md
  - Conversation history (platform API)
  - git status (modified files, branch)
  - .ai-workspace/context_history/snapshots/ (count)
         ↓
Command synthesizes:
  - Task summary (N in-progress, M pending, P blocked)
  - Work context (what's being worked on now)
  - Conversation markers (recent decisions/questions)
  - File changes (uncommitted work)
         ↓
Command generates:
  - Timestamp: YYYY-MM-DD-HH-MM-SS
  - Filename: snapshot-{timestamp}.md
  - Content: Template-based markdown
         ↓
Command writes:
  .ai-workspace/context_history/snapshots/snapshot-{timestamp}.md
         ↓
Command reports:
  "✅ Context snapshot created: snapshot-{timestamp}.md"
  "   Contains: X tasks, Y file changes, Z conversation markers"
  "   Recovery: Read this file to restore context"
```

---

## 3. Snapshot Template Design

### 3.1 Template Structure

```markdown
# Context Snapshot - {TIMESTAMP}

**Created**: {YYYY-MM-DD HH:MM:SS}
**Snapshot**: {YYYYMMDD}_{HHMM}_{label}
**Project**: {project_name from workspace}
**Branch**: {git branch}

---

## 🎯 Active Tasks Summary

**Total Active**: {count}
- In Progress: {count}
- Pending: {count}
- Blocked: {count}

### Tasks In Progress
{task_id} | {task_title} | REQ-{tags}
...

### Tasks Pending
{task_id} | {task_title} | REQ-{tags}
...

### Tasks Blocked
{task_id} | {task_title} | REQ-{tags} | Blocker: {reason}
...

**Source**: `.ai-workspace/tasks/active/ACTIVE_TASKS.md`

---

## 💼 Current Work Context

**What I'm Working On**:
{brief description of current focus - extracted from conversation}

**Recent Activities**:
- {activity 1 - e.g., "Implemented user authentication"}
- {activity 2 - e.g., "Fixed failing tests in auth_service_test.py"}
- {activity 3 - e.g., "Refactored error handling"}

**Next Steps Planned**:
- {next step 1}
- {next step 2}

---

## 🗣️ Conversation State Markers

**Key Decisions Made**:
1. {decision 1 - e.g., "Use JWT tokens instead of sessions"}
2. {decision 2 - e.g., "Move validation to middleware layer"}

**Open Questions**:
1. {question 1 - e.g., "Should we add rate limiting now or later?"}
2. {question 2 - e.g., "Which error format for API responses?"}

**Blockers/Issues**:
- {blocker 1 - e.g., "Waiting on design approval for error handling"}
- {blocker 2 - e.g., "Database migration pending"}

**Recent Command History**:
```
{last 5-10 commands run, if available}
```

---

## 📁 File Changes

**Modified Files** (uncommitted):
- `{file_path}` - {brief description}
- `{file_path}` - {brief description}

**Staged Files**:
- `{file_path}`

**Untracked Files**:
- `{file_path}`

**Git Status**:
```
{output of git status}
```

---

## 🔄 Recovery Guidance

### How to Restore This Context

1. **Review This Snapshot**:
   - Read all sections above to understand where you were
   - Pay special attention to "Current Work Context" and "Open Questions"

2. **Restore Active Tasks**:
   ```bash
   # Active tasks are still in ACTIVE_TASKS.md
   cat .ai-workspace/tasks/active/ACTIVE_TASKS.md
   ```

3. **Check Git State**:
   ```bash
   git status
   git log --oneline -n 10
   ```

4. **Resume Work**:
   - If task was in progress: Continue from "Next Steps Planned"
   - If blocked: Address blockers first
   - If starting new task: Run `/aisdlc-status` to see next action

5. **Tell Claude**:
   > "I'm resuming work from snapshot {snapshot_id}. The snapshot shows I was
   > working on {work_context}. {Open questions or next steps}."

### Quick Commands to Regain Context

```bash
# See current project status
/aisdlc-status

# Review active tasks
cat .ai-workspace/tasks/active/ACTIVE_TASKS.md

# See recent finished work
ls -lt .ai-workspace/tasks/finished/ | head -5

# Check for more snapshots
ls -lt .ai-workspace/context_history/snapshots/
```

---

## 📊 Metadata

**Snapshot Version**: 1.0
**Template**: `.ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md`
**Related Snapshots**:
- Previous: {previous_snapshot_id or "None"}
- Next: {next_snapshot_id or "None (latest)"}

**Conversation Metrics**:
- Messages in current session: {count}
- Estimated session duration: {duration}
- Commands run: {count}

**Statistics**:
- Files modified: {count}
- Tests run: {count passed/failed}
- Commits since last snapshot: {count}

---

## 🔗 Related Files

**Essential Reading**:
- `.ai-workspace/tasks/active/ACTIVE_TASKS.md` - Current tasks
- `docs/requirements/INTENT.md` - Original intent
- `docs/design/{solution}/AISDLC_IMPLEMENTATION_DESIGN.md` - Design

**Recent Finished Tasks**:
- `.ai-workspace/tasks/finished/{recent_task_1}.md`
- `.ai-workspace/tasks/finished/{recent_task_2}.md`

---

**END OF SNAPSHOT**

---

## Archive Notice

This snapshot will be automatically archived after 30 days to:
`.ai-workspace/context_history/archive/{YYYY-MM}/`

To prevent archival, copy to another location or update archival policy in
`.ai-workspace/config/workspace_config.yml`.
```

### 3.2 Template Variables

| Variable | Source | Example |
|----------|--------|---------|
| `{TIMESTAMP}` | Current time | `2025-12-16 14:30:45` |
| `{YYYY-MM-DD}` | Current date | `2025-12-16` |
| `{HH-MM-SS}` | Current time | `14-30-45` |
| `{project_name}` | Workspace config | `ai_sdlc_method` |
| `{git branch}` | `git branch --show-current` | `main` |
| `{task_id}` | ACTIVE_TASKS.md | `#42` |
| `{task_title}` | ACTIVE_TASKS.md | `Implement authentication` |
| `{REQ-tags}` | ACTIVE_TASKS.md | `REQ-F-AUTH-001, REQ-NFR-SEC-002` |
| `{work_context}` | Conversation analysis | `Implementing user login flow` |
| `{activity}` | Conversation analysis | `Fixed failing tests` |
| `{decision}` | Conversation analysis | `Use JWT tokens` |
| `{question}` | Conversation analysis | `Add rate limiting?` |
| `{file_path}` | `git status` | `src/auth/auth_service.py` |
| `{previous_snapshot_id}` | Last snapshot in directory | `20251215_1030_fixing_payment_tests` |

---

## 4. Command Specification

### 4.1 Command Definition

**Command**: `/aisdlc-snapshot-context`

**Location**: `claude-code/.claude-plugin/plugins/aisdlc-methodology/commands/aisdlc-snapshot-context.md`

**Implements**: REQ-TOOL-012.0.1.0

**Purpose**: Capture current session context into an immutable snapshot for recovery and continuity.

### 4.2 Command Behavior

**Phase 1: Validation**
1. Check `.ai-workspace/` exists
   - If NOT: Error: "Workspace not initialized. Run /aisdlc-init first."
2. Check `.ai-workspace/context_history/snapshots/` exists
   - If NOT: Create directory (and archive subdirectory)
3. Check template exists
   - Path: `.ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md`
   - If NOT: Use built-in template

**Phase 2: Context Gathering**
1. Read `.ai-workspace/tasks/active/ACTIVE_TASKS.md`
   - Parse tasks by status (in_progress, pending, blocked)
   - Extract task IDs, titles, REQ tags
2. Analyze conversation history (last 20-50 messages)
   - Extract work activities (what was done)
   - Identify decisions made (architectural choices)
   - Capture open questions (unresolved items)
   - Note blockers mentioned
3. Run `git status` and `git branch --show-current`
   - Get modified/staged/untracked files
   - Get current branch
4. Read workspace config
   - Get project name
   - Get archival settings (retention period)
5. List existing snapshots
   - Find previous snapshot (chronologically)
   - Count total snapshots

**Phase 3: Snapshot Generation**
1. Generate timestamp: `YYYYMMDD_HHMM`
2. Derive label from current work focus (snake_case, max 50 chars, default: `context_snapshot`)
3. Generate filename: `{YYYYMMDD}_{HHMM}_{label}.md`
4. Load template (`.ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md`)
4. Substitute template variables with gathered context
5. Add computed sections:
   - Active Tasks Summary (from ACTIVE_TASKS.md)
   - Current Work Context (from conversation analysis)
   - Conversation State Markers (decisions, questions, blockers)
   - File Changes (from git status)
   - Recovery Guidance (standardized instructions)
   - Metadata (snapshot version, timestamps, counts)

**Phase 4: Persistence**
1. Write snapshot to `.ai-workspace/context_history/{YYYYMMDD}_{HHMM}_{label}.md`
2. Set file permissions to read-only (optional, platform-dependent)

**Phase 5: Reporting**
1. Display success message with snapshot details
2. Suggest recovery command

### 4.3 Command Output Format

```
╔══════════════════════════════════════════════════════════════╗
║             Context Snapshot Created Successfully            ║
╚══════════════════════════════════════════════════════════════╝

📸 Snapshot: 20251216_1430_implementing_auth_service
📁 Location: .ai-workspace/context_history/20251216_1430_implementing_auth_service.md

📊 Snapshot Contents:
   ✓ Active Tasks: 5 (3 in-progress, 2 pending)
   ✓ File Changes: 8 modified, 2 staged
   ✓ Conversation Markers: 4 decisions, 2 open questions
   ✓ Recovery Guidance: Included

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 To restore this context later:

   1. Read the snapshot:
      cat .ai-workspace/context_history/20251216_1430_implementing_auth_service.md

   2. Tell Claude:
      "Restore context from 20251216_1430_implementing_auth_service"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Total Snapshots: 12
```

### 4.4 Error Handling

| Error Condition | Message | Action |
|----------------|---------|--------|
| Workspace not initialized | "❌ Error: Workspace not initialized. Run /aisdlc-init first." | Exit |
| Cannot create directory | "❌ Error: Cannot create context_history directory: {reason}" | Exit |
| Cannot write snapshot | "❌ Error: Cannot write snapshot: {reason}" | Exit |
| Template missing | "⚠️  Warning: Template not found, using built-in template" | Continue |
| Git not available | "⚠️  Warning: Git not available, skipping file change detection" | Continue |
| ACTIVE_TASKS.md missing | "⚠️  Warning: ACTIVE_TASKS.md not found, snapshot will have no task data" | Continue |

### 4.5 Integration with /aisdlc-checkpoint-tasks

**Relationship**:
- `/aisdlc-checkpoint-tasks` - Updates task status, creates finished task docs
- `/aisdlc-snapshot-context` - Captures broader session context beyond tasks

**Recommended Workflow**:
```
Work Session
     ↓
/aisdlc-checkpoint-tasks  (Update task status)
     ↓
/aisdlc-snapshot-context  (Capture full context)
     ↓
End Session
```

**Optional: Combined Command**:
Future enhancement could add `/aisdlc-save-session` that runs both:
1. Run `/aisdlc-checkpoint-tasks` to update tasks
2. Run `/aisdlc-snapshot-context` to capture context
3. Report combined results

---

## 5. Archival Design

### 5.1 Archival Policy

**Default Retention**: 30 days
**Archival Trigger**: Manual (developer decision)
**Note**: No automatic archival in initial version

### 5.2 Archival Process

**Manual Archival**:
Developers can manually manage old snapshots:
- Delete snapshots older than 30 days
- Move to personal archive location
- Keep indefinitely if needed

**Future Enhancement**:
Automatic archival could be added in future versions

### 5.3 Archival Configuration

**Workspace Config** (`.ai-workspace/config/workspace_config.yml`):
```yaml
context_snapshots:
  retention_days: 30           # Recommended retention period
```

---

## 6. Usage Examples

### 6.1 Basic Snapshot

**Scenario**: Developer finishing work session, wants to save context

```
User: /aisdlc-snapshot-context

Claude:
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
   Then tell Claude: "Restore context from 20251216_1430_implementing_auth_service"

📋 Total Snapshots: 8
```

### 6.2 Context Recovery

**Scenario**: Developer returns after interruption, lost conversation history

```
User: Restore context from 20251216_1430_implementing_auth_service

Claude: [Reads .ai-workspace/context_history/20251216_1430_implementing_auth_service.md]

✅ Context restored from 20251216_1430_implementing_auth_service

📋 Session Summary (from snapshot):
   - Date: 2025-12-16 14:30:45
   - Branch: feature/auth-service
   - Tasks: 3 active (2 in-progress, 1 pending)

🎯 You were working on:
   - Task #42: Implement user authentication (REQ-F-AUTH-001)
   - Status: In Progress
   - Recent: Fixed failing tests in auth_service_test.py

💬 Open Questions (from snapshot):
   1. Should we add rate limiting now or in next sprint?
   2. Which error format for API responses?

📁 Uncommitted Work:
   - src/auth/auth_service.py (modified)
   - tests/auth/test_auth_service.py (modified)

🔄 Next Steps (from snapshot):
   1. Complete refactoring of error handling
   2. Add integration tests for login flow
   3. Update API documentation

Ready to continue? I can help with any of the next steps or answer the open questions.
```

### 6.3 Team Handoff

**Scenario**: Developer A hands off work to Developer B

**Developer A** (end of day):
```
Developer A: /aisdlc-checkpoint-tasks
             /aisdlc-snapshot-context
             [Sends 20251216_1700_implementing_auth_service.md to Developer B]
```

**Developer B** (next morning):
```
Developer B: I'm taking over from Developer A. Here's the snapshot they left:
             [Shares 20251216_1700_implementing_auth_service.md content]

Claude: ✅ Context loaded from handoff snapshot

📋 Previous Developer Context:
   - Left off: Implementing authentication service
   - Completed: User login endpoint, basic tests
   - In Progress: Error handling refactor
   - Blocked: Waiting for design review on rate limiting

🎯 Where to Resume:
   1. Review uncommitted changes in src/auth/auth_service.py
   2. Complete error handling refactor (80% done)
   3. Address open question: "Which error format?" (2 options in snapshot)

💡 Suggested First Step:
   Review the design decision about error format (mentioned in snapshot),
   then continue the refactor. Ready to proceed?
```

### 6.4 Combined with Checkpoint

**Scenario**: Developer uses both commands together

```
User: /aisdlc-checkpoint-tasks

Claude:
╔══════════════════════════════════════════════════════════════╗
║              Task Checkpoint - 2025-12-16 16:45              ║
╚══════════════════════════════════════════════════════════════╝

📊 Evaluation Summary:
   ✅ Completed: 2 task(s)
   🔄 In Progress: 1 task(s)
   ⏸️  Not Started: 2 task(s)

✅ Completed Tasks:
   #41: Fix authentication timeout (REQ-F-AUTH-001)
        → Archived to .ai-workspace/tasks/finished/20251216_1645_fix_auth_timeout.md
   #43: Update API documentation (REQ-DES-002)
        → Archived to .ai-workspace/tasks/finished/20251216_1645_update_api_docs.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💾 Files Updated:
   - .ai-workspace/tasks/active/ACTIVE_TASKS.md
   - .ai-workspace/tasks/finished/20251216_1645_fix_auth_timeout.md
   - .ai-workspace/tasks/finished/20251216_1645_update_api_docs.md

User: /aisdlc-snapshot-context

Claude:
╔══════════════════════════════════════════════════════════════╗
║             Context Snapshot Created Successfully            ║
╚══════════════════════════════════════════════════════════════╝

📸 Snapshot: 20251216_1645_user_login_complete
📁 Location: .ai-workspace/context_history/20251216_1645_user_login_complete.md

📊 Snapshot Contents:
   ✓ Active Tasks: 3 (1 in-progress, 2 pending)
   ✓ File Changes: 0 (clean working directory)
   ✓ Conversation Markers: Just checkpointed 2 completed tasks
   ✓ Recovery Guidance: Included

✅ Session saved! You can safely close and resume later using this snapshot.
```

---

## 7. Implementation Considerations

### 7.1 Platform Integration

**Claude Code Specific**:
- Use native file I/O (Read/Write tools)
- Leverage conversation history API (if available)
- Use Bash tool for git commands
- Markdown format for readability

**Cross-Platform Considerations**:
- Conversation history API may vary by platform
- File system access may have restrictions
- Template paths may need platform-specific resolution

### 7.2 Performance

**Optimization Strategies**:
1. **Lazy Conversation Analysis**: Only analyze recent messages (last 20-50), not entire history
2. **Incremental Index**: Update `.snapshot_index.yml` incrementally, not rebuild
3. **Snapshot Limit**: Archive old snapshots to keep active directory small (<50 files)
4. **Template Caching**: Load template once, reuse for multiple snapshots

**Performance Targets**:
- Snapshot generation: < 5 seconds (typical)
- Snapshot generation: < 10 seconds (with large conversation history)
- Snapshot file size: < 50 KB (typical)

### 7.3 Security and Privacy

**Security Considerations**:
1. **No Sensitive Data**: Snapshots are human-readable - avoid capturing secrets, API keys, passwords
2. **File Permissions**: Set snapshots to read-only after creation (platform-permitting)
3. **Git Ignore**: Recommend adding `.ai-workspace/context_history/` to `.gitignore` (optional)
4. **Sanitization**: Scrub conversation markers for obvious secrets (API keys, tokens)

**Privacy Considerations**:
- Snapshots may contain team member names, decisions, questions
- Snapshots should not be committed to public repositories by default
- Team handoff snapshots should be shared via secure channels

### 7.4 Extensibility

**Future Enhancements**:
1. **Snapshot Search**: Search snapshots by keyword, date range, task ID
2. **Snapshot Diff**: Compare two snapshots to see what changed
3. **Snapshot Restore**: One-command restoration (vs. manual reading)
4. **Snapshot Export**: Export to PDF, HTML for sharing
5. **Snapshot Compression**: Compress archived snapshots to save space
6. **Snapshot Tagging**: Tag snapshots (milestone, release, handoff)
7. **Snapshot Metrics**: Track snapshot usage, recovery success rate
8. **Auto-Snapshot**: Automatic snapshots at configurable intervals or on certain events

---

## 8. Testing Strategy

### 8.1 Unit Testing

**Test Coverage**:
1. **Template Rendering**: Ensure all variables substituted correctly
2. **Timestamp Generation**: Verify format `YYYY-MM-DD-HH-MM-SS`
3. **Filename Generation**: Verify format `snapshot-{timestamp}.md`
4. **Directory Creation**: Ensure directories created if missing
5. **File Writing**: Verify snapshot written to correct location
6. **Immutability**: Verify file not modified after creation (if permissions set)

**Test Cases**:
```python
def test_snapshot_filename_format():
    """Verify snapshot filename matches YYYY-MM-DD-HH-MM-SS pattern"""

def test_snapshot_template_rendering():
    """Verify all template variables are substituted"""

def test_snapshot_directory_creation():
    """Verify snapshots/ and archive/ directories created if missing"""

def test_snapshot_immutability():
    """Verify snapshot file is read-only after creation"""

def test_snapshot_missing_tasks():
    """Verify graceful handling when ACTIVE_TASKS.md missing"""

def test_snapshot_missing_git():
    """Verify graceful handling when git not available"""
```

### 8.2 Integration Testing

**Test Scenarios**:
1. **End-to-End Snapshot**: Run `/aisdlc-snapshot-context`, verify file created
2. **Snapshot + Checkpoint**: Run both commands, verify integration
3. **Context Recovery**: Create snapshot, clear context, restore from snapshot
4. **Archival**: Create 50 snapshots, trigger archival, verify archive structure
5. **Team Handoff**: Create snapshot, share, restore on different machine

**BDD Scenarios**:
```gherkin
Feature: Context Snapshot and Recovery
  # Validates: REQ-TOOL-012.0.1.0

  Scenario: Create basic snapshot
    Given I have an initialized workspace
    And I have active tasks in ACTIVE_TASKS.md
    When I run /aisdlc-snapshot-context
    Then a snapshot file is created in .ai-workspace/context_history/
    And the filename matches pattern {YYYYMMDD}_{HHMM}_{label}.md
    And the snapshot contains active tasks summary
    And the snapshot contains recovery guidance

  Scenario: Restore context from snapshot
    Given I have a snapshot file 20251216_1430_implementing_auth_service.md
    And I have lost conversation history
    When I ask Claude to "Restore context from 20251216_1430_implementing_auth_service"
    Then Claude reads the snapshot file
    And Claude summarizes the snapshot contents
    And Claude suggests next steps from the snapshot

  Scenario: Snapshot with checkpoint integration
    Given I have completed 2 tasks
    And I have 1 task in progress
    When I run /aisdlc-checkpoint-tasks
    And I run /aisdlc-snapshot-context
    Then the checkpoint updates ACTIVE_TASKS.md
    And the snapshot reflects the updated task status
    And the snapshot shows 2 recently completed tasks
```

### 8.3 Manual Testing Checklist

- [ ] Create snapshot in empty workspace (should handle gracefully)
- [ ] Create snapshot with active tasks
- [ ] Create snapshot with git changes
- [ ] Create snapshot without git available
- [ ] Restore context from snapshot (manually read and tell Claude)
- [ ] Create 10 snapshots, verify chronological listing
- [ ] Verify snapshot file is human-readable markdown
- [ ] Verify snapshot contains all required sections
- [ ] Verify recovery guidance is actionable
- [ ] Test team handoff (share snapshot, restore on different machine)

---

## 9. Documentation Requirements

### 9.1 User Documentation

**Command Reference** (`/aisdlc-snapshot-context` help):
- Purpose
- Usage
- Output format
- Recovery procedure
- Integration with `/aisdlc-checkpoint-tasks`
- Examples

**Workflow Guide**:
- When to create snapshots (end of session, before handoff, before risky changes)
- How to restore from snapshots
- Team handoff best practices
- Archival policy and configuration

### 9.2 Developer Documentation

**Design Document** (this document):
- Architecture and data flow
- Template design
- Command specification
- Archival design
- Testing strategy

**Implementation Guide**:
- Code structure
- Template rendering logic
- Conversation analysis algorithm
- Archival implementation
- Extension points

---

## 10. Acceptance Criteria Validation

| Requirement | Design Element | Validation |
|-------------|---------------|------------|
| Command available: `/aisdlc-snapshot-context` | Section 4.1 | ✅ Command specification defined |
| Snapshots stored in `.ai-workspace/context_history/` | Section 2.1 | ✅ Directory structure specified |
| Snapshot includes: timestamp, active tasks summary, current work context, conversation state markers | Section 3.1 | ✅ Template includes all required sections |
| Snapshots are immutable (append-only) | Section 4.2, Phase 4 | ✅ Read-only file permissions after creation |
| Filename format: `{YYYYMMDD}_{HHMM}_{label}.md` | Section 4.2, Phase 3 | ✅ Filename generation specified |
| Recovery guidance included | Section 3.1 | ✅ Recovery section in template |
| Integrates with `/aisdlc-checkpoint-tasks` | Section 4.5 | ✅ Integration workflow defined |
| Archival after 30 days | Section 5 | ✅ Archival policy and process defined |

---

## 11. References

### Requirements
- [REQ-TOOL-012.0.1.0](../../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md#req-tool-012010-context-snapshot-and-recovery) - Context Snapshot and Recovery

### Related Requirements
- REQ-TOOL-002 - Developer Workspace
- REQ-TOOL-003 - Workflow Commands

### Related Design Documents
- [AISDLC_IMPLEMENTATION_DESIGN.md](AISDLC_IMPLEMENTATION_DESIGN.md) - Overall system design
- [Workflow Commands](../../claude-code/.claude-plugin/plugins/aisdlc-methodology/commands/README.md)

### Related Commands
- `/aisdlc-checkpoint-tasks` - Task status checkpoint
- `/aisdlc-status` - Project status display
- `/aisdlc-init` - Workspace initialization

---

**Document Status**: Draft (v1.0)
**Last Updated**: 2025-12-16
**Next Review**: After implementation

**Revision History**:
- v1.0 (2025-12-16): Initial design for REQ-TOOL-012.0.1.0

---

**"Excellence or nothing"**
