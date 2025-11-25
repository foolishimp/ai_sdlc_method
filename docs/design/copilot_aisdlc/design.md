# Copilot AISDLC Design

Purpose
- Deliver the AI SDLC Method on GitHub Copilot (VS/VS Code) with parity to Claude and Codex while using Copilot-native prompts, snippets, and scripts.

Architecture Overview
- Workspace: Reuse `.ai-workspace/` structure and templates unchanged.
- Prompts/Personas: Stage prompt packs (requirements, design, tasks, code, system_test, uat, runtime) stored under `copilot/` and load shared instructions (Key Principles, TDD/BDD, REQ tagging).
- Snippets: Editor snippets for TDD/BDD scaffolds, telemetry with REQ tags, ADR stubs, task docs.
- Commands/Tasks: Helper scripts or tasks to run workspace ops (checkpoint, finish, release) callable from Copilot chat or command palette.
- Context: Quick-load reference set (method reference, traceability matrix, solution docs) for Copilot chat custom instructions.

Component Notes
- Plugin System: Package as VS/VS Code extensions or snippet packs; SemVer and dependency metadata should mirror Claude/Codex naming and ranges.
- Command System: Map Claude/Codex command behaviors to scripts/tasks (`copilot-sdlc-*` wrappers or VS tasks) and ensure idempotent file updates.
- Persona/Agent System: Prompts include stage role definitions, quality gates, and links to shared instructions; switching persona = loading a stage prompt pack.
- Skills: Implemented as curated prompts + snippets + helper scripts (traceability, testing, release, workspace, observability).
- Workspace System: No changes to layout; scripts validate structure before writing and avoid destructive edits.
- Traceability: Enforce REQ tagging in code/tests; provide prompts/scripts to refresh `docs/TRACEABILITY_MATRIX.md` using solution folders.
- Testing: Maintain ≥80% coverage (100% critical paths); snippets scaffold tests; scripts can run coverage and report deltas.
- Release: Provide script to perform version bump, changelog, and git tag, mirroring `/aisdlc-release`.

Traceability Hooks
- `requirements.yaml` enumerates covered REQ keys.
- This folder is the design anchor for the Copilot solution; ADRs capture platform decisions.
- Implementations live in `copilot-code/` (plugins/snippets/scripts) and should annotate code/tests with `# Implements: REQ-... via copilot_aisdlc` when relevant.

Operational Notes
- Copilot custom instructions should load the prompt pack and shared rules; include a quick command to refresh context (method references + active tasks).
- All scripts/updates must be repeatable; destructive actions require explicit flags.
- Keep parity with Claude/Codex; divergences must be ADR-documented.
