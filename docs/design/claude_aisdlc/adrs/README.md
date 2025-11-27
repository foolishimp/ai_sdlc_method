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

**ADR-005**: [Iterative Refinement via Feedback Loops](ADR-005-iterative-refinement-feedback-loops.md)
- **Status**: ✅ Accepted
- **Date**: 2025-11-25
- **Decision**: All agents implement feedback protocols for iterative refinement
- **Rationale**: Quality through iteration, explicit feedback mechanisms
- **Requirements**: REQ-NFR-REFINE-001

**ADR-006**: [Plugin Configuration and Discovery](ADR-006-plugin-configuration-and-discovery.md)
- **Status**: ✅ Accepted
- **Date**: 2025-11-27
- **Decision**: Plugin discovery via marketplace.json with .claude-plugin/plugin.json metadata
- **Rationale**: Standard Claude Code patterns, federated loading support
- **Requirements**: REQ-F-PLUGIN-001, REQ-F-PLUGIN-002

**ADR-007**: [Hooks for Methodology Automation](ADR-007-hooks-for-methodology-automation.md)
- **Status**: 📋 Proposed
- **Date**: 2025-11-27
- **Decision**: Use lifecycle hooks to automate methodology compliance
- **Rationale**: Implicit automation complements explicit commands
- **Requirements**: REQ-F-HOOKS-001 (NEW), REQ-NFR-CONTEXT-001

---

## ADR Summary

**Total ADRs**: 7
**Status**: 6 Accepted ✅, 1 Proposed 📋
**Coverage**: Core architectural decisions for MVP

### Decision Themes

1. **Platform Choice** - Claude Code native (ADR-001)
2. **Integration Mechanisms**:
   - Commands for explicit actions (ADR-002)
   - Agents for stage personas (ADR-003)
   - Skills for reusable capabilities (ADR-004)
   - Hooks for implicit automation (ADR-007)
3. **Quality Mechanisms**:
   - Feedback loops for refinement (ADR-005)
   - Plugin discovery patterns (ADR-006)

### Architecture Pattern

```
PLATFORM: Claude Code (ADR-001)
    │
    ├─ COMMANDS (ADR-002) ─────► Explicit actions
    │                            /aisdlc-checkpoint-tasks
    │
    ├─ HOOKS (ADR-007) ────────► Implicit automation
    │                            SessionStart, Stop, PreToolUse
    │
    ├─ AGENTS (ADR-003) ───────► Stage-specific personas
    │                            aisdlc-requirements-agent.md
    │
    ├─ SKILLS (ADR-004) ───────► Reusable capabilities
    │                            requirement-extraction
    │
    └─ PLUGINS (ADR-006) ──────► Discovery & configuration
                                 marketplace.json, plugin.json
```

**Result**: Coherent architecture with explicit + implicit interaction patterns

---

## Requirements Coverage

All ADRs trace to requirements:

| ADR | Requirements Satisfied |
|-----|----------------------|
| ADR-001 | REQ-F-PLUGIN-001, REQ-F-CMD-001, REQ-F-CMD-002, REQ-F-WORKSPACE-001 |
| ADR-002 | REQ-F-CMD-001 |
| ADR-003 | REQ-F-CMD-002 |
| ADR-004 | REQ-F-PLUGIN-001 + all stage requirements |
| ADR-005 | REQ-NFR-REFINE-001 |
| ADR-006 | REQ-F-PLUGIN-001, REQ-F-PLUGIN-002 |
| ADR-007 | REQ-F-HOOKS-001 (NEW), REQ-NFR-CONTEXT-001 |

**Coverage**: 15+ requirements directly justified by these 7 ADRs

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

**Last Updated**: 2025-11-27
**Next Review**: 2026-03-01 (post-MVP validation)
