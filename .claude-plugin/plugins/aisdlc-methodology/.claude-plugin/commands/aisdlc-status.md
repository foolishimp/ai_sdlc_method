Display current task status from `.ai-workspace/tasks/`.

<!-- Implements: REQ-F-CMD-001 (Slash commands for workflow) -->

## Instructions

Show a quick snapshot of the task queue:

1. **Read** `.ai-workspace/tasks/active/ACTIVE_TASKS.md`
   - Count active tasks (look for "## Task #" headers, exclude examples)
   - List active task titles with priority and status

2. **List** recently finished tasks from `.ai-workspace/tasks/finished/`
   - Show last 5 finished task files (most recent first)

3. **Display** in this simple format:

```
╔══════════════════════════════════════════════════════════════╗
║                    AI SDLC Task Status                       ║
╚══════════════════════════════════════════════════════════════╝

📋 Active Tasks: {count}
   {list task titles with priority/status or "(No tasks in progress)"}

✅ Recently Finished: {count}
   {list last 5 finished tasks or "(No finished tasks yet)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Next: {suggestion based on state}
```

**Suggestions**:
- If no active tasks: "Use /start-session to begin new work"
- If active tasks exist: "Continue working on active tasks"
- If tasks are blocked: "Review dependencies and unblock tasks"

---

**Note**: This command is read-only and just shows task queue status.
