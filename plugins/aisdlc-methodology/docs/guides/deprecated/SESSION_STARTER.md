# Session Starter Checklist

## 🚀 Start of Every Session

Run these commands and review these items EVERY time you start working:

### 1. Check Current State
```bash
# Where are we?
git status
git log --oneline -5

# What's active?
cat methodology/active_tasks/ACTIVE_TASKS.md  # or your task tracking file

# Any failing tests?
pytest  # or npm test, depending on your project
```

### 2. Review Core Documents
- [ ] Read `methodology/principles/KEY_PRINCIPLES.md` - The 7 Sacred Principles
- [ ] Read `methodology/processes/TDD_WORKFLOW.md` - TDD methodology
- [ ] Read `methodology/guides/PAIR_PROGRAMMING_WITH_AI.md` - Collaboration approach
- [ ] Read `methodology/README.md` - Quick reference

### 3. Align on Goals
```markdown
Human: "Today we're working on [WHAT]"
AI: "I understand. Let me check the current state and active tasks..."
```

### 4. Choose Working Mode
- [ ] **Pair Programming Mode**: Human drives strategy, AI navigates
- [ ] **TDD Mode**: RED → GREEN → REFACTOR cycle
- [ ] **Bug Fix Mode**: Reproduce → Test → Fix → Verify
- [ ] **Exploration Mode**: Research and investigation

### 5. Set Up for Success
```bash
# Start dev server if needed
npm run dev  # or python manage.py runserver, etc.

# Start test watcher for TDD
pytest --watch  # or npm test -- --watch

# Open browser to relevant page (if web project)
# open http://localhost:3000/[relevant-page]
```

---

## 📝 Quick Session Template

Copy and paste this at the start of each session:

```markdown
## Session: [DATE] [TIME]

### Goals
1. [ ] Primary goal
2. [ ] Secondary goal
3. [ ] Stretch goal

### Current Task
- Task #N from active tasks
- Status: In Progress
- Feature Flag: task-N-feature-name (if applicable)

### Approach
- [ ] TDD: Write tests first
- [ ] Feature flag created (if new feature)
- [ ] TodoWrite tracking active

### Check-in Schedule
- [ ] 15 min - Initial approach review
- [ ] 30 min - Progress check
- [ ] 45 min - Testing checkpoint
- [ ] 60 min - Documentation & commit

### End of Session
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Committed with proper message
- [ ] Active tasks updated
```

---

## 🔄 Context Recovery

If context is lost mid-session, quickly recover with:

```bash
# What were we doing?
git status
git diff

# What's the plan?
cat methodology/active_tasks/ACTIVE_TASKS.md  # or your task file

# What's the methodology?
head -20 methodology/processes/TDD_WORKFLOW.md

# Recent work?
git log --oneline -10
```

---

## 🎯 Key Principles to Remember

1. **TDD First**: RED → GREEN → REFACTOR
2. **Pair Programming**: Communicate, check-in, collaborate
3. **Small Commits**: One task = one commit
4. **Feature Flags**: New features behind flags (where appropriate)
5. **Documentation**: Every task gets documented
6. **Test Coverage**: Maintain >80%

---

## 🚨 If You Get Lost

Just ask:
- "What's our current task?"
- "Show me the active tasks"
- "What's the TDD process again?"
- "Should we check in?"

The human will help reorient the session!

---

## 💡 Pro Tips

### Before Starting
- **Clear your head**: Take a moment to focus
- **Remove distractions**: Close unrelated tabs/windows
- **Set a timer**: Plan for breaks every 45-60 minutes

### During Session
- **Stay in the zone**: One task at a time
- **Test often**: Don't wait until "done"
- **Commit early**: Save progress incrementally
- **Communicate**: Over-communicate rather than assume

### After Session
- **Document**: Update task tracking
- **Clean up**: Close feature flags if appropriate
- **Reflect**: What went well? What to improve?
- **Plan ahead**: Note what's next

---

## 🎓 Session Success Criteria

A successful session has:
- ✅ Clear goals defined upfront
- ✅ Tests written before code
- ✅ All tests passing
- ✅ Code reviewed and refactored
- ✅ Changes committed with good messages
- ✅ Documentation updated
- ✅ Next steps identified

---

## 🤝 The Session Contract

**At the start of each session, agree on:**
1. What we're building today
2. Who drives first (human or AI)
3. When we'll check in
4. What "done" looks like
5. When we'll take breaks

**This ensures both partners are aligned and working effectively together!**
