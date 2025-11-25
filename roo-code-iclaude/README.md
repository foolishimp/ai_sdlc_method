# Roo Code Assets (iclaude)

This directory mirrors `claude-code/` but targets Roo Code (formerly Roo Cline) native tooling, modes, and custom instructions.

**Note**: `iclaude` suffix indicates this implementation was created by Claude.

## Directory Structure

```
roo-code-iclaude/
├── plugins/               # Roo Code extension packages
│   ├── aisdlc-core/       # Core traceability and REQ tagging
│   ├── aisdlc-methodology/
│   ├── code-skills/
│   ├── design-skills/
│   ├── principles-key/
│   ├── python-standards/
│   ├── requirements-skills/
│   ├── runtime-skills/
│   ├── testing-skills/
│   └── bundles/           # Pre-configured Roo bundles
│       ├── startup-bundle/
│       ├── datascience-bundle/
│       ├── qa-bundle/
│       └── enterprise-bundle/
│
├── installers/            # Setup scripts for Roo Code projects
│
└── project-template/      # Template for Roo Code users
    ├── roo/               # Roo modes and custom instructions
    └── .ai-workspace/     # Shared workspace layout (same as Claude)
```

## Two Types of Assets

### 1) Plugins (Roo Code Extensions)

**Location:** `roo-code-iclaude/plugins/`
**Purpose:** Distribute AISDLC via Roo Code's extension/mode model.
**Usage:** Install via Roo Code settings; exposes custom modes for each SDLC stage and skills for traceability, testing, release, workspace, and observability.

Documentation: See `plugins/README.md` and solution design in `docs/design/roo_aisdlc/`.

### 2) Project Template (User Setup)

**Location:** `roo-code-iclaude/project-template/`
**Purpose:** Copy into new projects to enable AISDLC workflows in Roo Code.
**Contents:** Roo custom modes/instructions plus the shared `.ai-workspace/` structure.

Documentation: See `project-template/README.md`.

## Roo Code Architecture

Roo Code uses a different extension model than Claude Code:

| Concept | Claude Code | Roo Code |
|---------|-------------|----------|
| Personas | Agent markdown files | Custom Modes (JSON/YAML) |
| Commands | Slash commands (`/aisdlc-*`) | Mode-specific prompts |
| Skills | Plugin skills | Custom instructions per mode |
| Context | CLAUDE.md auto-load | .roo/rules/ or custom instructions |
| Workspace | `.ai-workspace/` | `.ai-workspace/` (shared) |

## Parity with Claude

- Same requirements, same workspace layout, same REQ tagging rules.
- Modes/instructions/skills are Roo-native; behavior mirrors Claude assets.
- Divergences must be documented in `docs/design/roo_aisdlc/adrs/`.

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| README.md | Done | This file |
| plugins/ | Placeholder | Directory structure with README stubs |
| installers/ | Placeholder | Setup scripts planned |
| project-template/ | Placeholder | Roo modes to be defined |
