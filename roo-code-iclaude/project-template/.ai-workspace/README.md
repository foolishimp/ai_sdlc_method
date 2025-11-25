# AI Workspace (Roo Code)

This workspace structure is shared between Claude Code, Codex, and Roo Code implementations.

## Structure

```
.ai-workspace/
├── tasks/
│   ├── active/        # Current work items
│   │   └── ACTIVE_TASKS.md
│   ├── finished/      # Completed task documentation
│   └── archive/       # Historical tasks
├── templates/         # Document templates
├── config/            # Workspace configuration
└── session/           # Session state (if needed)
```

## Usage

Same rules apply regardless of AI coding tool:

1. **Check ACTIVE_TASKS.md** at start of each session
2. **Update task status** as work progresses
3. **Move completed tasks** to finished/ with documentation
4. **Tag all work** with REQ-* keys for traceability

## Cross-Tool Parity

| Aspect | Claude | Codex | Roo Code |
|--------|--------|-------|----------|
| Task location | Same | Same | Same |
| Task format | Same | Same | Same |
| REQ tagging | Same | Same | Same |
| Templates | Same | Same | Same |

Only the tool-specific configuration differs (`.claude/` vs `codex/` vs `.roo/`).
