# AI SDLC Method Implementation Design (Codex Solution)

Document Type: Design Synthesis  
Solution: `codex_aisdlc` (Codex-native)  
Status: Draft  
Date: 2025-11-25

## Purpose
Describe how the AI SDLC Method is delivered on Codex, mirroring the Claude solution while using Codex-native commands, personas, and skills. This design covers all implementation requirements listed in `requirements.yaml`.

## Executive Summary
The Codex solution delivers the same 7-stage methodology (Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback) via:
- **CLI Command Layer**: Codex-friendly commands (`codex-sdlc-*`) replacing slash commands while writing to the shared workspace.
- **Persona Presets**: Stage personas shipped as Codex configs (YAML/JSON) that load shared context (Key Principles, TDD, BDD, REQ keys).
- **Skills Library**: Python entry points for traceability, testing, release, workspace management, and observability—callable directly by Codex.
- **Context Bundle**: Auto-loaded reference set (method reference, principles, workflow guides, solution docs) declared in Codex config.
- **Workspace Parity**: `.ai-workspace/` structure and templates remain the canonical storage for tasks, sessions, and finished docs.

## Architecture Overview
1) **Plugin/Extension Packaging (REQ-F-PLUGIN-001/002/003/004)**
   - Packaged as a pip-installable Codex extension with SemVer and dependency metadata.
   - Supports federated composition via Codex config layers (global → project), matching override rules from the Claude solution.
2) **Command System (REQ-F-CMD-001/003)**
   - Command set: `codex-sdlc-context`, `codex-sdlc-checkpoint`, `codex-sdlc-finish`, `codex-sdlc-commit`, `codex-sdlc-release`, `codex-sdlc-refresh`.
   - Commands are idempotent and target the same files as Claude (`.ai-workspace/*`, `docs/TRACEABILITY_MATRIX.md`, `marketplace.json` for version updates).
   - Release flow mirrors `/aisdlc-release` (preflight, bump, changelog, tag, summary).
3) **Persona/Agent System (REQ-F-CMD-002)**
   - Stage presets stored as Codex configs under `codex/agents/` (not in repo yet); each preset loads REQ keys, quality gates, and the method reference.
   - Personas inject stage-specific prompts plus shared Key Principles/TDD/BDD rules.
4) **Skills (Reusable Capabilities)**
   - Domains: `traceability`, `testing`, `workspace`, `release`, `observability`.
   - Each skill is a Python entry point Codex can call with arguments (no Claude plugin wrappers).
   - Traceability skill can regenerate matrix rows using `requirements.yaml` and solution folders.
5) **Workspace System (REQ-F-WORKSPACE-001/002/003)**
   - No structural changes; commands enforce presence of `.ai-workspace/tasks`, `templates`, `config`.
   - Task/finished/session templates reused from repo; commands refuse destructive rewrites.
6) **Testing & Coverage (REQ-F-TESTING-001/002, REQ-NFR-COVERAGE-001)**
   - Skills expose coverage checks (≥80% default, 100% on critical paths) and test scaffolding.
   - BDD/System Test/UAT support via Gherkin scaffolds and validation rules.
7) **Traceability (REQ-NFR-TRACE-001/002, REQ-NFR-CONTEXT-001)**
   - Commands/skills enforce REQ tagging in code/tests and can refresh `docs/TRACEABILITY_MATRIX.md`.
8) **Iterative Refinement (REQ-NFR-REFINE-001)**
   - Feedback loop supported via persona presets and release/runbook guidance; ADRs capture platform-specific refinements.

## Design Artifacts
- `README.md` (this folder) – solution overview and scope.
- `requirements.yaml` – REQ coverage for this solution.
- `design.md` – high-level architecture and component notes.
- `adrs/` – Codex-specific decisions (starts at ADR-101).

**Implementation**: `codex-code/` at project root (not in design folder)

## Implementation Notes
- Packaging: Python package with entry points for commands and skills; Codex config lists commands/personas and auto-loads context docs.
- Configuration: Global + project-level config mirrors the federated model; later layers override earlier ones.
- Safety: Commands are repeatable and avoid destructive changes; backups optional for release operations.
- Alignment: Maintain parity with `docs/design/claude_aisdlc/*`; any divergence must be ADR-documented and reflected in traceability.
