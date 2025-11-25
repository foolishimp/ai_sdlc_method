# ADR-201: Custom Modes for Stage Personas

## Status

Accepted

## Context

The AI SDLC methodology requires 7 stage-specific personas (Requirements, Design, Tasks, Code, System Test, UAT, Runtime Feedback) that guide AI behavior during each SDLC phase. In Claude Code, these are implemented as agent markdown files in `.claude/agents/`. For Roo Code, we need an equivalent mechanism.

Roo Code provides **Custom Modes** as its extensibility mechanism. A custom mode consists of:
- `slug`: Unique identifier
- `name`: Human-readable name
- `roleDefinition`: System prompt defining persona behavior
- `groups`: Tool categories enabled (read, edit, command, mcp, browser)
- `customInstructions`: Additional instructions loaded into context

### Requirements Addressed

- REQ-F-CMD-002: Persona Management (Agents)
- REQ-F-PLUGIN-001: Plugin Packaging
- REQ-F-PLUGIN-002: Federated Plugin Loading

### Options Considered

1. **Single .roomodes file**: All 7 modes in one JSON array file
2. **Individual mode files**: Separate `.roo/modes/aisdlc-*.json` files
3. **Hybrid approach**: Base modes in .roomodes, overrides in modes/

## Decision

Use **Option 2: Individual mode files** stored in `.roo/modes/`.

Each SDLC stage gets its own mode file:
```
.roo/
└── modes/
    ├── aisdlc-requirements.json
    ├── aisdlc-design.json
    ├── aisdlc-tasks.json
    ├── aisdlc-code.json
    ├── aisdlc-system-test.json
    ├── aisdlc-uat.json
    └── aisdlc-runtime.json
```

### Mode File Structure

```json
{
  "slug": "aisdlc-code",
  "name": "AISDLC Code Agent",
  "roleDefinition": "You are the Code Agent for Stage 4 of the AI SDLC...",
  "groups": ["read", "edit", "command"],
  "customInstructions": "@rules/key-principles.md\n@rules/tdd-workflow.md\n@rules/req-tagging.md"
}
```

### Tool Group Assignments

| Mode | Groups | Rationale |
|------|--------|-----------|
| requirements | read, browser | Research, no code modification |
| design | read, edit | Create design docs, no execution |
| tasks | read, edit | Create task docs, no execution |
| code | read, edit, command | Full development capability |
| system-test | read, edit, command | Run tests, create test code |
| uat | read, browser | Business validation, no code |
| runtime | read, edit, command, mcp | Full ops capability including MCP |

## Consequences

### Positive

- **Modularity**: Each mode is independently versioned and updatable
- **Clarity**: Mode purpose is obvious from filename
- **Parity**: Maps cleanly to Claude's `.claude/agents/aisdlc-*.md` structure
- **Customization**: Users can override individual modes without touching others
- **Testability**: Each mode can be validated independently

### Negative

- **More files**: 7 files vs 1 for .roomodes approach
- **Consistency risk**: Modes might drift if not validated together
- **Discovery**: Users must know to look in `.roo/modes/`

### Mitigations

- Installer validates all 7 modes are present and consistent
- README documents mode locations and purpose
- Validation script checks mode structure against schema

## References

- REQ-F-CMD-002: Persona Management (Agents)
- REQ-F-PLUGIN-001: Plugin Packaging
- Claude agent files: `.claude/agents/aisdlc-*.md`
- Roo Code custom modes documentation
