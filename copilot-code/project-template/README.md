# Copilot Project Template

Purpose
- Starter kit for using the AI SDLC Method with GitHub Copilot (VS/VS Code).
- Mirrors Claude/Codex templates while providing Copilot prompts/snippets.

Contents
```
copilot-code/project-template/
├── copilot/               # Copilot chat prompts, instructions, snippet configs
└── .ai-workspace/         # Workspace structure (tasks, templates, config)
    ├── tasks/
    ├── templates/
    └── config/
```

How to Use
- Copy `.ai-workspace/` into your project (reuse existing templates).
- Add `copilot/` files to your repo or user settings to load stage prompts/snippets.
- Use the same REQ tagging, coverage, and TDD/BDD rules as Claude/Codex.

Notes
- Workspace rules stay identical; do not relocate task/session/finished files.
- Keep project-specific overrides documented and traceable to REQ IDs.
