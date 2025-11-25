# Codex Assets

This directory mirrors `claude-code/` but targets Codex-native tooling, packaging, and presets.

## Directory Structure

```
codex-code/
├── plugins/               # Codex extension packages (pip/entrypoints)
│   ├── aisdlc-core/       # Placeholder for core Codex package
│   ├── aisdlc-methodology/
│   ├── code-skills/
│   ├── design-skills/
│   ├── principles-key/
│   ├── python-standards/
│   ├── requirements-skills/
│   ├── runtime-skills/
│   ├── testing-skills/
│   └── bundles/           # Pre-configured Codex bundles
│       ├── startup-bundle/
│       ├── datascience-bundle/
│       ├── qa-bundle/
│       └── enterprise-bundle/
│
└── project-template/      # Template for Codex users (copied into projects)
    ├── codex/             # Codex configs/persona presets (mirrors .claude/)
    └── .ai-workspace/     # Shared workspace layout (same as Claude)
```

## Two Types of Assets

### 1) Plugins (Codex Extensions)

**Location:** `codex-code/plugins/`  
**Purpose:** Distribute AISDLC via Codex package/entrypoint model.  
**Usage:** Install via pip or Codex plugin loader; exposes commands (`codex-sdlc-*`) and skills (traceability, testing, release, workspace, observability).

Documentation: See `plugins/README.md` and solution design in `docs/design/codex_aisdlc/`.

### 2) Project Template (User Setup)

**Location:** `codex-code/project-template/`  
**Purpose:** Copy into new projects to enable AISDLC workflows in Codex.  
**Contents:** Codex persona/command configs plus the shared `.ai-workspace/` structure and guidance template.

Documentation: See `project-template/README.md`.

## Parity with Claude

- Same requirements, same workspace layout, same REQ tagging rules.
- Commands/presets/skills are Codex-native; behavior mirrors Claude assets.
- Divergences must be documented in `docs/design/codex_aisdlc/adrs/`.
