# Roo Code Config (Project Template)

Copy this directory to `.roo/` in your project to enable AISDLC workflows in Roo Code.

## Structure

```
.roo/
├── modes/                 # Custom mode definitions (7 SDLC stages)
│   ├── aisdlc-requirements.json
│   ├── aisdlc-design.json
│   ├── aisdlc-tasks.json
│   ├── aisdlc-code.json
│   ├── aisdlc-system-test.json
│   ├── aisdlc-uat.json
│   └── aisdlc-runtime.json
│
├── rules/                 # Shared instructions (loaded by modes)
│   ├── key-principles.md      # 7 Key Principles
│   ├── tdd-workflow.md        # RED-GREEN-REFACTOR cycle
│   ├── bdd-workflow.md        # Given/When/Then patterns
│   ├── req-tagging.md         # REQ-* format and usage
│   ├── feedback-protocol.md   # Bidirectional feedback
│   └── workspace-safeguards.md # Safety rules
│
└── memory-bank/           # Persistent context
    ├── projectbrief.md        # Project goals and scope
    ├── techstack.md           # Technology decisions
    ├── activecontext.md       # Current work focus
    └── methodref.md           # AISDLC quick reference
```

## Installation

1. Copy this `roo/` directory to `.roo/` in your project root
2. Copy `.ai-workspace/` from project-template to your project root
3. Edit memory bank files with your project details
4. Start Roo Code and select an AISDLC mode

## Mode Activation

Switch SDLC stages by activating modes in Roo Code's mode selector:

| Mode | Stage | When to Use |
|------|-------|-------------|
| `aisdlc-requirements` | 1 | Gathering and documenting requirements |
| `aisdlc-design` | 2 | Creating architecture and design docs |
| `aisdlc-tasks` | 3 | Breaking work into tasks |
| `aisdlc-code` | 4 | Implementing with TDD |
| `aisdlc-system-test` | 5 | Writing BDD integration tests |
| `aisdlc-uat` | 6 | Business validation |
| `aisdlc-runtime` | 7 | Production monitoring and feedback |

## Tool Groups

Each mode enables specific tool capabilities:

| Mode | read | edit | command | browser | mcp |
|------|------|------|---------|---------|-----|
| requirements | ✓ | | | ✓ | |
| design | ✓ | ✓ | | | |
| tasks | ✓ | ✓ | | | |
| code | ✓ | ✓ | ✓ | | |
| system-test | ✓ | ✓ | ✓ | | |
| uat | ✓ | | | ✓ | |
| runtime | ✓ | ✓ | ✓ | | ✓ |

## Rules Loading

Modes load rules via `@rules/<filename>` syntax:
```json
{
  "customInstructions": "@rules/key-principles.md\n@rules/tdd-workflow.md"
}
```

## Memory Bank

Memory bank files are auto-loaded for persistent context:
- Update `projectbrief.md` when project scope changes
- Update `techstack.md` when technology decisions change
- Update `activecontext.md` at start/end of each session

## Customization

### Modify Mode Behavior
Edit mode JSON files to:
- Change roleDefinition for different persona style
- Add/remove tool groups
- Include additional rules

### Add Custom Rules
Create new `.md` files in `rules/` and reference via `@rules/`

### Extend Memory Bank
Add new `.md` files for additional persistent context

## Parity with Claude/Codex

This configuration provides equivalent functionality to:
- Claude Code: `.claude/agents/` and slash commands
- Codex: CLI commands and persona presets

Same workspace structure (`.ai-workspace/`) used across all tools.

## Design Reference

See `docs/design/roo_aisdlc/` for:
- AISDLC_IMPLEMENTATION_DESIGN.md - Full design
- ADRs - Platform decisions (ADR-201+)
- requirements.yaml - REQ coverage
