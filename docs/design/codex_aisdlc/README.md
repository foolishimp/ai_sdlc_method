# Codex AISDLC Solution

Status: Draft (platform-aligned design for Codex)

Purpose
- Provide a Codex-native implementation of the AI SDLC Method, mirroring the Claude solution but optimized for Codex workflows and tooling.
- Preserve requirement traceability (REQ-F-*, REQ-NFR-*) while enabling multiple implementations alongside the Claude solution.

Scope
- Covers all implementation requirements from `docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` (see `requirements.yaml`).
- Targets the same 7-stage lifecycle with Codex-friendly commands, personas, and skills.

Key Differences vs Claude Solution
- Commands: CLI-friendly commands (no slash commands), packaged for Codex invocation (e.g., `codex-sdlc-*`).
- Personas: Stage personas provided as Codex presets/configs instead of Claude agent markdown.
- Skills: Modular Python entry points that Codex can call directly (no Claude plugin indirection).
- Context loading: Uses Codex config to auto-load method reference files and this solution folder.

Artifacts
- `requirements.yaml` – Requirements covered by this solution.
- `design.md` – Architecture and integration approach for Codex.
- `adrs/` – Platform-specific decisions for Codex packaging and invocation (see ADR-101+).

**Implementation**: `codex-code/` at project root (not in design folder)

Usage
- Use this folder as the authoritative design reference when building or invoking the Codex implementation of AISDLC.
- Keep links to REQ keys and ADRs updated as the Codex tooling evolves.
