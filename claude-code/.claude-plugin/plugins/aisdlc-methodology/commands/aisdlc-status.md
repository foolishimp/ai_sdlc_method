# /aisdlc-status - Show Project Status and Next Steps

Display current task status and suggest the next action based on project state.

<!-- Implements: REQ-F-CMD-001 (Slash commands for workflow) -->

## Instructions

Show a snapshot of project status and intelligently suggest next steps.

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

Based on state, suggest the most logical next action:

| State | Suggested Next Step |
|-------|---------------------|
| No workspace | `/aisdlc-init` - Initialize workspace and artifacts |
| No INTENT.md content | Edit `docs/requirements/INTENT.md` with your project intent |
| INTENT exists, no REQ-* | "Help me create requirements from INTENT.md" (Requirements Agent) |
| REQ-* exists, no design | "Design a solution for REQ-F-XXX-001" (Design Agent) |
| Design exists, no tasks | "Break down the design into tasks" (Tasks Agent) |
| Tasks exist, none in progress | Pick a task: "Work on Task #X" |
| Task in progress | Continue current task, or `/aisdlc-checkpoint-tasks` to save |
| All tasks complete | `/aisdlc-release` to create a release |

### Step 5: Display Output

```
╔══════════════════════════════════════════════════════════════╗
║                    AI SDLC Project Status                    ║
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
