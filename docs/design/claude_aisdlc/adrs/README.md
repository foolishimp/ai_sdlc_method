# Architecture Decision Records (ADRs)

**Purpose**: Document key architectural decisions for ai_sdlc_method implementation

---

## ADR Index

### Core Platform Decisions

**ADR-001**: [Claude Code as MVP Implementation Platform](ADR-001-claude-code-as-mvp-platform.md)
- **Status**: ✅ Accepted
- **Date**: 2025-11-25
- **Decision**: Use Claude Code native plugin system vs custom MCP server
- **Rationale**: 90% simpler, leverages existing platform, faster MVP
- **Requirements**: REQ-F-PLUGIN-001, REQ-F-CMD-001, REQ-F-CMD-002

**ADR-002**: [Commands for Workflow Integration](ADR-002-commands-for-workflow-integration.md)
- **Status**: ✅ Accepted
- **Date**: 2025-11-25
- **Decision**: Use slash commands (`.claude/commands/`) for workflow actions
- **Rationale**: Zero context-switching, seamless integration, minimal implementation
- **Requirements**: REQ-F-CMD-001

**ADR-003**: [Agents for Stage-Specific Personas](ADR-003-agents-for-stage-personas.md)
- **Status**: ✅ Accepted
- **Date**: 2025-11-25
- **Decision**: Use 7 agent files for stage-specific personas/mindsets
- **Rationale**: Stage-appropriate thinking, quality gates, role-based expertise
- **Requirements**: REQ-F-CMD-002

**ADR-004**: [Skills for Reusable Capabilities](ADR-004-skills-for-reusable-capabilities.md)
- **Status**: ✅ Accepted
- **Date**: 2025-11-25
- **Decision**: Package reusable capabilities as skills within plugins
- **Rationale**: DRY principle, composability, cross-stage availability
- **Requirements**: Implicit in all stage requirements

---

## ADR Summary

**Total ADRs**: 4
**Status**: All Accepted ✅
**Coverage**: Core architectural decisions for MVP

### Decision Themes

1. **Platform Choice** - Claude Code native (ADR-001)
2. **Integration Mechanisms**:
   - Commands for actions (ADR-002)
   - Agents for personas (ADR-003)
   - Skills for capabilities (ADR-004)

### Architecture Pattern

```
PLATFORM: Claude Code (ADR-001)
    │
    ├─ COMMANDS (ADR-002) ─────► Actions within conversation
    │                            /aisdlc-checkpoint-tasks
    │
    ├─ AGENTS (ADR-003) ───────► Stage-specific personas
    │                            aisdlc-requirements-agent.md
    │
    └─ SKILLS (ADR-004) ───────► Reusable capabilities
                                 requirement-extraction
```

**Result**: Coherent architecture where all pieces work together

---

## Requirements Coverage

All ADRs trace to requirements:

| ADR | Requirements Satisfied |
|-----|----------------------|
| ADR-001 | REQ-F-PLUGIN-001, REQ-F-CMD-001, REQ-F-CMD-002, REQ-F-WORKSPACE-001 |
| ADR-002 | REQ-F-CMD-001 |
| ADR-003 | REQ-F-CMD-002 |
| ADR-004 | REQ-F-PLUGIN-001 + all stage requirements |

**Coverage**: 10+ requirements directly justified by these 4 ADRs

---

## Ecosystem Acknowledgment

**Technology Landscape** (t = 2025-11-25):
- Claude Code: Stable plugin system, active development
- Model Context Protocol (MCP): Available for future expansion
- AI coding assistants: Copilot (different arch), Cursor (different approach)
- **Decision**: Start with Claude Code, remain extensible for others

**Evolution Path**:
- v0.1.0 (MVP): Claude Code native
- v1.0.0 (Year 1): Consider MCP server for multi-LLM support
- v2.0.0: Evaluate ecosystem changes

---

## Usage

**For New Decisions**:
1. Copy ADR template
2. Number sequentially (ADR-005, ADR-006, etc.)
3. Document context, decision, rationale, alternatives
4. Link to requirements
5. Add to this index

**For Reviews**:
- Review ADRs quarterly
- Update status if superseded
- Document evolution path

---

**Last Updated**: 2025-11-25
**Next Review**: 2026-03-01 (post-MVP validation)
