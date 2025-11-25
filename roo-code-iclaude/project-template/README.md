# Roo Code Project Template

Purpose
- Starter kit for using the AI SDLC Method in Roo Code.
- Mirrors the Claude project template but uses Roo custom modes/instructions while reusing the same `.ai-workspace/` layout.

## Contents

```
roo-code-iclaude/project-template/
├── roo/                   # Roo Code configs (modes/rules/memory)
│   ├── modes/             # Custom mode definitions
│   ├── rules/             # Custom instructions (shared across modes)
│   └── memory-bank/       # Optional persistent context
│
└── .ai-workspace/         # Workspace structure (shared with Claude)
    ├── tasks/
    │   ├── active/
    │   ├── finished/
    │   └── archive/
    ├── templates/
    ├── config/
    └── session/
```

## How to Use

1. **Copy workspace**: Copy `.ai-workspace/` into your project
2. **Add Roo config**: Copy `roo/` directory to `.roo/` in your project
3. **Configure modes**: Edit mode files in `.roo/modes/` as needed
4. **Add rules**: Customize instructions in `.roo/rules/`
5. **Optional memory**: Use `.roo/memory-bank/` for persistent context

## Roo-Specific Setup

### Custom Modes (`.roo/modes/` or `.roomodes`)

Each SDLC stage has a dedicated mode:
- `aisdlc-requirements` - Requirements Agent persona
- `aisdlc-design` - Design Agent persona
- `aisdlc-tasks` - Tasks Agent persona
- `aisdlc-code` - Code Agent persona (TDD focus)
- `aisdlc-system-test` - System Test Agent persona (BDD)
- `aisdlc-uat` - UAT Agent persona
- `aisdlc-runtime` - Runtime Feedback Agent persona

### Custom Instructions (`.roo/rules/`)

Shared rules loaded across modes:
- `key-principles.md` - The 7 Key Principles
- `tdd-workflow.md` - RED-GREEN-REFACTOR cycle
- `req-tagging.md` - REQ-* key format and propagation
- `feedback-protocol.md` - Bidirectional feedback rules

### Memory Bank (`.roo/memory-bank/`)

Optional persistent context:
- `projectbrief.md` - Project overview and goals
- `techstack.md` - Technology decisions
- `activecontext.md` - Current work context

## Notes

- Workspace rules (task/session/finished locations) stay identical to Claude
- REQ tagging, coverage targets, and TDD/BDD expectations are unchanged
- Keep project-specific overrides documented and traceable to REQ IDs
- Use `CLAUDE.md` equivalent guidance from `docs/design/roo_aisdlc/` to brief Roo
