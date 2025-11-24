# Template System Design

**Design Document**
**Version**: 1.0
**Date**: 2025-11-23
**Status**: Draft

---

## Requirements Traceability

This design implements the following requirements:

- **REQ-F-WORKSPACE-001**: Developer workspace structure (.ai-workspace/)
- **REQ-F-WORKSPACE-002**: Task management templates
- **REQ-F-WORKSPACE-003**: Session tracking templates
- **REQ-NFR-CONTEXT-001**: Persistent context across sessions

**Related Design Documents**:
- [Plugin Architecture](PLUGIN_ARCHITECTURE.md) - Plugin system
- [Command System](COMMAND_SYSTEM.md) - Slash commands integration
- [AI SDLC UX Design](AI_SDLC_UX_DESIGN.md) - Overall user experience

---

## 1. Overview

### 1.1 Purpose

The Template System provides **structured, file-based task and session management** for AI-augmented development. Instead of external tools (Jira, Trello, etc.), developers use local markdown files that:

1. **Preserve context** - Tasks and sessions stored in version control
2. **Enable AI collaboration** - Markdown format is LLM-friendly
3. **Support TDD workflow** - Templates enforce RED → GREEN → REFACTOR → COMMIT
4. **Work offline** - No cloud dependencies

### 1.2 The Generic Pattern (Technology-Neutral)

**Core Concept**: Development work requires context management:
- **What am I working on?** (tasks)
- **Why am I working on this?** (session goals)
- **What have I learned?** (finished task documentation)
- **How do I collaborate with AI?** (pair programming patterns)

**The Pattern**:
```
┌──────────────────────────────────────────┐
│  Workspace = Local File Structure       │
│                                          │
│  - Tasks (todo, active, finished)       │
│  - Sessions (current, history)          │
│  - Templates (reusable patterns)        │
│  - Config (preferences)                 │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Template = Structured Markdown          │
│                                          │
│  - Prompts for required fields          │
│  - Section structure (Problem/Solution) │
│  - Acceptance criteria checklist        │
│  - Traceability fields (REQ-*)          │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Workflow = File Lifecycle               │
│                                          │
│  Idea → TODO_LIST.md (quick capture)    │
│    ↓                                    │
│  Task → ACTIVE_TASKS.md (formal)        │
│    ↓                                    │
│  Work → TDD cycle (RED/GREEN/REFACTOR)  │
│    ↓                                    │
│  Done → finished/ (documentation)       │
│    ↓                                    │
│  Archive → archive/ (old tasks)         │
└──────────────────────────────────────────┘
```

**Key Properties**:
1. **File-based** - Git-friendly, no database
2. **Structured** - Templates enforce consistency
3. **Versioned** - Tasks tracked with code
4. **LLM-friendly** - Markdown format for AI parsing

---

## 2. Architecture Decision Records

### ADR-001: File-Based vs Database

**Context**:
- **Requirements**: REQ-F-WORKSPACE-001 (workspace structure), REQ-NFR-CONTEXT-001 (persistent context)
- **Ecosystem Constraints**:
  - Developers already use Git for version control
  - Adding database requires setup/maintenance overhead
  - Markdown is human-readable and LLM-parseable
  - File-based works offline

**Decision**:
- **Structure**: .ai-workspace/ directory with markdown files
- **Version Control**: Tasks/templates in Git, sessions git-ignored
- **Format**: Markdown (not JSON, YAML, or database)

**Rejected Alternatives**:
1. SQLite database - Requires schema migrations, not git-friendly
2. JSON files - Less human-readable
3. External SaaS (Jira, Linear) - Requires internet, API keys, costs money

**Rationale**:
| Aspect | File-based | Database | SaaS |
|--------|-----------|----------|------|
| Git-friendly | ✅ Native | ❌ Binary | ❌ API only |
| Offline | ✅ Yes | ✅ SQLite | ❌ No |
| Human-readable | ✅ Markdown | ⚠️ Queries | ⚠️ Web UI |
| LLM-parseable | ✅ Native | ⚠️ Schema | ❌ API |
| Setup overhead | ✅ None | ⚠️ Migrations | ❌ Account |
| Cost | ✅ Free | ✅ Free | ❌ $10-50/mo |

**Constraints Imposed**:
- Tasks must use markdown format
- No complex queries (must scan files)
- File naming conventions required
- Manual archiving (no auto-cleanup)

---

### ADR-002: Two-Tier Task System

**Context**:
- **Requirements**: REQ-F-WORKSPACE-002 (task management)
- **Ecosystem Constraints**:
  - Developers need quick idea capture (don't break flow)
  - Formal tasks require TDD discipline
  - Not all ideas become tasks

**Decision**:
Two task tiers:

1. **TIER 1**: Quick Capture (TODO_LIST.md)
   - Informal, no TDD required
   - Just capture the idea
   - Command: `/todo "description"`

2. **TIER 2**: Formal Tasks (ACTIVE_TASKS.md)
   - Requires: priority, estimate, acceptance criteria
   - Must follow TDD (RED → GREEN → REFACTOR)
   - Feature flags, traceability tags

**Rationale**:
- **Flexibility**: Not every idea needs formal process
- **Flow**: Quick capture doesn't interrupt work
- **Quality**: Formal tasks enforce discipline
- **Promotion**: Ideas can graduate to formal tasks

**Example**:
```
Quick Capture (5 seconds):
  /todo "add rate limiting"

Formal Task (5 minutes):
  ## Task #7: Add Rate Limiting to API

  **Priority**: High
  **Estimate**: 4 hours
  **Requirements**: REQ-NFR-DEMO-PERF-003
  **Acceptance Criteria**:
  - [ ] Rate limit: 100 req/min per IP
  - [ ] Tests for rate limiting
  - [ ] Graceful degradation
```

---

### ADR-003: Session Tracking (Git-Ignored)

**Context**:
- **Requirements**: REQ-F-WORKSPACE-003 (session tracking), REQ-NFR-CONTEXT-001 (persistent context)
- **Ecosystem Constraints**:
  - Sessions are personal/temporary (not shared)
  - Session history can get large (100s of sessions)
  - Team doesn't need my session notes

**Decision**:
- **Current session**: Git-ignored (`.ai-workspace/session/current_session.md`)
- **Session history**: Git-ignored (`.ai-workspace/session/history/`)
- **Session templates**: Version-controlled (`.ai-workspace/templates/SESSION_*.md`)

**Rationale**:
- Session notes are like IDE state (personal, not shared)
- Templates are shared (team conventions)
- Keeps repo clean (don't commit 100s of session files)

**Constraints Imposed**:
- Sessions don't sync across machines (local only)
- Must manually back up session history if needed
- Can't track team-wide session patterns

---

### ADR-004: Markdown Templates (Not Code Generation)

**Context**:
- **Requirements**: REQ-F-WORKSPACE-002 (templates)
- **Ecosystem Constraints**:
  - Developers use various editors (VSCode, Vim, Emacs)
  - Templates should work without special tools
  - LLMs can fill in markdown templates

**Decision**:
- **Format**: Markdown templates with placeholder sections
- **Mechanism**: Copy template, fill in sections
- **LLM-assisted**: AI helps fill templates (not just copy-paste)

**Rejected Alternatives**:
1. Code generation (Yeoman, plop) - Requires Node.js setup
2. Interactive CLI - Requires terminal prompts
3. Web forms - Requires server

**Rationale**:
- Markdown works everywhere
- LLMs excel at filling structured templates
- No tooling dependencies

**Example**:
```markdown
# Task: {TITLE}

## Problem
What needs to be solved?

## Solution
How will you solve it?

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

LLM fills in:
```markdown
# Task: Add Rate Limiting to API

## Problem
API has no rate limiting, vulnerable to abuse.

## Solution
Implement token bucket algorithm with Redis backend.

## Acceptance Criteria
- [ ] 100 req/min per IP address
- [ ] Graceful 429 responses
- [ ] Tests for rate limit enforcement
```

---

## 3. Workspace Structure

### 3.1 Directory Layout

```
.ai-workspace/
├── config/
│   └── workspace_config.yml          # Workspace configuration
├── session/
│   ├── current_session.md            # Active session (git-ignored)
│   └── history/                      # Past sessions (git-ignored)
│       └── YYYYMMDD_HHMM_*.md
├── tasks/
│   ├── todo/
│   │   └── TODO_LIST.md              # TIER 1: Quick capture
│   ├── active/
│   │   └── ACTIVE_TASKS.md           # TIER 2: Formal tasks
│   ├── finished/                     # TIER 3: Completed docs
│   │   └── YYYYMMDD_HHMM_*.md
│   └── archive/                      # Old completed tasks
│       └── YYYY/MM/
└── templates/
    ├── TASK_TEMPLATE.md              # Template for active tasks
    ├── FINISHED_TASK_TEMPLATE.md     # Template for finished tasks
    ├── SESSION_TEMPLATE.md           # Template for sessions
    ├── SESSION_STARTER.md            # Session kickoff guide
    └── PAIR_PROGRAMMING_GUIDE.md     # AI collaboration patterns
```

### 3.2 File Naming Conventions

**Finished Tasks**: `YYYYMMDD_HHMM_task_name.md`
- Example: `20251123_1430_add_rate_limiting.md`
- Sortable by timestamp
- Human-readable task name

**Session History**: `YYYYMMDD_HHMM_session.md`
- Example: `20251123_0900_session.md`
- Chronological order

**Archive**: `YYYY/MM/YYYYMMDD_HHMM_task_name.md`
- Example: `2025/11/20251123_1430_add_rate_limiting.md`
- Organized by year/month

---

## 4. Template Types

### 4.1 TASK_TEMPLATE.md (50 lines)

**Purpose**: Template for formal tasks in ACTIVE_TASKS.md

**Sections**:
- Task metadata (ID, priority, status, estimate)
- Requirements traceability (REQ-*)
- Description
- Acceptance criteria (checklist)
- TDD checklist (RED/GREEN/REFACTOR/COMMIT)
- Feature flag
- Dependencies

**Usage**:
```markdown
## Task #7: Add Rate Limiting to API

**Priority**: High
**Status**: Not Started
**Estimated Time**: 4 hours
**Requirements**: REQ-NFR-DEMO-PERF-003

**Acceptance Criteria**:
- [ ] Rate limit: 100 req/min per IP
- [ ] Tests pass (RED → GREEN → REFACTOR)
- [ ] Feature flag: rate-limiting-enabled

**TDD Checklist**:
- [ ] RED: Write failing test
- [ ] GREEN: Implement minimal solution
- [ ] REFACTOR: Improve code quality
- [ ] COMMIT: Finish task documentation
```

---

### 4.2 FINISHED_TASK_TEMPLATE.md (191 lines)

**Purpose**: Comprehensive documentation for completed tasks

**Sections** (12 major sections):
1. **Metadata**: Status, date, time, requirements
2. **Problem**: What was being solved
3. **Investigation**: Analysis performed
4. **Solution**: Architectural changes, TDD process
5. **Files Modified**: Changed files list
6. **Test Coverage**: Before/after metrics
7. **Feature Flag**: Rollout plan
8. **Code Changes**: Before/after examples
9. **Testing**: Manual testing, results
10. **Result**: Outcomes, metrics
11. **Side Effects**: Positive outcomes, considerations
12. **Future Considerations**: Follow-up tasks
13. **Lessons Learned**: What was learned
14. **Traceability**: Requirement coverage, commits
15. **Metrics**: Lines added, test coverage, performance
16. **Related**: Links to related tasks/issues

**Usage**: Creates comprehensive record of what was done, why, and what was learned.

**Value**:
- **Onboarding**: New team members read finished tasks
- **Context preservation**: Future you remembers decisions
- **Knowledge base**: Patterns emerge from lessons learned
- **Audit trail**: Requirement traceability

---

### 4.3 SESSION_TEMPLATE.md (95 lines)

**Purpose**: Track session goals, notes, decisions

**Sections**:
- Session metadata (date, time, duration)
- Goals (what to accomplish)
- Context (current state, blockers)
- Tasks worked on
- Decisions made
- Notes & discoveries
- Next session prep

**Usage**:
```markdown
# Dev Session - 2025-11-23

**Time**: 09:00 - 12:00 (3 hours)
**Focus**: Add rate limiting to API

## Goals
- [ ] Implement rate limiting (Task #7)
- [ ] Write tests for rate limiting
- [ ] Deploy to staging

## Tasks
- Task #7: Rate limiting (In Progress)

## Decisions
- Using Redis for distributed rate limiting
- Token bucket algorithm (100 req/min)

## Next Session
- Complete Task #7
- Start Task #8 (monitoring)
```

---

### 4.4 SESSION_STARTER.md (187 lines)

**Purpose**: Kickoff guide for starting a development session

**Sections**:
- Session kickoff checklist
- Context loading (review yesterday's work)
- Goal setting (what to accomplish today)
- Priority sorting
- Pair programming mode selection
- TDD workflow reminder

**Usage**: Run `/start-session` to load this guide

**Value**:
- **Consistency**: Same routine every session
- **Context switch**: Get into "the zone" faster
- **AI alignment**: Set expectations with AI assistant
- **Deliberate practice**: Reinforce TDD habits

---

### 4.5 PAIR_PROGRAMMING_GUIDE.md (271 lines)

**Purpose**: Patterns for effective human-AI collaboration

**Sections**:
1. **Three Pairing Modes**:
   - Human Driver / AI Navigator
   - AI Driver / Human Navigator
   - Collaborative (complex problems)

2. **Communication Patterns**:
   - Think aloud continuously
   - Check-in every 10-15 minutes
   - Clear handoffs between roles
   - Explicit approval for major changes

3. **Best Practices**:
   - AI writes tests first
   - Human reviews before commit
   - Rotate roles frequently
   - Document decisions

**Usage**: Reference when working with Claude Code or other AI assistants

**Value**:
- **Efficiency**: Clear division of labor
- **Quality**: Two sets of "eyes" on code
- **Learning**: AI explains, human understands
- **Safety**: Human reviews before commit

**Example**:
```
Human Driver / AI Navigator:
  Human: "I'll write the rate limiting logic"
  AI: "Consider edge cases: burst traffic, multiple IPs"
  Human: *writes code*
  AI: "Don't forget to update tests"
  Human: "Good catch, adding tests now"
```

---

## 5. Deployment Mechanism

### 5.1 Installer (setup_workspace.py)

**Location**: `installers/setup_workspace.py`

**Purpose**: Installs `.ai-workspace/` into target project

**Functionality**:
1. Validates target directory
2. Copies `templates/claude/.ai-workspace/` → `./.ai-workspace/`
3. Updates `.gitignore` (session/ directory)
4. Preserves existing tasks (if any)

**Usage**:
```bash
# Install workspace in current directory
python installers/setup_workspace.py

# Install in specific project
python installers/setup_workspace.py --target ../my-project

# Force reinstall (overwrites)
python installers/setup_workspace.py --force

# Skip .gitignore updates
python installers/setup_workspace.py --no-git
```

**Safety Features**:
- Checks if workspace already exists
- `--force` required to overwrite
- Backs up existing files before overwrite

---

### 5.2 Git Integration

**.gitignore entries**:
```gitignore
# AI SDLC Workspace - Local Session Data
.ai-workspace/session/current_session.md
.ai-workspace/session/history/
*.backup.*
```

**What's tracked**:
- ✅ `config/` - Workspace configuration
- ✅ `tasks/todo/` - Quick capture list
- ✅ `tasks/active/` - Formal tasks
- ✅ `tasks/finished/` - Completed task docs
- ✅ `tasks/archive/` - Old tasks
- ✅ `templates/` - Template files

**What's ignored**:
- ❌ `session/current_session.md` - Active session (personal)
- ❌ `session/history/` - Past sessions (personal)
- ❌ `*.backup.*` - Backup files

**Rationale**: Tasks are shared knowledge, sessions are personal context.

---

## 6. Integration with Commands

**Slash commands use templates**:

| Command | Template Used | Output |
|---------|---------------|--------|
| `/start-session` | SESSION_STARTER.md | Loads session kickoff guide |
| `/todo "description"` | (inline) | Adds to TODO_LIST.md |
| `/finish-task {id}` | FINISHED_TASK_TEMPLATE.md | Creates finished task doc |
| `/commit-task {id}` | (inline) | Generates commit message from finished task |

**Command integration design**: See [COMMAND_SYSTEM.md](COMMAND_SYSTEM.md) (to be created)

---

## 7. Quality Gates & Traceability

### 7.1 Template Quality

**Every template must**:
- ✅ Have clear section headers
- ✅ Include requirement traceability fields
- ✅ Provide acceptance criteria checklists
- ✅ Follow markdown formatting
- ✅ Include usage examples in comments

**Template validation**:
- Markdown lint (no broken formatting)
- Required sections present
- Placeholder text clearly marked

---

### 7.2 Traceability

**Templates → Requirements**:
- REQ-F-WORKSPACE-001 → .ai-workspace/ directory structure
- REQ-F-WORKSPACE-002 → TASK_TEMPLATE.md, FINISHED_TASK_TEMPLATE.md
- REQ-F-WORKSPACE-003 → SESSION_TEMPLATE.md, SESSION_STARTER.md
- REQ-NFR-CONTEXT-001 → Session persistence, task documentation

**Templates → Code**:
- TASK_TEMPLATE.md → tasks/active/ACTIVE_TASKS.md (in-use)
- FINISHED_TASK_TEMPLATE.md → tasks/finished/*.md (in-use)
- SESSION_TEMPLATE.md → session/current_session.md (in-use)

---

## 8. Implementation Status

### 8.1 Current Status

✅ **Implemented**:
- All 5 templates created (794 lines total)
- Workspace structure (.ai-workspace/)
- Installer (setup_workspace.py)
- Git integration (.gitignore)
- Documentation (README.md)

⚠️ **Partial**:
- Commands integration (templates exist, commands partial)

❌ **Not Implemented**:
- Template validation tool
- Automated archiving
- Template versioning

---

### 8.2 Code Artifacts

**Implemented**:
- `templates/claude/.ai-workspace/` - Complete workspace structure
- `templates/claude/.ai-workspace/templates/` - 5 templates (794 lines)
- `installers/setup_workspace.py` - Installer (150 lines)
- `.ai-workspace/` - Working example (this project)

**Tests**:
- No automated tests (manual validation only)

**Traceability**:
- REQ-F-WORKSPACE-001 → .ai-workspace/ structure ✅
- REQ-F-WORKSPACE-002 → TASK_TEMPLATE.md, FINISHED_TASK_TEMPLATE.md ✅
- REQ-F-WORKSPACE-003 → SESSION_TEMPLATE.md, SESSION_STARTER.md ✅
- REQ-NFR-CONTEXT-001 → Session persistence ✅

---

## 9. Comparison with External Tools

### 9.1 vs Jira/Linear

| Feature | .ai-workspace | Jira/Linear |
|---------|---------------|-------------|
| Cost | ✅ Free | ❌ $10-50/mo/user |
| Offline | ✅ Yes | ❌ No |
| Version control | ✅ Git | ⚠️ API/export |
| LLM-friendly | ✅ Markdown | ⚠️ API required |
| Setup time | ✅ 1 minute | ❌ Hours (org setup) |
| Search | ⚠️ grep/ripgrep | ✅ Full-text |
| Complex queries | ❌ Manual | ✅ JQL/filters |
| Team dashboards | ❌ No | ✅ Yes |
| Mobile app | ❌ No | ✅ Yes |

**Use .ai-workspace when**: Individual developer, offline work, Git-centric workflow

**Use Jira/Linear when**: Large teams, complex workflows, need dashboards/reports

---

### 9.2 vs Notion/Obsidian

| Feature | .ai-workspace | Notion | Obsidian |
|---------|---------------|--------|----------|
| Format | ✅ Plain markdown | ❌ Proprietary | ✅ Markdown |
| Git-friendly | ✅ Yes | ❌ No | ✅ Yes |
| Offline | ✅ Yes | ❌ No | ✅ Yes |
| Templates | ✅ Markdown | ✅ Rich | ✅ Markdown |
| Cost | ✅ Free | ⚠️ $8-15/mo | ⚠️ Free + $8/mo sync |
| AI integration | ✅ LLM-native | ⚠️ AI addon | ⚠️ Plugins |
| Structure | ✅ Prescribed | ❌ Free-form | ❌ Free-form |

**Use .ai-workspace when**: Developer workflow, TDD focus, Git integration critical

**Use Notion when**: Rich formatting, team wikis, cross-functional collaboration

**Use Obsidian when**: Personal knowledge management, graph view, plugins

---

## 10. Future Enhancements

### 10.1 Planned Features

**Short-term** (v1.1):
- [ ] Template validation tool (lint markdown, check sections)
- [ ] Automated archiving (move old finished tasks)
- [ ] Template versioning (track template changes)

**Mid-term** (v1.2):
- [ ] Task search tool (grep wrapper for common queries)
- [ ] Statistics (tasks completed, time estimates vs actual)
- [ ] Export to Jira/Linear (for team integration)

**Long-term** (v2.0):
- [ ] Web UI (view tasks in browser)
- [ ] Task dependencies graph
- [ ] Time tracking integration

---

## 11. References

**Requirements**:
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md)

**Related Design**:
- [Plugin Architecture](PLUGIN_ARCHITECTURE.md)
- [Command System](COMMAND_SYSTEM.md) (to be created)
- [AI SDLC UX Design](AI_SDLC_UX_DESIGN.md)

**Implementation**:
- [.ai-workspace/README.md](../../.ai-workspace/README.md)
- [templates/claude/.ai-workspace/](../../templates/claude/.ai-workspace/)
- [installers/setup_workspace.py](../../installers/setup_workspace.py)

**Templates** (794 lines total):
- TASK_TEMPLATE.md (50 lines)
- FINISHED_TASK_TEMPLATE.md (191 lines)
- SESSION_TEMPLATE.md (95 lines)
- SESSION_STARTER.md (187 lines)
- PAIR_PROGRAMMING_GUIDE.md (271 lines)

---

**Document Status**: Draft
**Next Review**: After Command System design (Task #3) completion
