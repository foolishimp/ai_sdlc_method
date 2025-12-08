# /aisdlc-status - Show Project Status and Next Steps

Display current task status and suggest the next action based on project state.

<!-- Implements: REQ-TOOL-003 (Workflow Commands) -->

## Instructions

Show a snapshot of project status and intelligently suggest next steps.

### Step 0: Get Version

Read the plugin version from the plugin.json file at:
`claude-code/.claude-plugin/plugins/aisdlc-methodology/.claude-plugin/plugin.json`

Display this version in the header (e.g., "v0.4.9").

### Step 1: Check Workspace Exists

First, check if `.ai-workspace/` exists:
- If NOT: suggest running `/aisdlc-init`

### Step 2: Check Mandatory Artifacts

Check for these mandatory artifacts:
- `docs/requirements/INTENT.md`
- `docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`
- `docs/design/*/AISDLC_IMPLEMENTATION_DESIGN.md`
- `docs/TRACEABILITY_MATRIX.md`

### Step 3: Read Task Status

Read `.ai-workspace/tasks/active/ACTIVE_TASKS.md`:
- Count tasks by status (in_progress, pending, blocked, completed)
- List active task titles with REQ-* tags

List recently finished tasks from `.ai-workspace/tasks/finished/` (last 5).

### Step 4: Determine Next Step

Based on state, suggest the most logical next action from this progression:

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: /aisdlc-init                                       │
│          Initialize workspace and artifact templates        │
│                          ↓                                  │
│  Step 2: Edit docs/requirements/INTENT.md                   │
│          Describe what you want to build                    │
│                          ↓                                  │
│  Step 3: "Help me create requirements from INTENT.md"       │
│          → Generates REQ-F-*, REQ-NFR-*, etc.               │
│                          ↓                                  │
│  Step 4: "Design a solution for REQ-F-XXX-001"              │
│          → Creates components, ADRs, traceability           │
│                          ↓                                  │
│  Step 5: "Break down the design into tasks"                 │
│          → Creates work items in ACTIVE_TASKS.md            │
│                          ↓                                  │
│  Step 6: "Work on Task #1 using TDD"                        │
│          → RED → GREEN → REFACTOR → COMMIT                  │
│                          ↓                                  │
│  Step 7: /aisdlc-checkpoint-tasks                           │
│          → Save progress                                    │
│                          ↓                                  │
│  Step 8: /aisdlc-release                                    │
│          → Create release with changelog                    │
└─────────────────────────────────────────────────────────────┘
```

**Next Step Logic**:
| State | You Are At | Suggested Next Step |
|-------|------------|---------------------|
| No workspace | — | Step 1: `/aisdlc-init` |
| No INTENT.md content | Step 1 ✓ | Step 2: Edit `docs/requirements/INTENT.md` |
| INTENT exists, no REQ-* | Step 2 ✓ | Step 3: "Help me create requirements" |
| REQ-* exists, no design | Step 3 ✓ | Step 4: "Design a solution for REQ-F-XXX-001" |
| Design exists, no tasks | Step 4 ✓ | Step 5: "Break down the design into tasks" |
| Tasks exist, none in progress | Step 5 ✓ | Step 6: Pick a task: "Work on Task #X" |
| Task in progress | Step 6 | Continue or `/aisdlc-checkpoint-tasks` |
| All tasks complete | Step 7 ✓ | Step 8: `/aisdlc-release` |

### Step 5: Display Output

```
╔══════════════════════════════════════════════════════════════╗
║                    AI SDLC Project Status                    ║
║                        Version: {version}                    ║
╚══════════════════════════════════════════════════════════════╝

📁 Workspace: {✅ Initialized | ❌ Not found - run /aisdlc-init}

📄 Artifacts:
   {✅ | ❌} INTENT.md           {status: Empty | Has content}
   {✅ | ❌} Requirements        {count} REQ-* keys defined
   {✅ | ❌} Design              {count} components defined
   {✅ | ❌} Traceability Matrix {coverage %}

📋 Tasks:
   In Progress: {count}
   Pending:     {count}
   Blocked:     {count}
   Completed:   {count}

   Active Tasks:
   {list task titles with REQ-* tags, or "(No active tasks)"}

✅ Recently Finished:
   {list last 5 finished tasks or "(None yet)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 NEXT STEP: {intelligent suggestion based on state}

   {explanation of why this is the next step}

   Example: "{specific command or prompt to use}"
```

---

**Note**: This command is read-only. Run the suggested action to proceed.
