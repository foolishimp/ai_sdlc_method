# Context Snapshot - {TIMESTAMP}

**Created**: {YYYY-MM-DD} {HH:MM}
**Snapshot**: {SNAPSHOT_ID}
**Project**: {PROJECT_NAME}
**Branch**: {GIT_BRANCH}

---

## 🎯 Active Tasks Summary

**Total Active**: {TOTAL_ACTIVE_COUNT}
- In Progress: {IN_PROGRESS_COUNT}
- Pending: {PENDING_COUNT}
- Blocked: {BLOCKED_COUNT}

### Tasks In Progress

{IN_PROGRESS_TASKS_TABLE}

### Tasks Pending

{PENDING_TASKS_TABLE}

### Tasks Blocked

{BLOCKED_TASKS_TABLE}

**Source**: `.ai-workspace/tasks/active/ACTIVE_TASKS.md`

---

## 💼 Current Work Context

**What I'm Working On**:
{CURRENT_WORK_DESCRIPTION}

**Recent Activities**:
{RECENT_ACTIVITIES_LIST}

**Next Steps Planned**:
{NEXT_STEPS_LIST}

---

## 🗣️ Conversation State Markers

**Key Decisions Made**:
{DECISIONS_LIST}

**Open Questions**:
{QUESTIONS_LIST}

**Blockers/Issues**:
{BLOCKERS_LIST}

**Recent Command History**:
```
{COMMAND_HISTORY}
```

---

## 📁 File Changes

**Modified Files** (uncommitted):
{MODIFIED_FILES_LIST}

**Staged Files**:
{STAGED_FILES_LIST}

**Untracked Files**:
{UNTRACKED_FILES_LIST}

**Git Status**:
```
{GIT_STATUS_OUTPUT}
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
   > "I'm resuming work from snapshot {SNAPSHOT_ID}. The snapshot shows I was
   > working on {WORK_SUMMARY}. {OPEN_QUESTIONS_SUMMARY}"

### Quick Commands to Regain Context

```bash
# See current project status
/aisdlc-status

# Review active tasks
cat .ai-workspace/tasks/active/ACTIVE_TASKS.md

# See recent finished work
ls -lt .ai-workspace/tasks/finished/ | head -5

# Check for more snapshots
ls -lt .ai-workspace/context_history/
```

---

## 📊 Metadata

**Snapshot Version**: 1.0
**Template**: `.ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md`
**Related Snapshots**:
- Previous: {PREVIOUS_SNAPSHOT_ID}
- Next: {NEXT_SNAPSHOT_ID}

**Conversation Metrics**:
- Messages in current session: {MESSAGE_COUNT}
- Estimated session duration: {SESSION_DURATION}
- Commands run: {COMMAND_COUNT}

**Statistics**:
- Files modified: {FILES_MODIFIED_COUNT}
- Tests run: {TESTS_RUN_SUMMARY}
- Commits since last snapshot: {COMMIT_COUNT}

---

## 🔗 Related Files

**Essential Reading**:
- `.ai-workspace/tasks/active/ACTIVE_TASKS.md` - Current tasks
- `docs/requirements/INTENT.md` - Original intent
- `docs/design/{SOLUTION_NAME}/AISDLC_IMPLEMENTATION_DESIGN.md` - Design

**Recent Finished Tasks**:
{RECENT_FINISHED_TASKS_LIST}

---

**END OF SNAPSHOT**
