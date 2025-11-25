# ADR-102: Codex Stage Personas as Presets

**Status**: accepted (implementation pending)  
**Date**: 2025-11-26  
**Requirements**: REQ-F-CMD-002, REQ-NFR-TRACE-001, REQ-NFR-CONTEXT-001  
**Decision Drivers**: Codex lacks Claude agent markdown ingestion. We need stage personas that inject the same method reference, Key Principles, and stage-specific instructions.

## Context
- Claude uses `.claude/agents/aisdlc-*.md`; Codex needs its own preset format.
- Persona presets must load shared rules (Key Principles, TDD/BDD, req-tagging) and stage-specific quality gates.
- Presets should be copied with the project template and registered by an installer.

## Decision
- Store seven stage presets under `codex-code/project-template/codex/agents/` (JSON/YAML) with pointers to shared rules under `codex-code/project-template/codex/rules/`.
- Installer `setup_commands.py` (Codex) will place presets into the user’s Codex config path and validate references to rules and memory bank files.
- Presets must surface REQ tagging reminders and direct users to `.ai-workspace/tasks/active/ACTIVE_TASKS.md` on session start.

## Consequences
- Codex sessions can load the same lifecycle personas without relying on Claude agent files.
- Shared context (Key Principles, TDD/BDD workflows, feedback protocol) stays consistent across platforms.
- Traceability reminders are injected at persona load, reducing REQ-tag regressions.

## Workarounds (until presets exist)
- Manually paste the Claude agent content into Codex sessions for each stage, updating references from `.claude/` to `codex/` paths.
- For critical flows, include `CODEx.md` + method reference in the chat context to approximate persona loading.
