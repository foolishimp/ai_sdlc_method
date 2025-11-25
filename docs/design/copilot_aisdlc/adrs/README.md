# Copilot AISDLC ADRs

Platform-specific decisions for the Copilot implementation of the AI SDLC Method. Use these to record deviations or extensions from Claude/Codex.

Conventions
- Numbering starts at ADR-301 to avoid collision with Claude/Codex ADRs.
- Each ADR must cite the relevant REQ IDs (see `requirements.yaml`) and link back to this solution folder.
- Status values: proposed, accepted, superseded, deprecated.

Seed Decisions (to author as they are finalized)
- ADR-301: Copilot prompt packs and snippets replace slash/CLI persona switching.
- ADR-302: Copilot tasks/scripts as equivalents to AISDLC commands (checkpoint, finish, release).
- ADR-303: Packaging as VS/VS Code extension/snippet pack with SemVer and dependency metadata.
- ADR-304: Context loading strategy for Copilot custom instructions (method references + workspace validation).
