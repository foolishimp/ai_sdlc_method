# Plugin/Extension Architecture (Codex Solution)

Purpose
- Define how the AISDLC method is packaged and loaded in Codex, mirroring Claude’s plugin approach while using Codex-native extension points.

Packaging
- Python package (pip) with entry points:
  - Commands: `codex-sdlc-context`, `codex-sdlc-checkpoint`, `codex-sdlc-finish`, `codex-sdlc-commit`, `codex-sdlc-release`, `codex-sdlc-refresh`.
  - Skills: `traceability`, `testing`, `workspace`, `release`, `observability`.
- Metadata: SemVer, dependencies, and compatibility declared similarly to `marketplace.json`.
- Composition: Supports layered configs (global → project) with override precedence matching Claude’s federated model.

Loading & Context
- Codex config points to:
  - Command entry points
  - Persona presets (stage configs)
  - Context bundle (method reference, principles, TDD, solution docs)
- On session start, context is auto-loaded; a manual `codex-sdlc-context` refreshes if needed.

Traceability Integration
- Skills read `requirements.yaml` and solution folders to map REQ → design → implementation.
- Release tooling updates version references and can emit traceability deltas.

Safety & Idempotency
- Commands/skills avoid destructive edits; backups or `--force` flags required for risky operations.
- Validation steps precede writes (workspace structure, clean git state for release).

Alignment
- Behavior should mirror the Claude plugin set; any divergence requires an ADR entry in `adrs/`.
