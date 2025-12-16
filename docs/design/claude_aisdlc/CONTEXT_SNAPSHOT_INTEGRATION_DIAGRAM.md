# Context Snapshot Integration Diagram

**Requirement**: REQ-TOOL-012.0.1.0
**Solution**: claude_aisdlc

---

## Integration with Existing Commands

```
┌─────────────────────────────────────────────────────────────────┐
│                        Work Session Flow                         │
└─────────────────────────────────────────────────────────────────┘

Developer starts work
         ↓
    /aisdlc-status
         │ (Shows what to work on next)
         ↓
    Work on tasks
    (Code, test, commit)
         ↓
    /aisdlc-checkpoint-tasks ←─────────────────┐
         │                                     │
         │ Updates:                            │
         │ • ACTIVE_TASKS.md                   │
         │ • Moves completed → finished/       │
         │                                     │
         ↓                                     │
    /aisdlc-snapshot-context                  │
         │                                     │
         │ Creates:                            │
         │ • snapshot-{timestamp}.md           │
         │                                     │
         │ Reads:                              │
         │ • ACTIVE_TASKS.md ──────────────────┘
         │ • Conversation history
         │ • git status
         │
         ↓
    End session
         │
         └──────────────────────────────┐
                                        │
         ┌──────────────────────────────┘
         │
    Next session starts
         │
         ↓
    /aisdlc-status
         │ (May suggest restoring from snapshot)
         ↓
    "Restore context from {YYYYMMDD}_{HHMM}_{label}"
         │
         │ Claude reads snapshot
         │ • Summarizes where you were
         │ • Shows open questions
         │ • Suggests next steps
         ↓
    Resume work from exact point
```

---

## Data Flow Between Commands

```
┌────────────────────────────────────────────────────────────────────┐
│                        /aisdlc-checkpoint-tasks                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  1. Analyze conversation for completed work                  │  │
│  │  2. Update ACTIVE_TASKS.md                                    │  │
│  │  3. Create finished task docs in finished/                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬───────────────────────────────┘
                                     │
                                     │ (ACTIVE_TASKS.md updated)
                                     ↓
┌────────────────────────────────────────────────────────────────────┐
│                        /aisdlc-snapshot-context                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Reads:                                                       │  │
│  │  • ACTIVE_TASKS.md (task status from checkpoint)             │  │
│  │  • finished/*.md (recent completed work)                     │  │
│  │  • Conversation history (decisions, questions, blockers)     │  │
│  │  • git status (file changes)                                 │  │
│  │                                                               │  │
│  │  Generates:                                                   │  │
│  │  • {YYYYMMDD}_{HHMM}_{label}.md                              │  │
│  │    - Active tasks summary                                     │  │
│  │    - Work context                                             │  │
│  │    - Conversation markers                                     │  │
│  │    - Recovery guidance                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬───────────────────────────────┘
                                     │
                                     │ (snapshot created)
                                     ↓
                        .ai-workspace/context_history/
                        20251216_1430_implementing_auth_service.md
                                     │
                                     │ (Developer leaves, returns later)
                                     ↓
                        Developer: "Restore from snapshot..."
                                     │
                                     ↓
                        Claude reads snapshot, summarizes context
                                     │
                                     ↓
                        Developer resumes exactly where they left off
```

---

## Directory Structure Integration

```
.ai-workspace/
│
├── config/
│   └── workspace_config.yml
│       └── context_snapshots:           # Snapshot configuration
│             retention_days: 30
│
├── tasks/
│   ├── active/
│   │   └── ACTIVE_TASKS.md              ◄─── Read by snapshot
│   │                                          (task status)
│   └── finished/
│       └── 20251216_1430_task_42.md     ◄─── Read by snapshot
│                                              (recent completed work)
│
├── context_history/                     ◄─── NEW (REQ-TOOL-012)
│   ├── 20251215_1030_fixing_payment_tests.md
│   ├── 20251215_1645_context_snapshot.md
│   ├── 20251216_1430_implementing_auth_service.md  ◄─── Created by command
│   └── README.md                        ◄─── Directory documentation
│
└── templates/
    ├── ACTIVE_TASKS_TEMPLATE.md
    ├── FINISHED_TASK_TEMPLATE.md
    └── CONTEXT_SNAPSHOT_TEMPLATE.md     ◄─── NEW (REQ-TOOL-012)
```

---

## Command Interaction Matrix

| Command | Reads | Writes | Integration Points |
|---------|-------|--------|--------------------|
| `/aisdlc-status` | ACTIVE_TASKS.md<br>finished/<br>context_history/ | None | Can suggest snapshot recovery |
| `/aisdlc-checkpoint-tasks` | ACTIVE_TASKS.md<br>Conversation | ACTIVE_TASKS.md<br>finished/*.md | Updates task status for snapshot |
| `/aisdlc-snapshot-context` | ACTIVE_TASKS.md<br>finished/<br>Conversation<br>git status | context_history/*.md | Captures full context including task status |
| (User) Restore context | context_history/*.md | None | Manual recovery by reading snapshot |

---

## Workflow Examples

### Example 1: End-of-Day Save

```
15:00 - Developer works on authentication feature
        • Implements user login
        • Writes tests
        • Fixes bug in password validation

16:30 - Developer ready to finish work
        ↓
        /aisdlc-checkpoint-tasks
        ↓
        ╔═══════════════════════════════════════════════════════╗
        ║           Task Checkpoint - 2025-12-16 16:30          ║
        ╚═══════════════════════════════════════════════════════╝

        ✅ Completed: 1 task(s)
           #42: Implement user login (REQ-F-AUTH-001)
           → Archived to finished/20251216_1630_user_login.md

        🔄 In Progress: 1 task(s)
           #43: Password validation (REQ-F-AUTH-002)
        ↓
        /aisdlc-snapshot-context
        ↓
        ╔═══════════════════════════════════════════════════════╗
        ║        Context Snapshot Created Successfully          ║
        ╚═══════════════════════════════════════════════════════╝

        📸 Snapshot: 20251216_1630_implementing_user_login
        📊 Contents:
           ✓ Active Tasks: 2 (1 in-progress, 1 pending)
           ✓ File Changes: 0 (clean working directory)
           ✓ Conversation Markers: 1 open question

16:35 - Developer closes laptop, goes home
```

### Example 2: Morning Recovery

```
09:00 - Developer returns next morning
        • New laptop, no conversation history
        ↓
        Developer: "Restore context from 20251216_1630_implementing_user_login"
        ↓
        Claude reads: .ai-workspace/context_history/20251216_1630_implementing_user_login.md
        ↓
        ╔═══════════════════════════════════════════════════════╗
        ║                Context Restored                       ║
        ╚═══════════════════════════════════════════════════════╝

        📋 Session Summary:
           - Date: 2025-12-16 16:30:00
           - Branch: feature/auth-service
           - Tasks: 2 active (1 in-progress, 1 pending)

        🎯 You were working on:
           - Task #43: Password validation (REQ-F-AUTH-002)
           - Status: In Progress
           - Recent: Fixed bug in password validation

        💬 Open Questions:
           1. Should we enforce minimum password complexity?

        🔄 Next Steps:
           1. Complete password validation tests
           2. Add integration tests
        ↓
09:05 - Developer picks up exactly where they left off
```

### Example 3: Team Handoff

```
Developer A (17:00):
        • Completes checkpoint
        • Creates snapshot
        • Sends snapshot file to Developer B

Developer B (09:00 next day):
        • Opens Claude
        • Shares snapshot content with Claude
        ↓
        Claude: "✅ Context loaded from handoff snapshot

        📋 Previous Developer Context:
           - Left off: Implementing authentication
           - Completed: User login endpoint
           - In Progress: Password validation
           - Blocked: Waiting for security review

        🎯 Where to Resume:
           Continue password validation after security approval"
        ↓
        Developer B continues seamlessly
```

---

## Archival Process Flow

```
Snapshot Created
      ↓
.ai-workspace/context_history/20251216_1430_implementing_auth_service.md
      │
      │ (After 30 days)
      ↓
Manual Archival/Deletion
      │ (developer decision)
      ↓
Options:
  1. Delete old snapshot
  2. Move to personal archive location
  3. Keep indefinitely
      │
      ↓
Note: No automatic archival in initial version
```

---

## Error Handling Integration

```
/aisdlc-snapshot-context
      ↓
Workspace check
      ├─ NOT initialized
      │     ↓
      │  ❌ Error: Run /aisdlc-init first
      │
      ├─ Initialized
      │     ↓
      └─ Continue
            ↓
Directory check
      ├─ NOT exists
      │     ↓
      │  Create .ai-workspace/context_history/snapshots/
      │  Create .ai-workspace/context_history/archive/
      │     ↓
      └─ Exists
            ↓
Template check
      ├─ NOT exists
      │     ↓
      │  ⚠️  Warning: Using built-in template
      │     ↓
      └─ Exists
            ↓
ACTIVE_TASKS.md check
      ├─ NOT exists
      │     ↓
      │  ⚠️  Warning: No task data in snapshot
      │     ↓
      └─ Exists
            ↓
Git check
      ├─ NOT available
      │     ↓
      │  ⚠️  Warning: No git data in snapshot
      │     ↓
      └─ Available
            ↓
Create snapshot (all warnings non-fatal, continue gracefully)
      ↓
✅ Success
```

---

## Performance Considerations

| Operation | Typical Time | Max Time | Notes |
|-----------|--------------|----------|-------|
| Read ACTIVE_TASKS.md | <100ms | 500ms | Small file |
| Analyze conversation | 1-3s | 10s | Limited to last 20-50 messages |
| Run git commands | 100-500ms | 2s | 3 commands total |
| Template rendering | <100ms | 500ms | Simple text substitution |
| Write snapshot | <100ms | 500ms | ~20-50 KB file |
| **Total** | **2-5s** | **10s** | Acceptable for end-of-session |

**Optimization Strategies**:
- Limit conversation analysis to recent messages (not full history)
- Parallel execution where possible (git commands, file reads)
- Template caching (load once, reuse)
- Incremental index updates (not full rebuild)

---

## Security Considerations

```
Snapshot Content                 Security Measure
─────────────────────────────────────────────────────────
Active tasks                     ✅ Safe (no secrets)
File paths                       ✅ Safe (no content)
Git branch name                  ✅ Safe
Conversation markers             ⚠️  Sanitize for API keys, tokens
Open questions                   ✅ Safe (typically safe)
Decisions                        ✅ Safe (architectural only)
Commands run                     ⚠️  Sanitize for credentials

Protection Measures:
1. Pattern matching to detect/remove:
   - API keys (pattern: [A-Za-z0-9]{20,})
   - Tokens (pattern: Bearer .*, token=.*)
   - Passwords (pattern: password=.*, pwd=.*)

2. File permissions:
   - Set snapshots to read-only after creation
   - Prevent accidental modification

3. Git ignore:
   - Recommend adding .ai-workspace/context_history/ to .gitignore
   - Prevents accidental commit to public repos

4. Team handoff:
   - Share snapshots via secure channels
   - Not via public chat, email, etc.
```

---

**Document Status**: Active (v1.0)
**Last Updated**: 2025-12-16
**Next Review**: After implementation

---

**"Excellence or nothing"**
