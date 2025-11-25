# Copilot (VS) Assets

This directory mirrors `claude-code/` and `codex-code/`, targeting GitHub Copilot in Visual Studio/VS Code with AISDLC-aligned prompts, snippets, and helper scripts.

## Directory Structure

```
copilot-code/
├── plugins/               # Copilot extension scaffolds (prompt packs, snippets)
│   ├── aisdlc-core/
│   ├── aisdlc-methodology/
│   ├── code-skills/
│   ├── design-skills/
│   ├── principles-key/
│   ├── python-standards/
│   ├── requirements-skills/
│   ├── runtime-skills/
│   ├── testing-skills/
│   └── bundles/
│       ├── startup-bundle/
│       ├── datascience-bundle/
│       ├── qa-bundle/
│       └── enterprise-bundle/
│
├── project-template/      # Template for Copilot users (copilot config + workspace)
│   ├── copilot/           # Copilot chat prompts, instructions, snippet configs
│   └── .ai-workspace/     # Shared workspace layout (same as Claude/Codex)
│
└── installers/            # Placeholder for setup scripts (to mirror claude/codex)
```

## Purpose
- Provide Copilot chat prompt packs, snippets, and scripts that enforce the AISDLC methodology.
- Keep parity with Claude and Codex assets: same REQ tagging, Key Principles, TDD/BDD rules, workspace structure.
- Document any Copilot-specific behaviors in the companion design folder (`docs/design/copilot_aisdlc/`).

## Notes
- Behavior should mirror Claude/Codex; divergences must be ADR-documented under `docs/design/copilot_aisdlc/adrs/`.
- Workspace discipline (`.ai-workspace/`) and traceability rules remain unchanged.
