# ADR-015: Sensory Service Technology Binding — MCP Server + Claude Headless

**Status**: Accepted
**Date**: 2026-02-22
**Deciders**: Methodology Author
**Requirements**: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005

---

## Context

The specification (§4.5.4) defines the sensory service as a **long-running service** with five capabilities: workspace watching, monitor scheduling, affect triage, homeostatic response generation, and review boundary exposure. The spec is deliberately technology-agnostic — it says "long-running service", "probabilistic agent", and "tool interface" without prescribing HOW.

This ADR records the Claude Code implementation's binding of those abstract concepts to concrete platform technologies.

### Why This ADR Exists

These technology bindings were previously embedded in the spec documents (AI_SDLC_ASSET_GRAPH_MODEL.md and AISDLC_IMPLEMENTATION_REQUIREMENTS.md). During spec/design boundary enforcement review (2026-02-22), they were correctly identified as design decisions and moved here. The spec now says WHAT (long-running service, probabilistic agent, tool interface); this ADR says HOW for the Claude Code platform.

### Options Considered

**For the service runtime:**
1. **MCP Server** — Claude Code's native server protocol; long-running, tool-exposing, workspace-integrated
2. **Standalone Python service** — separate process with REST/gRPC API
3. **Claude Code hooks only** — no long-running service; sensing only during iterate()

**For probabilistic agent (homeostatic response generation):**
1. **Claude headless** — Claude Code's non-interactive API for batch/background LLM invocations
2. **Direct API calls** — Anthropic API via SDK
3. **External LLM service** — any OpenAI-compatible endpoint

**For the review boundary:**
1. **MCP tools** — Claude Code's tool protocol, surfacing proposals to the interactive session
2. **File-based inbox** — proposals written to a directory, human reviews via editor
3. **Web UI** — separate frontend for proposal review

---

## Decision

### Sensory Service: MCP Server

The sensory service runs as an **MCP (Model Context Protocol) server** within the Claude Code ecosystem.

```
┌─────────────────────────────────────────────────────────────────┐
│                   SENSORY SERVICE (MCP Server)                    │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ Interoceptive│  │ Exteroceptive│  │ Affect Triage       │   │
│  │ Monitors     │  │ Monitors     │  │ (rule + agent-class)│   │
│  │ INTRO-001..7 │  │ EXTRO-001..4 │  │                     │   │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬───────────┘   │
│         │                  │                     │               │
│         └──────── signals ─┴─────────────────────┘               │
│                            │                                      │
│                     ┌──────┴──────┐                               │
│                     │ Claude      │                               │
│                     │ Headless    │  draft proposals only         │
│                     └──────┬──────┘                               │
│                            │                                      │
│  ═══════════════ REVIEW BOUNDARY (MCP tools) ═══════════════════ │
│                            │                                      │
└────────────────────────────┼──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              INTERACTIVE SESSION (Human in loop)                  │
│                                                                   │
│  Human reviews proposals → approve / modify / dismiss            │
│  Approved proposals → intent_raised / spec_modified events       │
│  Changes applied to workspace                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Why MCP Server:**
- Native to Claude Code — no additional deployment, infrastructure, or dependency management
- Long-running — persists across user interactions, maintains monitor state
- Tool-exposing — MCP tools are the native mechanism for surfacing capabilities to the interactive session
- Workspace-integrated — can watch filesystem events, read event logs, access project state
- Portable — the MCP protocol is an open standard; other implementations can provide equivalent functionality

**Configuration:**
- Registered in `.mcp.json` (project-level) or user-level MCP config
- Started on workspace open (or on-demand)
- Monitor schedules and thresholds in `sensory_monitors.yml`
- Affect triage rules in `affect_triage.yml`

### Probabilistic Agent: Claude Headless

For signals that require probabilistic classification or homeostatic response generation, the sensory service invokes **Claude headless** — Claude Code's non-interactive batch invocation mode.

**Two invocation points:**

1. **Affect triage (ambiguous signals)** — when rule-based classification is insufficient, Claude headless classifies the signal. This is the IntentEngine's bounded-ambiguity path (ADR-014) applied within the sensory service.

2. **Draft proposal generation** — for signals that escalate past triage, Claude headless generates draft proposals: proposed intent events, proposed diffs, proposed spec modifications. These are **drafts only** — the service cannot modify workspace files.

**Why Claude headless (vs direct API):**
- Consistent with the implementation platform — same model, same context handling, same tool access
- Supports the iterate agent's context window management (can load project state, graph topology, feature vectors)
- No additional API keys, authentication, or endpoint configuration

**What Claude headless produces (draft only):**
- `draft_intent_raised` — proposed intent with signal source, affected REQ keys, recommended vector type
- `draft_diff` — proposed code/config change (rendered but not applied)
- `draft_spec_modification` — proposed requirement addition or modification

**What Claude headless does NOT do:**
- Modify workspace files
- Emit `intent_raised` or `spec_modified` events to the canonical event log
- Create or modify feature vectors
- Approve its own proposals

### Review Boundary: MCP Tools

The review boundary is implemented as **MCP tools** exposed by the sensory service to the interactive Claude session:

| MCP Tool | Purpose | Output |
|----------|---------|--------|
| `/sensory-status` | Current state of all monitors, last run times, signal counts | Monitor health dashboard |
| `/sensory-proposals` | List pending draft proposals with full context | Proposal list with trigger chains |
| `/sensory-approve --id <proposal_id>` | Approve a proposal — the interactive session applies the change | Confirmation + events emitted |
| `/sensory-dismiss --id <proposal_id> --reason <reason>` | Dismiss a proposal with reason (logged for learning) | Dismissal logged |
| `/sensory-config` | View/modify monitor configuration, thresholds | Current config |

**Review workflow:**
1. Human invokes `/sensory-proposals` in interactive session
2. Reviews each proposal (full context: triggering signal, triage classification, proposed action)
3. Approves (interactive session applies change, emits events) or dismisses (logged with reason)

**Why MCP tools (vs file-based inbox):**
- Interactive — proposals are presented with full context in the conversational interface
- Actionable — approval triggers immediate application by the interactive session
- Auditable — all approve/dismiss actions emit events to `events.jsonl`
- Consistent — same UX pattern as `/aisdlc-*` commands

---

## Rationale

### Why These Specific Bindings

The sensory service technology choices follow a single principle: **use the platform's native capabilities**. For Claude Code, that means MCP for services, Claude headless for probabilistic compute, and MCP tools for human interaction. A Gemini implementation would bind to Gemini's equivalent service model; a Codex implementation to Codex's.

### Relationship to Spec/Design Boundary

The specification says:
- "long-running service" → this ADR binds to MCP Server
- "probabilistic agent" → this ADR binds to Claude headless
- "tool interface" / "service interface" → this ADR binds to MCP tools
- "project state view" → this ADR binds to STATUS.md (a generated markdown file)

Each binding is a design decision that could be made differently by a different implementation platform. The spec's technology-agnostic language ensures that Gemini Genesis and Codex Genesis can make different binding decisions while implementing the same specification.

### Project State View Binding

The spec refers to "project state view" (an auto-regenerated derived view of project status). In the Claude Code implementation, this is materialised as **STATUS.md** — a markdown file regenerated at every iteration boundary as a protocol hook side effect. The filename is a convention; the invariant is that a derived project state view exists and is kept fresh.

---

## Consequences

### Positive

- **Clean spec/design separation** — technology bindings live in this ADR, not in the platform-agnostic spec
- **Platform portability** — other implementations can read the same spec and make different binding decisions
- **Native integration** — MCP server + Claude headless + MCP tools are the natural Claude Code integration points
- **Observable** — all sensory service actions produce events in the shared event log

### Negative

- **Platform lock-in at design level** — this ADR is specific to Claude Code. Other platforms need their own equivalent ADR.
- **MCP dependency** — requires MCP server infrastructure. Mitigated: MCP is an open standard with growing ecosystem support.

---

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) §4.5 (Sensory Systems), §4.6 (IntentEngine)
- [ADR-008](ADR-008-universal-iterate-agent.md) — Universal Iterate Agent (primary consumer of sensory signals)
- [ADR-011](ADR-011-consciousness-loop-at-every-observer.md) — Consciousness Loop (signal source classification taxonomy)
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding (affect triage IS the IntentEngine at sensory level)
- [ADR-016](ADR-016-design-tolerances-as-optimization-triggers.md) — Design Tolerances (tolerance thresholds monitored by sensory service)

---

## Requirements Addressed

- **REQ-SENSE-001**: Interoceptive monitoring — monitors run within the MCP server
- **REQ-SENSE-002**: Exteroceptive monitoring — monitors run within the MCP server
- **REQ-SENSE-003**: Affect triage pipeline — rule-based + Claude headless classification
- **REQ-SENSE-004**: Sensory system configuration — `sensory_monitors.yml`, `affect_triage.yml`
- **REQ-SENSE-005**: Review boundary — MCP tools (`/sensory-status`, `/sensory-proposals`, `/sensory-approve`, `/sensory-dismiss`, `/sensory-config`)
