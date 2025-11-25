# Roo Code AISDLC Solution

Status: Draft (platform-aligned design for Roo Code)
Implementation: `roo-code-iclaude/` (iclaude = implemented by Claude)

## Purpose

- Provide a Roo Code-native implementation of the AI SDLC Method, mirroring the Claude solution but optimized for Roo Code workflows and tooling.
- Preserve requirement traceability (REQ-F-*, REQ-NFR-*) while enabling multiple implementations alongside Claude and Codex solutions.

## Scope

- Covers all implementation requirements from `docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` (see `requirements.yaml`).
- Targets the same 7-stage lifecycle with Roo Code custom modes, rules, and memory bank.

## Key Differences vs Claude Solution

| Aspect | Claude Code | Roo Code |
|--------|-------------|----------|
| **Personas** | Agent markdown files (`.claude/agents/`) | Custom Modes (`.roo/modes/` or `.roomodes`) |
| **Commands** | Slash commands (`/aisdlc-*`) | Mode-embedded instructions (no slash) |
| **Skills** | Plugin skills via markdown | Custom instructions in `.roo/rules/` |
| **Context** | `CLAUDE.md` auto-loaded | `.roo/rules/` + Memory Bank |
| **Configuration** | `.claude/settings.json` | Mode JSON/YAML definitions |

## Roo Code Architecture

### Custom Modes

Roo Code uses **Custom Modes** as the primary extension mechanism:

```json
{
  "slug": "aisdlc-code",
  "name": "AISDLC Code Agent",
  "roleDefinition": "You are the Code Agent following TDD workflow (RED-GREEN-REFACTOR)...",
  "groups": ["read", "edit", "command", "mcp"],
  "customInstructions": "Always tag code with REQ-* keys. Follow Key Principles."
}
```

### Custom Instructions (Rules)

Shared rules in `.roo/rules/` are referenced by modes:
- `key-principles.md` - The 7 Key Principles
- `tdd-workflow.md` - TDD cycle documentation
- `req-tagging.md` - REQ key format and usage
- `feedback-protocol.md` - Bidirectional feedback rules

### Memory Bank (Optional)

Persistent context in `.roo/memory-bank/`:
- `projectbrief.md` - Project overview
- `techstack.md` - Technology decisions
- `activecontext.md` - Current work items

## Artifacts

- `README.md` (this file) - Solution overview and scope
- `requirements.yaml` - Requirements covered by this solution
- `design.md` - Architecture and integration approach
- `AISDLC_IMPLEMENTATION_DESIGN.md` - Detailed implementation design
- `adrs/` - Platform-specific decisions (ADR-201+)

**Implementation**: `roo-code-iclaude/` at project root (not in design folder)

## Usage

- Use this folder as the authoritative design reference when building or invoking the Roo Code implementation of AISDLC.
- Keep links to REQ keys and ADRs updated as the Roo Code tooling evolves.
- Implementation code lives in `roo-code-iclaude/` at project root.
