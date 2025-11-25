# ADR-101: Codex Command Layer Replaces Slash Commands

**Status**: accepted (implementation in progress)  
**Date**: 2025-11-26  
**Requirements**: REQ-F-CMD-001, REQ-NFR-CONTEXT-001, REQ-NFR-TRACE-001  
**Decision Drivers**: Codex has no native slash commands; commands must be callable via console entry points while writing to the shared `.ai-workspace/` structure and preserving REQ tagging.

## Context
- Claude’s `/aisdlc-*` slash commands cannot be invoked from Codex.
- We must keep behavior parity: workspace validation, task lifecycle updates, traceability enforcement, and release preflight.
- Codex discovery/installation will be driven by plugins listed in `marketplace.json` and installed via a Codex-friendly installer.

## Decision
- Provide CLI entry points named `codex-sdlc-*` (at minimum: `context`, `workspace`, `checkpoint`, `finish`, `commit`, `release`, `refresh`).
- Distribute these as console_scripts in the Codex methodology package (`codex-code/plugins/aisdlc-methodology`).
- Commands must be idempotent, operate on `.ai-workspace/` + `docs/TRACEABILITY_MATRIX.md`, and enforce REQ tags.
- Installer (`codex-code/installers/setup_commands.py`) will register configs/presets and validate command availability.

## Consequences
- Codex users invoke CLI instead of slash commands; behavior parity is preserved.
- Release automation (REQ-F-CMD-003) is staged via `codex-sdlc-release` with dry-run by default.
- Command telemetry and outputs must include REQ keys for traceability auditing.

## Workarounds (until implementation lands)
- Use Claude commands on the same workspace as a stopgap, or manually update `.ai-workspace/tasks/*` and `docs/TRACEABILITY_MATRIX.md` following the method reference.
- Document manual steps in `codex-code/project-template/README.md` until console scripts are wired.
