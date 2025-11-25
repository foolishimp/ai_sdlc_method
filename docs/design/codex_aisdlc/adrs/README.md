# Codex AISDLC ADRs

Platform-specific decisions for the Codex implementation of the AI SDLC Method. Use these to record deviations or extensions from the Claude solution.

Conventions
- Numbering starts at ADR-101 to avoid collision with Claude ADRs.
- Each ADR must cite the relevant REQ IDs (see `requirements.yaml`) and link back to this solution folder.
- Status values: proposed, accepted, superseded, deprecated.

Seed Decisions (to author as they are finalized)
- ADR-101: Codex CLI commands replace slash commands for workflow automation.
- ADR-102: Codex persona presets for SDLC stages (requirements, design, tasks, code, system_test, uat, runtime).
- ADR-103: Packaging Codex skills as a pip-installable extension with SemVer and dependency metadata.
- ADR-104: Context auto-loading strategy for Codex sessions (reference set + workspace validation).
