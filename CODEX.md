# CODEX.md - ai_sdlc_method Configuration

Guidance for Codex when working in this repository. Follow the AI SDLC methodology and keep requirement traceability intact.

## Context to Load First
- Read `docs/design/codex_aisdlc/README.md` for the Codex-specific solution overview.
- Check `.ai-workspace/tasks/active/ACTIVE_TASKS.md` for current work; do not bypass this file.
- Keep `.ai-workspace/templates/AISDLC_METHOD_REFERENCE.md` handy for recovery and workflow guardrails.
- Codex solution design lives in `docs/design/codex_aisdlc/` (implementation design, architecture, ADRs).
- Methodology reference configs live in `claude-code/plugins/aisdlc-methodology/config/` (`stages_config.yml`, `config.yml`).

## Non-Negotiable Rules
- Practice TDD: RED -> GREEN -> REFACTOR -> COMMIT. No code without tests.
- Minimum coverage: 80% overall, aim for 100% on critical paths (see `.ai-workspace/config/workspace_config.yml` and REQ-NFR-COVERAGE-001).
- Tag work with requirement keys (REQ-F-*, REQ-NFR-*, REQ-DATA-*). In code use inline comments such as `# Implements: REQ-F-...`; in tests `# Validates: ...`.
- Maintain the 7-stage flow: Requirements -> Design -> Tasks -> Code -> System Test (BDD) -> UAT -> Runtime Feedback. Close the loop when runtime issues appear.
- Apply the Seven Questions (CLAUDE.md, Section “Before You Code”); stop if any answer is “no.”
- Preserve the workspace structure; do not relocate task/session files or bypass the supplied templates.

## Working Pattern
1) Recover context: `git status`, read ACTIVE_TASKS, skim recent session notes if present in `.ai-workspace/session/`.
2) Align to stage: identify the current SDLC stage and persona implied by the task; pull details from `docs/requirements/AI_SDLC_REQUIREMENTS.md` and `docs/design/codex_aisdlc/AISDLC_IMPLEMENTATION_DESIGN.md` as needed.
3) Requirements & design: ensure REQ keys exist and designs map to them (`docs/TRACEABILITY_MATRIX.md` shows coverage). If missing, create/clarify before coding.
4) Code stage: write failing tests first, implement minimally, refactor, then commit with REQ tags. Follow quality standards from `claude-code/plugins/aisdlc-methodology/config/config.yml`.
5) System Test/UAT: express behavior in Given/When/Then when applicable and map scenarios to REQ keys.
6) Runtime feedback: if touching release/telemetry paths, tag metrics/alerts with REQ keys and update feedback docs if they exist.
7) Document progress: update tasks via the active task file (respecting its format) and keep finished artifacts under `.ai-workspace/tasks/finished/` when closing work.

## References to Consult
- Codex solution design: `docs/design/codex_aisdlc/` (README.md, AISDLC_IMPLEMENTATION_DESIGN.md, design.md, adrs/).
- Methodology: `docs/requirements/AI_SDLC_REQUIREMENTS.md`, `docs/requirements/AI_SDLC_OVERVIEW.md`, `docs/ai_sdlc_method.md` (complete spec).
- Implementation requirements and traceability: `docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`, `docs/TRACEABILITY_MATRIX.md`.
- Process and principles: `claude-code/plugins/aisdlc-methodology/docs/processes/TDD_WORKFLOW.md`, `.../principles/KEY_PRINCIPLES.md`.
- Workspace rules and templates: `.ai-workspace/README.md`, `.ai-workspace/config/workspace_config.yml`, `.ai-workspace/templates/*.md`.

## Collaboration Notes
- Prefer small, traceable changes; keep provenance by referencing REQ IDs in commits and summaries.
- If context is missing or ambiguous, pause to gather from the docs above before proceeding.
- Avoid altering marketplace or plugin metadata unless a task explicitly targets them.

