# Architecture Decision Records (ADRs)

**Purpose**: Document key architectural decisions for ai_sdlc_method implementation

---

## ADR Index

### v2.1 — Current (Asset Graph Model)

**ADR-008**: [Universal Iterate Agent](ADR-008-universal-iterate-agent.md)
- **Status**: Accepted
- **Date**: 2026-02-19
- **Decision**: Single iterate agent parameterised by edge config, replacing 7 stage agents
- **Supersedes**: ADR-003, ADR-004, ADR-005
- **Requirements**: REQ-ITER-001, REQ-ITER-002, REQ-EVAL-001

**ADR-009**: [Graph Topology as Configuration](ADR-009-graph-topology-as-configuration.md)
- **Status**: Accepted
- **Date**: 2026-02-19
- **Decision**: YAML config files for asset types, transitions, edge parameterisations
- **Requirements**: REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003, REQ-CTX-001

**ADR-010**: [Spec Reproducibility](ADR-010-spec-reproducibility.md)
- **Status**: Accepted
- **Date**: 2026-02-19
- **Decision**: Content-addressable manifest with SHA-256 hashing for Context[] reproducibility
- **Requirements**: REQ-INTENT-004

### Carried Forward from v1.x

**ADR-001**: [Claude Code as MVP Implementation Platform](ADR-001-claude-code-as-mvp-platform.md)
- **Status**: Accepted (carried forward)
- **Date**: 2025-11-25
- **Decision**: Use Claude Code native plugin system vs custom MCP server
- **Rationale**: 90% simpler, leverages existing platform, faster MVP
- **Note**: Platform choice remains valid for v2.1. Plugin mechanism unchanged.

**ADR-002**: [Commands for Workflow Integration](ADR-002-commands-for-workflow-integration.md)
- **Status**: Accepted (carried forward)
- **Date**: 2025-11-25
- **Decision**: Use slash commands (`.claude/commands/`) for workflow actions
- **Note**: Commands change (8 new commands), mechanism unchanged.

**ADR-006**: [Plugin Configuration and Discovery](ADR-006-plugin-configuration-and-discovery.md)
- **Status**: Accepted (carried forward)
- **Date**: 2025-11-27
- **Decision**: Plugin discovery via marketplace.json with .claude-plugin/plugin.json metadata
- **Note**: Plugin structure adapts for v2.1 content, discovery mechanism unchanged.

### Superseded by v2.1

**ADR-003**: [Agents for Stage-Specific Personas](ADR-003-agents-for-stage-personas.md)
- **Status**: Superseded by ADR-008
- **Date**: 2025-11-25
- **Decision**: ~~7 agent files for stage-specific personas~~ → 1 iterate agent

**ADR-004**: [Skills for Reusable Capabilities](ADR-004-skills-for-reusable-capabilities.md)
- **Status**: Superseded by ADR-008
- **Date**: 2025-11-25
- **Decision**: ~~11 skills for reusable capabilities~~ → edge parameterisations

**ADR-005**: [Iterative Refinement via Feedback Loops](ADR-005-iterative-refinement-feedback-loops.md)
- **Status**: Superseded by ADR-008
- **Date**: 2025-11-25
- **Decision**: ~~Per-stage feedback loops~~ → inherent in iterate()

**ADR-007**: [Hooks for Methodology Automation](ADR-007-hooks-for-methodology-automation.md)
- **Status**: Superseded (hooks now driven by graph transitions)
- **Date**: 2025-11-27
- **Decision**: ~~Lifecycle hooks for stage transitions~~ → graph transition triggers

---

## ADR Summary

**Total ADRs**: 10 (3 new v2.1, 3 carried forward, 4 superseded)

### v2.1 Architecture Pattern

```
PLATFORM: Claude Code (ADR-001, carried forward)
    │
    ├─ COMMANDS (ADR-002, adapted) ──► /aisdlc-iterate, /aisdlc-status, ...
    │
    ├─ ITERATE AGENT (ADR-008) ──────► Single agent, edge-parameterised
    │                                   aisdlc-iterate.md (THE one agent)
    │
    ├─ GRAPH TOPOLOGY (ADR-009) ─────► YAML configs in Context[]
    │                                   asset_types.yml, transitions.yml
    │
    ├─ SPEC REPRODUCIBILITY (ADR-010) ► Content-addressable manifest
    │                                   context_manifest.yml
    │
    └─ PLUGINS (ADR-006, carried) ───► Discovery & configuration
                                        marketplace.json, plugin.json
```

### v1.x vs v2.1 Comparison

| Aspect | v1.x ADRs | v2.1 ADRs |
|--------|-----------|-----------|
| Agent model | 7 stage agents (ADR-003) | 1 iterate agent (ADR-008) |
| Reuse | 11 skills (ADR-004) | Edge parameterisations (ADR-008, ADR-009) |
| Iteration | Per-stage loops (ADR-005) | Universal iterate() (ADR-008) |
| Topology | Implicit in agents | Explicit YAML config (ADR-009) |
| Reproducibility | Not addressed | Content-addressable manifest (ADR-010) |
| Platform | Claude Code (ADR-001) | Claude Code (ADR-001, unchanged) |
| Commands | Slash commands (ADR-002) | Slash commands (ADR-002, adapted) |
| Plugins | Discovery (ADR-006) | Discovery (ADR-006, unchanged) |

---

## Requirements Coverage (v2.1)

| ADR | Requirements Satisfied |
|-----|----------------------|
| ADR-001 | REQ-TOOL-001, REQ-TOOL-003 |
| ADR-002 | REQ-TOOL-003, REQ-TOOL-002 |
| ADR-006 | REQ-TOOL-001, REQ-TOOL-004 |
| ADR-008 | REQ-ITER-001, REQ-ITER-002, REQ-EVAL-001 |
| ADR-009 | REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003, REQ-CTX-001 |
| ADR-010 | REQ-INTENT-004 |

---

**Last Updated**: 2026-02-19
**Model Version**: v2.1 (Asset Graph Model)
