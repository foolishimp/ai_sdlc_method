# Copilot Plugins (Prompt Packs & Snippets)

Purpose
- Copilot-native distribution of AISDLC personas, prompts, and snippets.
- Mirrors the Claude/Codex plugin sets; packaged as VS/VS Code prompt packs or snippet extensions.

Structure
```
copilot-code/plugins/
├── aisdlc-core/
├── aisdlc-methodology/
├── principles-key/
├── python-standards/
├── code-skills/
├── design-skills/
├── requirements-skills/
├── runtime-skills/
├── testing-skills/
└── bundles/
    ├── startup-bundle/
    ├── datascience-bundle/
    ├── qa-bundle/
    └── enterprise-bundle/
```

Packaging Model
- VS/VS Code extension scaffolds or snippet packs.
- Content includes:
  - Chat presets (stage personas) referencing shared instructions.
  - Snippets for TDD/BDD scaffolds, telemetry with REQ tags, ADR stubs, traceability checks.
  - Helper commands (tasks/release) wired to scripts in `project-template` or repo scripts.

Alignment & Docs
- Behavior mirrors Claude/Codex; differences must be ADR-documented (`docs/design/copilot_aisdlc/adrs/`).
- See `docs/design/copilot_aisdlc/` for design/implementation guidance.
