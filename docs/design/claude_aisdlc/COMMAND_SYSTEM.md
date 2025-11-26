# Command System Design (v0.4)

**Version**: 0.4.0
**Date**: 2025-11-27
**Status**: Implemented
**ADR Reference**: [ADR-002-commands-for-workflow-integration](adrs/ADR-002-commands-for-workflow-integration.md)

---

## Overview

The AISDLC command system provides workflow automation through Claude Code's native slash command mechanism. Commands are markdown files in `.claude/commands/` that instruct Claude to perform structured operations on the workspace.

**Philosophy**: Commands should eliminate context-switching between AI conversation and external tools. Every command must solve real workflow friction.

---

## Command Evolution

| Version | Command Count | Change |
|---------|---------------|--------|
| v0.1.0 | 16 | Initial exploratory set |
| v0.1.3 | 10 | Removed context switching commands (5) |
| v0.1.4 | 6 | Removed persona commands (4) - vestigial |
| v0.3.0 | 6 | Stabilized MVP command set |
| **v0.4.0** | **7** | Added `aisdlc-update` for framework updates |

**Key Insight**: Fewer, essential commands > many optional commands.

---

## Final Command Set (v0.4)

```
claude-code/plugins/aisdlc-methodology/commands/
├── aisdlc-checkpoint-tasks.md   # Sync task state with conversation
├── aisdlc-commit-task.md        # Generate REQ-tagged commit message
├── aisdlc-finish-task.md        # Complete task with documentation
├── aisdlc-refresh-context.md    # Reload methodology into context
├── aisdlc-release.md            # Create project release with changelog
├── aisdlc-status.md             # Show task queue snapshot
└── aisdlc-update.md             # Update framework from GitHub
```

---

## Command Specifications

### 1. `/aisdlc-status` - Task Queue Snapshot

**Purpose**: Quick visibility into work state without leaving conversation.

**Decision Rationale**:
- Developers constantly need to know: What's active? What's done?
- Traditional: `git status`, open Jira, check TODO app = 3 context switches
- With command: Single query, full picture in conversation

**Implements**: REQ-F-TODO-003, REQ-F-CMD-001

**Behavior**:
1. Read `.ai-workspace/tasks/active/ACTIVE_TASKS.md`
2. Count and list active tasks
3. List last 5 finished tasks from `.ai-workspace/tasks/finished/`
4. Display formatted summary with suggestion

**Design Choice**: Read-only, no side effects. Safe to run anytime.

---

### 2. `/aisdlc-checkpoint-tasks` - Task State Synchronization

**Purpose**: Update task status based on actual conversation work.

**Decision Rationale**:
- AI conversation naturally produces work (code, tests, fixes)
- Task state can drift from reality during long sessions
- Manual status updates = forgotten or inconsistent
- Checkpoint analyzes conversation → updates tasks automatically

**Implements**: REQ-F-WORKSPACE-002, REQ-NFR-CONTEXT-001

**Behavior**:
1. Analyze conversation history for completed work
2. For each active task, determine: Completed | In Progress | Blocked | Not Started
3. Move completed tasks to `.ai-workspace/tasks/finished/` with documentation
4. Update remaining task status in `ACTIVE_TASKS.md`
5. Report summary

**Design Choice**: Context-aware. Uses conversation history, not just file state.

---

### 3. `/aisdlc-finish-task {task_id}` - Task Completion

**Purpose**: Explicitly complete a task with full documentation.

**Decision Rationale**:
- Finished tasks are valuable documentation
- Captures: problem, investigation, solution, TDD process, metrics
- Alternative: Tasks disappear with no record → lost institutional knowledge
- Finish creates permanent artifact in `tasks/finished/`

**Implements**: REQ-F-CMD-001

**Behavior**:
1. Find task in `ACTIVE_TASKS.md`
2. Verify completion criteria met (tests passing, acceptance criteria)
3. Create finished task document from template
4. Remove from active tasks
5. Confirm with file path

**Design Choice**: Explicit action (not automatic) because completion requires validation.

---

### 4. `/aisdlc-commit-task {task_id}` - REQ-Tagged Commits

**Purpose**: Generate commit message with requirement traceability.

**Decision Rationale**:
- Commits should link back to requirements (REQ-F-*, REQ-NFR-*)
- Manual commit messages: inconsistent, missing tags
- Command reads finished task → generates structured message
- Enforces: TDD notation, requirement keys, Claude co-authorship

**Implements**: REQ-F-CMD-001, REQ-NFR-TRACE-001

**Behavior**:
1. Find finished task document in `.ai-workspace/tasks/finished/`
2. Extract: title, problem, solution, tests, REQ keys
3. Generate commit message with format:
   ```
   Task #{id}: {title}

   {problem summary}
   {solution summary}

   Tests: {test_summary}
   TDD: RED → GREEN → REFACTOR

   Implements: {REQ keys}

   🤖 Generated with [Claude Code](https://claude.ai/code)
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
4. Show message, get approval
5. Execute git commit

**Design Choice**: Requires finished task document. Don't commit work without documentation.

---

### 5. `/aisdlc-refresh-context` - Methodology Reload

**Purpose**: Restore Claude's awareness of AISDLC methodology.

**Decision Rationale**:
- Long conversations cause context drift
- Claude may forget workspace structure, critical rules, workflow
- Alternative: Repeat methodology in every message → wasteful
- Refresh loads method reference + validates workspace

**Implements**: REQ-F-CMD-001

**Behavior**:
1. Read `.ai-workspace/templates/AISDLC_METHOD_REFERENCE.md`
2. Verify workspace structure exists
3. Check active tasks
4. Output confirmation with critical rules reminder
5. Ask what to work on

**Design Choice**: Idempotent. Safe to run multiple times. No side effects.

---

### 6. `/aisdlc-release` - Project Release Management

**Purpose**: Create versioned releases with changelog.

**Decision Rationale**:
- Projects need versioned releases for deployment/distribution
- Manual: determine version, write changelog, create tag = error-prone
- Command automates: version bump, changelog from commits, git tag
- Follows SemVer (major.minor.patch)

**Implements**: REQ-F-CMD-003

**Behavior**:
1. Validate: no uncommitted changes, on main branch
2. Get current version from git tags
3. Auto-bump build number (patch): vX.Y.Z → vX.Y.Z+1
4. Generate changelog from git log since last tag
5. Create annotated git tag
6. Report with next steps (push tag, create GitHub release)

**Design Choice**: Auto-bumps patch only. Major/minor requires manual tag.

**Safety**: Local only. Does not push. User reviews before publishing.

---

### 7. `/aisdlc-update` - Framework Updates

**Purpose**: Update project's AISDLC framework from GitHub.

**Decision Rationale**:
- Framework evolves independently of projects using it
- Manual: clone repo, copy files, merge changes = tedious
- Command fetches latest release → updates framework files
- Preserves: active tasks, finished tasks, project-specific config

**Implements**: REQ-F-UPDATE-001

**Behavior**:
1. Determine target version (latest tag or specified)
2. Create backup in `/tmp/aisdlc-backup-{project}-{timestamp}/`
3. Shallow clone from GitHub
4. Update: templates, commands, agents, CLAUDE.md (framework sections)
5. Preserve: active tasks, finished tasks, project-specific CLAUDE.md sections
6. Validate update
7. Report with rollback instructions

**Design Choice**: Backup first. Never loses work. Preserves customizations.

---

## Removed Commands

### Context Switching Commands (removed v0.1.3)

```
aisdlc-set-context.md        # Switch between projects
aisdlc-save-context.md       # Save current context
aisdlc-restore-context.md    # Restore saved context
aisdlc-list-contexts.md      # List available contexts
aisdlc-clear-context.md      # Clear current context
```

**Removal Rationale**:
- Over-engineered for MVP
- Claude Code's session model handles context naturally
- Adding complexity without solving real friction
- Context = conversation history (already persistent)

### Persona Commands (removed v0.1.4)

```
aisdlc-apply-persona.md      # Apply stage persona
aisdlc-list-personas.md      # List available personas
aisdlc-persona-checklist.md  # Show persona checklist
aisdlc-switch-persona.md     # Switch to different persona
```

**Removal Rationale**:
- Vestigial from earlier design
- Personas implemented via agents (`.claude/agents/*.md`), not commands
- REQ-F-CMD-002 (persona management) fulfilled by agent system
- Commands were duplicating agent functionality

### TODO Command (removed v0.1.4)

```
aisdlc-todo.md               # Add quick TODO
```

**Removal Rationale**:
- Replaced by Claude's native TodoWrite tool
- Better integration with Claude's task tracking
- Redundant with tool-based approach

---

## Command Design Principles

### 1. Workflow Integration Over Tool Replacement

Commands integrate git, task management, and documentation into conversation flow. They don't replace external tools; they bridge AI conversation to them.

**Example**:
```
Without: Leave Claude → terminal → git commit → return → re-explain context
With: /aisdlc-commit-task 5 → Claude handles git, maintains context
```

### 2. Stateful Awareness

Commands know what you're working on by reading workspace files:
- `ACTIVE_TASKS.md` for current work
- `tasks/finished/` for completed work
- Conversation history for context

**Example**: `/aisdlc-checkpoint-tasks` analyzes what you discussed → updates task state

### 3. Safe by Default

- Read-only commands (status, refresh-context) have no side effects
- Write commands (checkpoint, finish, commit, release) require confirmation
- Update command creates backup before changes
- No command auto-pushes to remote

### 4. Minimal Surface Area

**7 commands total**. Each solves distinct workflow friction:

| Friction | Command |
|----------|---------|
| "What am I working on?" | `/aisdlc-status` |
| "Did I complete anything?" | `/aisdlc-checkpoint-tasks` |
| "This task is done" | `/aisdlc-finish-task` |
| "Time to commit" | `/aisdlc-commit-task` |
| "Claude forgot methodology" | `/aisdlc-refresh-context` |
| "Time to release" | `/aisdlc-release` |
| "Framework is outdated" | `/aisdlc-update` |

### 5. Namespace Safety

All commands prefixed `aisdlc-` to avoid conflicts with:
- User's custom commands
- Other methodology plugins
- Future Claude Code built-in commands

---

## Command Format

Commands are markdown files with this structure:

```markdown
# Command title and usage

<!-- Implements: REQ-F-* (requirement traceability) -->

**Usage**: `/command-name [arguments]`

## Instructions

[Step-by-step instructions for Claude to execute]

## Example

[Example session showing command usage]
```

### Format Decisions

1. **Markdown, not code**: Commands are prompts, not scripts. Claude interprets and executes.
2. **HTML comments for traceability**: `<!-- Implements: REQ-* -->` parsed by traceability tools
3. **Usage line**: Clear invocation syntax
4. **Numbered steps**: Claude follows sequentially
5. **Examples**: Show expected behavior

---

## Installation

Commands are installed via `installers/setup_commands.py`:

```python
# Source: claude-code/plugins/aisdlc-methodology/commands/
# Target: .claude/commands/

# Copies all command files to project
# ~50 lines of Python
# Idempotent (can re-run safely)
```

---

## Requirement Traceability

| Command | Requirements |
|---------|-------------|
| aisdlc-status | REQ-F-TODO-003, REQ-F-CMD-001 |
| aisdlc-checkpoint-tasks | REQ-F-WORKSPACE-002, REQ-NFR-CONTEXT-001 |
| aisdlc-finish-task | REQ-F-CMD-001 |
| aisdlc-commit-task | REQ-F-CMD-001, REQ-NFR-TRACE-001 |
| aisdlc-refresh-context | REQ-F-CMD-001 |
| aisdlc-release | REQ-F-CMD-003 |
| aisdlc-update | REQ-F-UPDATE-001 |

---

## Metrics

- **Total commands**: 7
- **Average lines per command**: ~60
- **Total command lines**: ~420
- **Commands removed**: 9 (56% reduction from v0.1.0)
- **Installation code**: ~50 lines

---

## Future Considerations

### Potential Additions (if proven need)

| Command | Use Case | Decision |
|---------|----------|----------|
| `/aisdlc-sync-jira` | Two-way Jira sync | Defer until Jira integration requested |
| `/aisdlc-test` | Run project tests | Defer - use native `pytest` via Bash |
| `/aisdlc-deploy` | Trigger deployment | Defer - CI/CD handles this |

### Stability Commitment

The v0.4 command set is **stable for MVP**. Changes require:
1. Demonstrated workflow friction
2. No existing command/tool solution
3. ADR documenting decision

---

## References

- [ADR-002: Commands for Workflow Integration](adrs/ADR-002-commands-for-workflow-integration.md)
- [ADR-001: Claude Code as MVP Platform](adrs/ADR-001-claude-code-as-mvp-platform.md)
- [REQ-F-CMD-001: Slash Commands for Workflow](../../requirements/AI_SDLC_REQUIREMENTS.md)
- [Claude Code Slash Commands](https://docs.anthropic.com/claude-code/commands)
