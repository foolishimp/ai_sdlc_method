# ADR-104: Codex Context Auto-Loading and Workspace Guardrails

**Status**: accepted (implementation pending)  
**Date**: 2025-11-26  
**Requirements**: REQ-F-WORKSPACE-001/002/003, REQ-NFR-CONTEXT-001, REQ-NFR-TRACE-001  
**Decision Drivers**: Codex must reliably load method references, rules, and active tasks while preventing corruption of the shared `.ai-workspace/` artifacts.

## Context
- Claude auto-loads `CLAUDE.md` and agent files; Codex needs an equivalent mechanism to load method references, rules, and active tasks.
- Workspace integrity (tasks/active, finished, templates) is critical; commands must be safe/idempotent and enforce REQ tagging.

## Decision
- Provide a `codex-sdlc-context` command that:
  - Loads reference set: `CODEX.md`, `docs/design/codex_aisdlc/*`, Key Principles, TDD/BDD guides, req-tagging, workspace safeguards.
  - Surfaces `.ai-workspace/tasks/active/ACTIVE_TASKS.md` and refuses to proceed if missing.
  - Prints current stage/persona hints and REQ tagging reminders.
- Guardrail: all `codex-sdlc-*` commands validate workspace structure before writes; if missing, they exit with instructions to run `setup_workspace.py`.
- Federated loading: prefer project-level Codex configs, fall back to global Codex config (mirroring Claude override order).

## Consequences
- Codex sessions start with consistent context, reducing drift from Claude behavior.
- Workspace safety is enforced at the command layer; accidental overwrites are prevented.
- REQ tagging is reinforced at every command invocation.

## Workarounds (until implemented)
- Manually open `CODEX.md`, `.ai-workspace/tasks/active/ACTIVE_TASKS.md`, and rules under `codex-code/project-template/codex/rules/` at session start.
- Use Claude commands on the same workspace as a fallback while Codex commands are built.
