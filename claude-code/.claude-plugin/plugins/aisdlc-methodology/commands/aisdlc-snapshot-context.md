# /aisdlc-snapshot-context - Capture Session Context Snapshot

Capture current session context into an immutable snapshot for recovery and continuity.

<!-- Implements: REQ-TOOL-012.0.1.0 (Context Snapshot and Recovery) -->
<!-- Implements: REQ-TOOL-002 (Developer Workspace) -->
<!-- Implements: REQ-TOOL-003 (Workflow Commands) -->

**Usage**: `/aisdlc-snapshot-context`

**Instructions**:

## Phase 1: Validation

1. **Check workspace exists**:
   - Verify `.ai-workspace/` directory exists
   - If NOT: Error: "❌ Workspace not initialized. Run /aisdlc-init first."

2. **Ensure context_history directory exists**:
   - Check `.ai-workspace/context_history/` exists
   - If NOT: Create directory

3. **Check template availability**:
   - Try to read `.ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md`
   - If NOT found: Use built-in template (defined in Phase 3)
   - Log: "⚠️  Warning: Template not found, using built-in template"

## Phase 2: Context Gathering

### 2.1 Gather Task Context

1. **Read active tasks**:
   - Read `.ai-workspace/tasks/active/ACTIVE_TASKS.md`
   - If NOT found: Log warning, continue with empty task data

2. **Parse tasks by status**:
   - Count tasks by status: in_progress, pending, blocked
   - For each status, extract:
     - Task ID (e.g., #42)
     - Task title
     - REQ-* tags
     - Blocker reason (for blocked tasks)

3. **Create task tables**:
   ```
   Format for in_progress/pending:
   - Task #{ID}: {TITLE} | REQ-{TAGS}

   Format for blocked:
   - Task #{ID}: {TITLE} | REQ-{TAGS} | Blocker: {REASON}
   ```

### 2.2 Analyze Conversation Context

1. **Extract work activities** (from recent conversation, last 20-50 messages):
   - Look for mentions of:
     - "Implemented...", "Added...", "Fixed...", "Created..."
     - File modifications mentioned
     - Test results mentioned
     - Commits made

2. **Identify decisions made**:
   - Look for phrases like:
     - "We decided to...", "Using...", "Chose to..."
     - Architecture choices
     - Technology selections
     - Design patterns adopted

3. **Capture open questions**:
   - Look for unresolved questions:
     - Questions asked by user
     - Questions raised during discussion
     - "Should we...?", "Which approach...?", "What about...?"

4. **Note blockers/issues**:
   - Look for:
     - "Blocked by...", "Waiting for...", "Cannot proceed until..."
     - Failing tests mentioned
     - Missing dependencies
     - Approval pending

5. **Extract next steps**:
   - Look for:
     - "Next we need to...", "TODO:", "Remaining work:"
     - Incomplete acceptance criteria
     - Planned improvements

### 2.3 Gather Git Context

1. **Run git commands** (if git available):
   ```bash
   git branch --show-current  # Current branch
   git status                 # File changes
   git log --oneline -n 5     # Recent commits
   ```

2. **Parse git status output**:
   - Modified files (uncommitted)
   - Staged files
   - Untracked files

3. **Handle git not available**:
   - If git commands fail: Log warning, continue with empty git data
   - Warning: "⚠️  Git not available, skipping file change detection"

### 2.4 Gather Metadata

1. **Get timestamp**:
   - Current date/time in format: `YYYY-MM-DD HH:MM:SS`
   - For filename: `YYYY-MM-DD-HH-MM-SS` (no spaces, no colons)

2. **Get project name**:
   - Try to read from `.ai-workspace/config/workspace_config.yml`
   - If not found: Use directory name
   - If not found: Use "Unknown Project"

3. **Get retention policy**:
   - Try to read `retention_days` from workspace_config.yml
   - Default: 30 days

4. **List existing snapshots**:
   - List files in `.ai-workspace/context_history/snapshots/`
   - Sort chronologically
   - Identify previous snapshot (most recent before this one)
   - Count total snapshots

## Phase 3: Snapshot Generation

### 3.1 Load Template

1. **Read template file**:
   - Try: `.ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md`
   - If found: Use as base
   - If NOT found: Use built-in template

### 3.2 Substitute Template Variables

Replace all template placeholders with gathered context:

| Variable | Source | Fallback |
|----------|--------|----------|
| `{TIMESTAMP}` | Current datetime | Required |
| `{YYYY-MM-DD}` | Current date | Required |
| `{HH:MM:SS}` | Current time | Required |
| `{HH-MM-SS}` | Current time (filename-safe) | Required |
| `{SNAPSHOT_ID}` | `{YYYYMMDD}_{HHMM}_{label}` | Required |
| `{PROJECT_NAME}` | Workspace config or dir name | "Unknown Project" |
| `{GIT_BRANCH}` | `git branch --show-current` | "(not in git repo)" |
| `{TOTAL_ACTIVE_COUNT}` | Count of active tasks | 0 |
| `{IN_PROGRESS_COUNT}` | Count of in-progress tasks | 0 |
| `{PENDING_COUNT}` | Count of pending tasks | 0 |
| `{BLOCKED_COUNT}` | Count of blocked tasks | 0 |
| `{IN_PROGRESS_TASKS_TABLE}` | Formatted task list | "(None)" |
| `{PENDING_TASKS_TABLE}` | Formatted task list | "(None)" |
| `{BLOCKED_TASKS_TABLE}` | Formatted task list | "(None)" |
| `{CURRENT_WORK_DESCRIPTION}` | From conversation analysis | "(No active work detected)" |
| `{RECENT_ACTIVITIES_LIST}` | From conversation analysis | "(No recent activities)" |
| `{NEXT_STEPS_LIST}` | From conversation analysis | "(No next steps defined)" |
| `{DECISIONS_LIST}` | From conversation analysis | "(No decisions recorded)" |
| `{QUESTIONS_LIST}` | From conversation analysis | "(No open questions)" |
| `{BLOCKERS_LIST}` | From conversation analysis | "(No blockers)" |
| `{COMMAND_HISTORY}` | Last 5-10 commands | "(No commands tracked)" |
| `{MODIFIED_FILES_LIST}` | From git status | "(No modified files)" |
| `{STAGED_FILES_LIST}` | From git status | "(No staged files)" |
| `{UNTRACKED_FILES_LIST}` | From git status | "(No untracked files)" |
| `{GIT_STATUS_OUTPUT}` | Full git status output | "(Git not available)" |
| `{PREVIOUS_SNAPSHOT_ID}` | Previous snapshot filename | "None" |
| `{NEXT_SNAPSHOT_ID}` | Always "None (latest)" | "None (latest)" |
| `{MESSAGE_COUNT}` | Conversation message count | "Unknown" |
| `{SESSION_DURATION}` | Estimated time | "Unknown" |
| `{COMMAND_COUNT}` | Commands run this session | "Unknown" |
| `{FILES_MODIFIED_COUNT}` | Count from git status | 0 |
| `{TESTS_RUN_SUMMARY}` | From conversation | "None" |
| `{COMMIT_COUNT}` | From git log | 0 |
| `{SOLUTION_NAME}` | From design path | "unknown_solution" |
| `{RECENT_FINISHED_TASKS_LIST}` | Last 3 from finished/ | "(None)" |
| `{RETENTION_DAYS}` | From workspace config | 30 |
| `{WORK_SUMMARY}` | Brief work summary | "continuing previous work" |
| `{OPEN_QUESTIONS_SUMMARY}` | Summary of questions | "No open questions." |

### 3.3 Handle Missing Data Gracefully

For each section, if data is not available:
- Use fallback text (e.g., "(None)", "(Not available)")
- Do NOT leave blank or show error messages
- Include section header even if empty

## Phase 4: Persistence

### 4.1 Write Snapshot File

1. **Generate filename** (follows finished task convention):
   - Format: `{YYYYMMDD}_{HHMM}_{label}.md`
   - Label: derived from current work focus (snake_case, max 50 chars)
   - Example: `20251216_1430_implementing_auth_service.md`
   - If no clear label: use `context_snapshot` as default

2. **Write to context_history directory**:
   - Path: `.ai-workspace/context_history/{filename}`
   - Content: Rendered template with all variables substituted

3. **Set file permissions** (if platform supports):
   - Make file read-only to enforce immutability
   - If fails: Log warning, continue

### 4.2 Update Index (Optional Future Enhancement)

If `.ai-workspace/context_history/.snapshot_index.yml` exists:
1. Append new snapshot entry:
   ```yaml
   - id: snapshot-2025-12-16-14-30-45
     timestamp: 2025-12-16T14:30:45Z
     tasks_count: 5
     files_changed: 8
     prev: snapshot-2025-12-15-10-30-00
     archived: false
   ```
2. Update previous snapshot's `next` field

## Phase 5: Reporting

### 5.1 Display Success Message

```
╔══════════════════════════════════════════════════════════════╗
║             Context Snapshot Created Successfully            ║
╚══════════════════════════════════════════════════════════════╝

📸 Snapshot: {SNAPSHOT_ID}
📁 Location: .ai-workspace/context_history/{filename}

📊 Snapshot Contents:
   ✓ Active Tasks: {TOTAL_ACTIVE_COUNT} ({IN_PROGRESS_COUNT} in-progress, {PENDING_COUNT} pending{, BLOCKED_COUNT blocked})
   ✓ File Changes: {FILES_MODIFIED_COUNT} modified, {STAGED_COUNT} staged
   ✓ Conversation Markers: {DECISIONS_COUNT} decisions, {QUESTIONS_COUNT} open questions
   ✓ Recovery Guidance: Included

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 To restore this context later:

   1. Read the snapshot:
      cat .ai-workspace/context_history/{filename}

   2. Tell Claude:
      "Restore context from {SNAPSHOT_ID}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Total Snapshots: {TOTAL_SNAPSHOTS} active, {ARCHIVED_COUNT} archived
```

### 5.2 Handle Errors

If snapshot creation fails at any point:

```
❌ Error: Failed to create context snapshot

Reason: {error_message}

Troubleshooting:
1. Check workspace is initialized: /aisdlc-init
2. Verify write permissions in .ai-workspace/context_history/
3. Check disk space available

For help: /aisdlc-help
```

## Phase 6: Archival Check (Optional Future Enhancement)

After successful snapshot creation:

1. **Count snapshots in active directory**:
   - If > 50 snapshots: Suggest archival
   - If > 100 snapshots: Force archival

2. **Check snapshot ages**:
   - Find snapshots older than retention period (default: 30 days)
   - If any found: Suggest archival

3. **Archive old snapshots** (if configured):
   - Move snapshots to `.ai-workspace/context_history/archive/{YYYY-MM}/`
   - Update archive index
   - Report: "📦 Archived {count} old snapshots"

---

## Error Handling

| Error Condition | Message | Action |
|----------------|---------|--------|
| Workspace not initialized | "❌ Error: Workspace not initialized. Run /aisdlc-init first." | Exit |
| Cannot create directory | "❌ Error: Cannot create context_history directory: {reason}" | Exit |
| Cannot write snapshot | "❌ Error: Cannot write snapshot: {reason}" | Exit |
| Template missing | "⚠️  Warning: Template not found, using built-in template" | Continue |
| Git not available | "⚠️  Warning: Git not available, skipping file change detection" | Continue |
| ACTIVE_TASKS.md missing | "⚠️  Warning: ACTIVE_TASKS.md not found, snapshot will have no task data" | Continue |

---

## Integration with /aisdlc-checkpoint-tasks

**Recommended Workflow**:
1. Work on tasks
2. Run `/aisdlc-checkpoint-tasks` (updates task status, creates finished docs)
3. Run `/aisdlc-snapshot-context` (captures full session context)
4. End session

**Complementary Purposes**:
- `/aisdlc-checkpoint-tasks` - Updates ACTIVE_TASKS.md, moves completed tasks to finished/
- `/aisdlc-snapshot-context` - Captures broader context (conversation, decisions, questions)

**Data Flow**:
```
/aisdlc-checkpoint-tasks
    ↓ (updates)
ACTIVE_TASKS.md
    ↓ (reads)
/aisdlc-snapshot-context
    ↓ (creates)
{YYYYMMDD}_{HHMM}_{label}.md (includes task status from ACTIVE_TASKS.md)
```

---

## Usage Examples

### Example 1: Basic Snapshot

**User**: `/aisdlc-snapshot-context`

**Output**:
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

   1. Read the snapshot:
      cat .ai-workspace/context_history/20251216_1430_implementing_auth_service.md

   2. Tell Claude:
      "Restore context from 20251216_1430_implementing_auth_service"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Total Snapshots: 8
```

### Example 2: Context Recovery

**User**: "Restore context from 20251216_1430_implementing_auth_service"

**Claude Process**:
1. Read `.ai-workspace/context_history/20251216_1430_implementing_auth_service.md`
2. Parse snapshot content
3. Summarize for user

**Output**:
```
✅ Context restored from 20251216_1430_implementing_auth_service

📋 Session Summary (from snapshot):
   - Date: 2025-12-16 14:30
   - Branch: feature/auth-service
   - Tasks: 3 active (2 in-progress, 1 pending)

🎯 You were working on:
   - Task #42: Implement user authentication (REQ-F-AUTH-001)
   - Status: In Progress
   - Recent: Fixed failing tests in auth_service_test.py

💬 Open Questions (from snapshot):
   1. Should we add rate limiting now or in next sprint?

📁 Uncommitted Work:
   - src/auth/auth_service.py (modified)
   - tests/auth/test_auth_service.py (modified)

🔄 Next Steps (from snapshot):
   1. Complete refactoring of error handling
   2. Add integration tests for login flow

Ready to continue? I can help with the next steps or answer the open question.
```

---

## Notes

- Snapshots are **immutable** - never modify after creation
- Snapshots complement `/aisdlc-checkpoint-tasks` - use both for complete session save
- Snapshots are **human-readable** - share with team members for handoffs
- Old snapshots archived automatically after retention period (default: 30 days)
- Snapshots focus on **context**, not full conversation replay
- If conversation history API not available, conversation analysis will be limited

**Recommended Usage**:
- End of work session
- Before team handoff
- Before risky changes (major refactor, architecture change)
- Weekly snapshot for project continuity
- After completing major milestones
