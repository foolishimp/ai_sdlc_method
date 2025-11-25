# Codex Project Template

Purpose
- Starter kit for using the AI SDLC Method in Codex.
- Mirrors the Claude project template but uses Codex configs/persona presets while reusing the same `.ai-workspace/` layout.

Contents
```
codex-code/project-template/
├── codex/                 # Codex configs (commands/personas/hooks) — add per project
└── .ai-workspace/         # Workspace structure (tasks, templates, config)
    ├── tasks/
    ├── templates/
    └── config/
```

How to Use
- Copy `.ai-workspace/` into your project (or install via Codex installer once available).
- Add a `codex/` directory with:
  - Persona presets (stage configs)
  - Command definitions mapping to `codex-sdlc-*` entrypoints
  - Optional hooks (pre-commit, context indicators)
- Use `CLAUDE.md` equivalent guidance from `docs/design/codex_aisdlc/` to brief Codex.

Notes
- Workspace rules (task/session/finished locations) stay identical to Claude.
- REQ tagging, coverage targets, and TDD/BDD expectations are unchanged.
- Keep project-specific overrides documented and traceable to REQ IDs.
