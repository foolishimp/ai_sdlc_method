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

Platform Mapping (Design Resolutions)
- Agents/Personas → Codex presets under `codex/project-template/codex/agents/` (ADR-102); loaded via installer and surfaced by `codex-sdlc-context`.
- Commands → Console scripts `codex-sdlc-*` (ADR-101) for context, workspace setup, checkpoint/finish/commit, release, refresh; idempotent writes to `.ai-workspace/` and `docs/TRACEABILITY_MATRIX.md`.
- Plugins/Skills → Codex packages with `.codex-plugin/plugin.json` (`*-codex` names) registered in `marketplace.json` (ADR-103); dependencies use Codex suffix to avoid cross-platform collisions.
- Federated loading → Global Codex config overridden by project config, matching Claude precedence (documented/validated by installers and ADR-104 guardrails).
- Traceability → `codex-sdlc-validate` (future) regenerates/validates REQ tags and matrix rows; all commands emit REQ reminders (ADR-104).
- Release → `codex-sdlc-release` mirrors Claude flow (preflight, SemVer bump, changelog, annotated tag) with dry-run default.
- Quality gates → Coverage ≥80% enforced via command preflights; workspace integrity checks block destructive writes (ADR-104).

Worked Example (TDD Cycle via Codex)
1) Run `codex-sdlc-context` to load references and print ACTIVE_TASKS; exits if `.ai-workspace/` is missing.
2) Start Code stage preset (Codex agent) which loads Key Principles, TDD rules, req-tagging reminders.
3) Run `codex-sdlc-checkpoint --task TASK-123 --req REQ-F-AUTH-001` to log intent and prepare workspace notes.
4) Write failing test; tag with `# Validates: REQ-F-AUTH-001`.
5) Implement minimal code; tag with `# Implements: REQ-F-AUTH-001`.
6) Run `codex-sdlc-commit --task TASK-123 --req REQ-F-AUTH-001` to record status, update traceability matrix, and suggest commit message.
7) If releasing, run `codex-sdlc-release --dry-run` to preflight SemVer bump and changelog before tagging.

Traceability Hooks
- Requirements: `requirements.yaml` enumerates the REQ keys covered.
- Design Artifacts: This folder (`docs/design/codex_aisdlc/`) serves as the design anchor for the Codex solution.
- ADRs: Platform decisions recorded under `adrs/` with links from README and relevant commands/skills.
- Implementations: When specific implementations exist, document them under `implementations/imp-codex_aisdlc-*.md` and annotate code/tests with `# Implements: REQ-... via codex_aisdlc`.

Operational Notes
- Context loading should be automatic for Codex sessions; fall back to a `codex-sdlc-context` command to reload method references and active tasks.
- All file-writing commands must be safe to run repeatedly (no destructive overwrites without backup/flags).
- Maintain alignment with the Claude solution; divergences should be ADR-backed and documented here.
