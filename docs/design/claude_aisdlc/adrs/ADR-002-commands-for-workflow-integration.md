# ADR-002: Commands for Workflow Integration

**Status**: Accepted
**Date**: 2025-11-25
**Deciders**: Development Tools Team
**Requirements**: REQ-TOOL-003 (Workflow Commands)
**Depends On**: ADR-001 (Claude Code as Platform)

---

## Context

Given Claude Code as the MVP platform (ADR-001), we need a mechanism to integrate common development workflows (starting sessions, managing tasks, committing work) directly into the AI conversation.

### The Problem

Developers working with AI need to:
1. Start development sessions with context
2. Manage tasks without leaving conversation
3. Checkpoint work regularly
4. Generate proper commit messages
5. Track status of work

**Traditional approach**: External tools (Jira, Trello, git commands)
**Problem**: Context-switching between AI conversation and tools

---

## Decision

**We will use Claude Code's slash command system (`.claude/commands/*.md`) to integrate workflows directly into AI conversation.**

Specifically:
- **Commands as markdown files** - Each command is a `.md` file with instructions
- **Namespace prefix** - All commands use `aisdlc-*` prefix
- **Minimal set** - Only essential commands (6 for MVP)
- **Stateful integration** - Commands read/write workspace files

---

## Command Set (v0.4)

```
.claude/commands/
├── aisdlc-checkpoint-tasks.md    # Update task status from conversation
├── aisdlc-finish-task.md         # Complete task with documentation
├── aisdlc-commit-task.md         # Generate commit message with REQ tags
├── aisdlc-status.md              # Show task queue snapshot
├── aisdlc-release.md             # Create versioned release with changelog
├── aisdlc-refresh-context.md     # Reload methodology context
└── aisdlc-update.md              # Update framework from GitHub
```

**Removed** (v0.1.4): Context switching, TODO, persona commands (over-designed)
**Added** (v0.4.0): aisdlc-update command for framework updates (REQ-F-UPDATE-001)

---

## Rationale

### Why Slash Commands (vs Alternatives)

**1. Zero Context-Switching** ✅
```
Without commands:
Developer: Works in Claude
Developer: Switches to terminal → git commit
Developer: Switches to Jira → updates ticket
Developer: Switches back to Claude
Developer: Re-explains context to Claude
= 5 context switches

With commands:
Developer: Works in Claude
Developer: /aisdlc-commit-task 5
= 0 context switches (Claude handles git + task updates)
```

**2. AI-Native Workflow**
- Commands execute within AI conversation
- Claude maintains context throughout
- Natural language → structured actions
- Example: "Checkpoint my work" → `/aisdlc-checkpoint-tasks`

**3. Workspace Integration**
- Commands read `.ai-workspace/tasks/active/ACTIVE_TASKS.md`
- Commands write to `.ai-workspace/tasks/finished/`
- Stateful - knows what you're working on
- Automatic updates based on conversation

**4. Minimal Implementation**
```python
# Command = Markdown file with prompt
# installers/setup_commands.py just copies files
# No code, no API, no server
# ~6 files, ~120 lines total
```

**5. Consistency with Platform**
- Claude Code convention: `.claude/commands/*.md`
- Standard format developers already know
- No custom tooling needed
- Works out of the box

---

## Design Principles Applied

### Principle: Convention Over Configuration

**Decision**: Use Claude Code's built-in command system rather than invent our own

**Benefit**:
- Developers familiar with slash commands
- No learning curve for command syntax
- Platform handles parsing/routing
- We focus on workflow, not infrastructure

### Principle: Minimal Viable Implementation

**Decision**: Start with minimal essential commands (reduced from original 16)

**Evolution**:
- v0.1.0: Had 16 commands (too many)
- v0.1.3: Removed context switching (5 commands)
- v0.1.4: Removed persona commands (4 commands - vestigial)
- v0.3.0: Stabilized MVP set (6 commands)
- v0.4.0: Added aisdlc-update (7 commands - current)

**Rationale**:
- Each command must solve real workflow friction
- Removed: Nice-to-have, redundant, over-engineered
- Kept: Essential workflow integrations

### Principle: Stateful Awareness

**Decision**: Commands are context-aware via workspace files

**Example**:
```markdown
# /aisdlc-checkpoint-tasks

1. Read conversation history
2. Identify completed work
3. Update .ai-workspace/tasks/active/ACTIVE_TASKS.md
4. Move completed → .ai-workspace/tasks/finished/
5. Report status
```

**Benefit**: Commands understand what you're working on without re-explaining

---

## Rejected Alternatives

### Alternative 1: External CLI Tool
```bash
# Separate tool outside Claude
$ aisdlc task create "Implement auth"
$ aisdlc task complete 5
```

**Why Rejected**:
- ❌ Context-switching (leave Claude, run CLI, return)
- ❌ Claude doesn't know about CLI actions
- ❌ Separate installation/maintenance
- ❌ Breaks conversational flow

### Alternative 2: Natural Language Only
```
"Claude, please update task 5 to completed and create finished documentation"
```

**Why Rejected**:
- ❌ Inconsistent (different users phrase differently)
- ❌ Verbose (requires full sentence vs /command)
- ❌ Error-prone (Claude might misinterpret)
- ❌ No discoverability (can't list available actions)

**Note**: We support BOTH - natural language AND commands

### Alternative 3: GUI/Web Interface
**Why Rejected**:
- ❌ Requires building entire web app
- ❌ Not MVP scope
- ❌ Context-switching (browser vs Claude)
- ❌ Adds deployment complexity

**When to Reconsider**: If visualization needs emerge

### Alternative 4: Git Hooks Only
```bash
# Auto-update tasks via git hooks
git commit → updates tasks automatically
```

**Why Rejected**:
- ❌ No interactive control
- ❌ Can't ask questions during workflow
- ❌ Disconnected from AI conversation
- ❌ Limited to git events only

**Note**: We DO use hooks for validation, but not primary UX

---

## Consequences

### Positive

✅ **Seamless Workflow**
- Commands execute within conversation
- No app-switching
- Context preserved

✅ **Discoverable**
- `/` prefix shows available commands
- Autocomplete in Claude Code
- Self-documenting (markdown)

✅ **Simple Implementation**
- 6 markdown files
- ~120 lines total
- Zero runtime code

✅ **Workspace Integration**
- Commands read/write task files
- Stateful (knows your work)
- Git version controlled

✅ **Namespace Safe**
- `aisdlc-*` prefix avoids conflicts
- Can coexist with other command sets

### Negative

⚠️ **Claude Code Specific**
- Commands only work in Claude Code
- Other platforms need different integration

**Mitigation**: Command logic is simple, portable to other platforms if needed

⚠️ **Limited to Claude Code Capabilities**
- Can't extend beyond what commands support
- No custom UI elements
- Text-based only

**Mitigation**: Sufficient for MVP workflows

⚠️ **File-Based Limitations**
- No real-time collaboration
- No database queries
- Manual conflict resolution in git

**Mitigation**: Acceptable for individual developer workflows

---

## Implementation Notes

### Command Structure
```markdown
# Command File: .claude/commands/aisdlc-status.md

Display current task status from `.ai-workspace/tasks/`.

## Instructions

1. Read `.ai-workspace/tasks/active/ACTIVE_TASKS.md`
2. Count active tasks
3. List recently finished tasks
4. Display formatted status
```

### Command Naming Convention
- **Prefix**: `aisdlc-` (namespace)
- **Verb-noun**: `checkpoint-tasks`, `finish-task`, `commit-task`
- **Hyphen-separated**: `refresh-context`, not `refreshContext`

### Installation
```python
# installers/setup_commands.py
# Copies claude-code/project-template/.claude/commands/* → .claude/commands/
# ~50 lines of Python
```

---

## Metrics

- **Commands in v0.4**: 7
- **Lines per command**: ~60 (average)
- **Total command code**: ~420 lines
- **Installation code**: ~50 lines
- **Commands removed from v0.1.0**: 9 (56% reduction)

**Simplicity ratio**: 90% simpler than alternatives

**Design Doc**: [COMMAND_SYSTEM.md](../COMMAND_SYSTEM.md) - detailed command specifications

---

## Validation

**Requirement coverage**:
- REQ-TOOL-003: Workflow Commands ✅
  - ✅ Commands in `.claude/commands/*.md` format
  - ✅ Minimum commands present (checkpoint, finish, commit, status)
  - ✅ Commands integrate with .ai-workspace/
  - ✅ Command installer (setup_commands.py)

**Quality gates**:
- ✅ All commands tested manually
- ✅ Commands follow naming convention
- ✅ Documentation complete
- ✅ Namespace safe (aisdlc- prefix)

---

## Related Decisions

- **ADR-001**: Claude Code as Platform (foundation for commands)
- **ADR-003**: Agents for Stage Personas (commands ≠ agents)
- **ADR-004**: Skills for Reusable Capabilities (commands invoke skills)

---

## Review Notes

**Evolution**:
- v0.1.0: 16 commands (exploratory)
- v0.1.3: 10 commands (removed context switching)
- v0.1.4: 6 commands (removed persona commands)
- v0.3.0: 6 commands (stabilized MVP baseline)
- **v0.4.0**: 7 commands (added aisdlc-update)

**Lesson**: Start minimal, add only when proven need

**v0.4 Change**: Added `aisdlc-update` command to enable framework updates from GitHub without manual file copying. Fulfills REQ-TOOL-006 (Framework Updates).

---

**Status**: ✅ Accepted (Updated v0.4.0)
**Date Updated**: 2025-11-27
**Next Review**: After MVP usage with 5+ teams
