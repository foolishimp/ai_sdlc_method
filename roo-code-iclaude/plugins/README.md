# Roo Code Plugins (Extensions)

Purpose
- Roo Code-native distribution of the AISDLC methodology, skills, and standards.
- Mirrors the Claude plugin set but ships as Roo custom modes with instructions.

Structure
```
roo-code-iclaude/plugins/
├── aisdlc-core/           # Foundation (traceability, REQ tagging)
├── aisdlc-methodology/    # 7-stage method + personas as modes
├── principles-key/        # Key Principles enforcement
├── python-standards/      # Language standards (example)
├── code-skills/           # Coding/refactoring helpers
├── design-skills/         # Design/ADR helpers
├── requirements-skills/   # Requirements helpers
├── runtime-skills/        # Runtime/telemetry helpers
├── testing-skills/        # TDD/BDD helpers
└── bundles/               # startup/datascience/qa/enterprise bundles
```

## Roo Code Mode Model

Roo Code uses **Custom Modes** instead of slash commands:

### Mode Structure
Each SDLC stage becomes a custom mode with:
- **Name**: `aisdlc-<stage>` (e.g., `aisdlc-requirements`, `aisdlc-code`)
- **Instructions**: Stage-specific prompts and quality gates
- **Tools**: Allowed operations (read, write, execute, browser)
- **File patterns**: Relevant file types for the stage

### Example Mode Definition
```json
{
  "slug": "aisdlc-code",
  "name": "AISDLC Code Agent",
  "instructions": "You are the Code Agent following TDD workflow...",
  "groups": ["read", "edit", "command"],
  "source": "project"
}
```

## Packaging Model

- Modes defined in `.roo/modes/` or `.roomodes` file
- Custom instructions in `.roo/rules/` directory
- Skills as reusable instruction snippets
- SemVer tracking via plugin metadata
- Layered configuration: global → project (later overrides earlier)

## Commands Mapping

| Claude Command | Roo Equivalent |
|----------------|----------------|
| `/aisdlc-checkpoint-tasks` | Mode instruction + manual trigger |
| `/aisdlc-finish-task` | Mode instruction + manual trigger |
| `/aisdlc-commit-task` | Mode instruction + manual trigger |
| `/aisdlc-status` | Mode instruction + manual trigger |
| `/aisdlc-release` | Mode instruction + manual trigger |

## Alignment & Docs

- Behavior mirrors Claude plugins; differences must be ADR-documented (`docs/design/roo_aisdlc/adrs/`).
- See `docs/design/roo_aisdlc/` for design and implementation guidance.
