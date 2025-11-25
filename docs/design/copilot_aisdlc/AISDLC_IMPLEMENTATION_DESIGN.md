# AI SDLC Method Implementation Design (Copilot Solution)

Document Type: Design Synthesis  
Solution: `copilot_aisdlc` (Copilot-native)  
Status: Draft  
Date: 2025-11-25

## Purpose
Describe how the AI SDLC Method is delivered in GitHub Copilot (VS/VS Code), mirroring Claude and Codex while using Copilot-native prompts, snippets, and helper scripts. Covers all implementation requirements listed in `requirements.yaml`.

## Executive Summary
The Copilot solution delivers the 7-stage methodology via:
- **Prompt Packs (Personas)**: Stage-specific prompt sets that inject Key Principles, TDD/BDD rules, and REQ-tagging guidance.
- **Snippets/Tasks**: Editor snippets for TDD/BDD scaffolds, telemetry with REQ tags, ADR stubs, and task docs; tasks/scripts to run workspace operations (checkpoint, finish, release).
- **Context Bundle**: Quick-load references (method reference, traceability matrix, solution docs) surfaced via Copilot custom instructions.
- **Workspace Parity**: `.ai-workspace/` structure and rules identical to Claude/Codex solutions.

## Architecture Overview
1) **Plugin/Extension Packaging (REQ-F-PLUGIN-001/002/003/004)**
   - VS/VS Code extension or snippet pack with SemVer and dependency metadata mirroring Claude/Codex names.
   - Layered configuration via project/user settings; later overrides earlier (e.g., project prompt pack overrides user defaults).

2) **Command System (REQ-F-CMD-001/003)**
   - Replace slash commands with scripts/tasks (e.g., `copilot-sdlc-context`, `copilot-sdlc-checkpoint`, `copilot-sdlc-finish`, `copilot-sdlc-commit`, `copilot-sdlc-release`, `copilot-sdlc-refresh`).
   - Commands are idempotent and target the same files: `.ai-workspace/*`, `docs/TRACEABILITY_MATRIX.md`, `marketplace.json` for version updates.
   - Release flow mirrors `/aisdlc-release`: preflight (clean git), version bump, changelog, tag, summary.

3) **Persona/Agent System (REQ-F-CMD-002)**
   - Stage prompts stored in `copilot/` (project template) and referenced by Copilot custom instructions.
   - Each prompt includes stage role, gates, and shared rules (Key Principles, TDD/BDD, REQ tagging).

4) **Skills (Reusable Capabilities)**
   - Delivered as curated prompts + scripts/snippets:
     - Traceability: validate REQ tags, regenerate matrix rows from `requirements.yaml` and solution folders.
     - Testing: scaffold unit/BDD tests, run coverage, enforce thresholds.
     - Workspace: validate layout, create finished task docs, checkpoint tasks.
     - Release: version bump, changelog, git tagging.
     - Observability: insert telemetry/logging with REQ tags; stub alerts.

5) **Workspace System (REQ-F-WORKSPACE-001/002/003)**
   - No layout changes; scripts refuse to run if structure is missing or would be corrupted.
   - Task/session templates reused from repo; destructive rewrites forbidden without explicit flags.

6) **Testing & Coverage (REQ-F-TESTING-001/002, REQ-NFR-COVERAGE-001)**
   - Coverage ≥80% (100% critical paths); snippets embed coverage reminders.
   - BDD/System Test/UAT support via Gherkin scaffolds tied to REQ keys.

7) **Traceability (REQ-NFR-TRACE-001/002, REQ-NFR-CONTEXT-001)**
   - Enforce REQ tagging in code/tests via prompts/snippets; scripts can refresh `docs/TRACEABILITY_MATRIX.md`.
   - Implementations in `copilot-code/` should annotate code with `# Implements: REQ-... via copilot_aisdlc`.

8) **Iterative Refinement (REQ-NFR-REFINE-001)**
   - Feedback loop supported via prompts and release/runbook guidance; ADRs capture platform-specific refinements.

## Design Artifacts
- `README.md`, `requirements.yaml`, `design.md` (this folder).
- `adrs/` (start at ADR-301) for Copilot platform decisions.

## Implementation Notes
- Packaging: Extension/snippet pack + optional scripts; document install steps in `copilot-code/README.md`.
- Configuration: User + workspace settings; project prompt packs override user defaults.
- Safety: Scripts repeatable; backups optional for release operations; no destructive edits by default.
- Alignment: Maintain parity with Claude/Codex; divergences must be ADR-documented and reflected in traceability.
