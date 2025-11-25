# Codex AISDLC Design

Purpose
- Deliver the AI SDLC Method on the Codex platform with parity to the Claude solution while keeping artifacts modular and platform-idiomatic.

Architecture Overview
- Workspace: Reuse `.ai-workspace/` structure and templates (tasks, sessions, config) unchanged.
- Commands: Provide Codex-friendly CLI commands (e.g., `codex-sdlc-context`, `codex-sdlc-checkpoint`, `codex-sdlc-release`) that read/write the same files targeted by Claude commands.
- Personas: Stage personas defined as Codex presets/configs (YAML/JSON) that inject shared context (requirements, Key Principles, TDD/BDD guides).
- Skills: Python entry points grouped by domain (traceability, testing, release, workspace, observability) callable by Codex; no reliance on Claude plugin APIs.
- Context: Bundled reference set (Key Principles, TDD workflow, AISDLC method reference, solution docs) auto-loaded via Codex configuration.

Component Notes
- Plugin System: Package commands/skills as a Codex extension (pip-installable) with metadata for discovery; maintain SemVer and dependency ranges mirroring `marketplace.json`.
- Command System: Map slash-command behaviors to CLI equivalents; ensure idempotent file updates (tasks, finished docs, changelog/tag generation).
- Agent/Persona System: Each stage preset links to requirements (`requirements.yaml`), quality gates, and the shared method docs; use prompt templates tailored for Codex.
- Workspace System: No changes to directory layout; commands must refuse to run if structure is missing or would be corrupted.
- Traceability: Enforce REQ tagging in code/tests; provide a Codex skill to regenerate `docs/TRACEABILITY_MATRIX.md` pulling solution paths (`docs/design/codex_aisdlc/*`) and implementations.
- Testing: Preserve coverage ≥80% (critical paths 100%); offer Codex skill to scaffold tests and report coverage deltas.
- Release: Provide CLI to perform version bump, changelog, and git tag creation for the Codex package, updating version references consistently.

Traceability Hooks
- Requirements: `requirements.yaml` enumerates the REQ keys covered.
- Design Artifacts: This folder (`docs/design/codex_aisdlc/`) serves as the design anchor for the Codex solution.
- ADRs: Platform decisions recorded under `adrs/` with links from README and relevant commands/skills.
- Implementations: When specific implementations exist, document them under `implementations/imp-codex_aisdlc-*.md` and annotate code/tests with `# Implements: REQ-... via codex_aisdlc`.

Operational Notes
- Context loading should be automatic for Codex sessions; fall back to a `codex-sdlc-context` command to reload method references and active tasks.
- All file-writing commands must be safe to run repeatedly (no destructive overwrites without backup/flags).
- Maintain alignment with the Claude solution; divergences should be ADR-backed and documented here.
