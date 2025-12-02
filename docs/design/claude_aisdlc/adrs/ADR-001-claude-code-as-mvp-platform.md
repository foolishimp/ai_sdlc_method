# ADR-001: Claude Code as MVP Implementation Platform

**Status**: Accepted
**Date**: 2025-11-25
**Deciders**: Development Tools Team
**Requirements**: REQ-TOOL-001 (Plugin Architecture), REQ-TOOL-003 (Workflow Commands), REQ-AI-003 (Stage-Specific Agent Personas)

---

## Context

The AI SDLC methodology needs a platform to deliver the 7-stage framework to developers. We need to choose the initial implementation platform for MVP (v0.1.0).

### Available Options

1. **Claude Code native** - Use Claude Code's plugin system, commands, and agents
2. **Custom MCP server** - Build Model Context Protocol server supporting multiple LLMs
3. **VSCode extension** - Build custom VS Code extension
4. **Language-specific library** - Python/Node.js library developers import
5. **CLI tool** - Standalone command-line tool

---

## Decision

**We will use Claude Code's native plugin system as the MVP implementation platform.**

Specifically:
- **Plugins** - Deliver methodology via `.claude-plugin/` format
- **Commands** - Workflow integration via `.claude/commands/` slash commands
- **Agents** - Stage personas via `.claude/agents/` markdown files
- **Skills** - Reusable capabilities via plugin skills

---

## Rationale

### Why Claude Code (vs Alternatives)

**1. Native Platform Leverage** ✅
- Claude Code already has plugin system - we use it, not build it
- Commands already supported - we write markdown, not code
- Agents already supported - we write personas, not infrastructure
- Zero runtime dependencies - just files

**2. 90% Simpler Than Alternatives**
```
Custom MCP Server:
- Build API server
- Handle authentication
- Manage sessions
- Parse/validate requests
- Support multiple LLMs
- Deploy infrastructure
= 2,000+ lines of code

Claude Code Plugin:
- Write markdown files
- Define YAML configuration
- Package as plugin
= 200 lines of config
```

**3. Git-Friendly**
- All assets are markdown/YAML files
- Version controlled naturally
- No databases to manage
- Offline capable
- No deployment complexity

**4. LLM-Optimized**
- Claude Code IS Claude (same model)
- Native understanding of methodology
- No translation layer needed
- Optimized for long context (1M tokens)

**5. Federated Architecture Built-In**
- Claude Code marketplace system already supports:
  - GitHub marketplaces
  - Local marketplaces
  - Plugin loading order (composition)
  - Dependency management
- We leverage existing functionality

**6. Fast MVP Iteration**
- Edit markdown → reload Claude → test
- No build step, no deployment
- Dogfood immediately
- Rapid iteration cycle

---

## Rejected Alternatives

### Alternative 1: Custom MCP Server
**Why Rejected**:
- ❌ 10x more complex (server, API, multi-LLM support)
- ❌ Infrastructure to deploy and maintain
- ❌ Slower iteration (code → build → deploy cycle)
- ❌ Not MVP scope (Year 1 feature per intent)

**When to Reconsider**: Year 1, if demand exists for Copilot/Gemini support

### Alternative 2: VSCode Extension
**Why Rejected**:
- ❌ VSCode-specific (not portable)
- ❌ Requires TypeScript/JavaScript development
- ❌ Extension marketplace different from Claude plugins
- ❌ More complex than markdown files

**When to Reconsider**: If VSCode-specific features needed

### Alternative 3: Python/Node.js Library
**Why Rejected**:
- ❌ Programmatic API, not conversational
- ❌ Requires code integration, not just config
- ❌ Doesn't leverage AI assistant naturally
- ❌ Language lock-in

**When to Reconsider**: If programmatic access needed

### Alternative 4: CLI Tool
**Why Rejected**:
- ❌ Separate from AI conversation
- ❌ Context-switching between CLI and Claude
- ❌ Doesn't integrate with AI workflow
- ❌ Requires separate installation

**When to Reconsider**: If non-AI workflows needed

---

## Consequences

### Positive

✅ **MVP Speed**
- Can ship v0.1.0 quickly (files, not code)
- No infrastructure to deploy
- Dogfood from day 1

✅ **Simplicity**
- Markdown + YAML (no programming required)
- Git-friendly (version controlled)
- Offline capable (no network dependencies)

✅ **Native Integration**
- Commands work seamlessly in Claude Code
- Agents load automatically
- Skills available via plugins
- No glue code needed

✅ **Federated Architecture**
- Leverage Claude Code's marketplace system
- Plugin composition built-in
- Corporate → Division → Team → Project hierarchy natural

✅ **Zero Deployment Complexity**
- No servers to run
- No databases to manage
- No authentication to handle
- Just files in git

### Negative

⚠️ **Claude Code Dependency**
- Locked to Claude Code for MVP
- Other LLMs require future work (MCP server)
- Claude Code changes could break plugins

**Mitigation**:
- Extensible architecture (can add MCP later)
- File format is platform-agnostic
- Methodology documented independently of platform

⚠️ **Limited to File-Based Assets**
- No database queries
- No real-time collaboration
- No web UI (yet)

**Mitigation**:
- Acceptable for MVP scope
- Can add later if needed
- Most dev work is file-based anyway

⚠️ **Plugin System Constraints**
- Must follow Claude Code plugin conventions
- Limited to capabilities Claude Code provides
- Can't extend platform itself

**Mitigation**:
- Constraints are reasonable
- Claude Code platform is extensible
- Feedback to Anthropic for improvements

---

## Ecosystem Acknowledgment E(t)

**Ecosystem Constraints Considered**:

1. **Claude Code Platform** (t = 2025-11-25)
   - Plugin system: Stable, documented
   - Command system: `.claude/commands/*.md` format
   - Agent system: `.claude/agents/*.md` format
   - Marketplace: GitHub-based, local file support

2. **Anthropic Roadmap**
   - Claude Code under active development
   - Model Context Protocol (MCP) supported
   - Plugin API stable

3. **Competitive Landscape**
   - GitHub Copilot - No comparable plugin system
   - Cursor - Different architecture
   - Codeium - Different approach
   - Claude Code - Most extensible for methodology delivery

4. **Technology Constraints**
   - Markdown format - Universal
   - YAML configuration - Standard
   - Git version control - Universal
   - No proprietary formats

---

## Validation

**Does this decision satisfy requirements?**

| Requirement | Satisfied? | How |
|-------------|------------|-----|
| REQ-TOOL-001 | ✅ | Claude Code has native plugin system |
| REQ-TOOL-004 | ✅ | Marketplace supports configuration hierarchy |
| REQ-TOOL-005 | ✅ | SemVer versioning in plugin.json |
| REQ-TOOL-003 | ✅ | Slash commands via `.claude/commands/` |
| REQ-AI-003 | ✅ | Agents via `.claude/agents/` |
| REQ-TOOL-002 | ✅ | File-based workspace compatible |
| REQ-TOOL-002 | ✅ | Files persist in git |
| REQ-TOOL-004 | ✅ | Plugin loading order = composition |

**All core tool requirements satisfied by this decision.** ✅

---

## Related Decisions

- **ADR-002**: Commands for Workflow Integration (justifies command usage)
- **ADR-003**: Agents for Stage Personas (justifies agent usage)
- **ADR-004**: Skills for Reusable Capabilities (justifies skill pattern)

---

## Notes

- This is an **MVP decision** - not permanent lock-in
- Architecture remains **extensible** for future platforms
- File format is **platform-agnostic** (can migrate if needed)
- **Year 1**: Consider MCP server for multi-LLM support

---

**Decision made**: 2025-11-25
**Review date**: 2026-03-01 (after MVP validation with 5+ teams)
