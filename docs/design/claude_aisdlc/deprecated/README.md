# Deprecated Design Documents

These design documents were created during earlier development phases and have been superseded by the comprehensive stage-based design documents.

## Deprecated Files

| File | Reason | Replaced By |
|------|--------|-------------|
| `AI_SDLC_UX_DESIGN.md` | Exploratory UX design (Nov 2025) | Stage-specific design documents |
| `AGENTS_SKILLS_INTEROPERATION.md` | Covered by new AI augmentation design | `AI_AUGMENTATION_DESIGN.md` |
| `CLAUDE_AGENTS_EXPLAINED.md` | Covered by new AI augmentation design | `AI_AUGMENTATION_DESIGN.md` |
| `COMMAND_SYSTEM.md` | Tooling-focused, now part of REQ-TOOL-* | Stage designs cover tooling |
| `FOLDER_BASED_ASSET_DISCOVERY.md` | Tooling-focused, covered by REQ-TOOL-002 | Tooling in stage designs |
| `HOOKS_SYSTEM.md` | Tooling-focused, covered by REQ-TOOL-008 | Tooling in stage designs |
| `PLUGIN_ARCHITECTURE.md` | Tooling-focused, covered by REQ-TOOL-001 | Tooling in stage designs |
| `TEMPLATE_SYSTEM.md` | Tooling-focused, covered by REQ-TOOL-002 | Tooling in stage designs |

## Current Design Structure

The current design documents follow the 7-stage SDLC methodology:

```
docs/design/claude_aisdlc/
├── AISDLC_IMPLEMENTATION_DESIGN.md   # Synthesis document
├── INTENT_MANAGEMENT_DESIGN.md       # REQ-INTENT-*
├── WORKFLOW_STAGE_DESIGN.md          # REQ-STAGE-*
├── REQUIREMENTS_STAGE_DESIGN.md      # REQ-REQ-*
├── DESIGN_STAGE_DESIGN.md            # REQ-DES-*
├── TASKS_STAGE_DESIGN.md             # REQ-TASK-*
├── CODE_STAGE_DESIGN.md              # REQ-CODE-*
├── SYSTEM_TEST_STAGE_DESIGN.md       # REQ-SYSTEST-*
├── UAT_STAGE_DESIGN.md               # REQ-UAT-*
├── RUNTIME_FEEDBACK_DESIGN.md        # REQ-RUNTIME-*
├── TRACEABILITY_DESIGN.md            # REQ-TRACE-*
├── AI_AUGMENTATION_DESIGN.md         # REQ-AI-*
├── adrs/                             # Architecture Decision Records
└── deprecated/                       # This folder
```

## When to Reference Deprecated Docs

These documents may still be useful for:
- Understanding historical design decisions
- Reviewing exploratory UX concepts
- Reference for tooling implementation details

However, for current requirements traceability and implementation, use the stage-based design documents.

---

**Deprecated**: 2025-12-03
