# ADR-S-002: Multi-Tenancy Model

**Series**: S (specification-level decisions — apply to all implementations)
**Status**: Accepted
**Date**: 2026-03-02
**Scope**: Repository layout — `specification/` vs `imp_*/` boundary

---

## Context

The Asset Graph Model must support multiple runtimes (Claude Code, Gemini CLI, Codex, AWS Bedrock, future). These differ in:

- **Tool API**: how they call external tools, run tests, emit events
- **Command surface**: slash commands vs CLI flags vs API calls
- **Hosting model**: local CLI, cloud function, container
- **Ecosystem constraints**: Python vs Node vs Go

Without an explicit boundary between the shared contract and per-platform code:

1. **Coupling accumulates silently.** A practitioner working on the Claude implementation adds a Claude-specific note to the shared spec. The spec is now wrong for Gemini.
2. **No isolation guarantee.** A bug fix in one implementation can accidentally change shared documents that other implementations depend on.
3. **Forks diverge unpredictably.** When two implementers both write to `specification/`, conflicts are resolved by whoever commits last, not by derivation rules.

The question is: what is the exact boundary, and what are the invariants that hold across it?

---

## Decision

### The boundary

```
specification/         ← shared, tech-agnostic contract (WHAT)
imp_<name>/            ← isolated, tech-bound implementation (HOW)
```

**One writer rule**: `specification/` is written by the methodology author. Each `imp_<name>/` is written exclusively by the implementer for that platform. No cross-tenant writes.

### Tenant directory layout

Each `imp_<name>/` is a complete, self-contained implementation:

```
imp_<name>/
├── design/             ← tech-bound ADRs, architecture, design docs
├── code/               ← runtime code, configs, installers
├── tests/              ← implementation-specific tests
└── docs/               ← platform-specific guides
```

### What crosses the boundary (read-only)

| `imp_*/` reads from `specification/` | `specification/` reads from `imp_*/` |
|--------------------------------------|---------------------------------------|
| `core/` — formal system | Nothing. |
| `requirements/` — what to build | |
| `features/` — build order | |
| `verification/` — acceptance contracts | |

The dependency is **one-way**: implementations read from spec; spec does not depend on implementations.

### Shared runtime state

`.ai-workspace/` is a shared runtime workspace. It is not specification. It is owned by the running agent and its contents are derived projections (feature vectors, events, task lists). It is not subject to the one-writer rule but also does not carry authoritative specification content.

### Invariant

> A document in `specification/` that contains any of the following is misplaced and must be moved to `imp_<name>/`:
> - A named technology, platform, or runtime (Claude, Gemini, Python, Node.js, MCP)
> - A deployment target (cloud provider, container runtime, serverless)
> - A version pin to a specific library or tool

---

## Consequences

**Positive:**
- A new implementation can be started by reading `specification/` alone — no cross-contamination from other implementations.
- A bug in one implementation cannot propagate to shared spec.
- The methodology can be open-sourced one implementation at a time without leaking unrelated tech choices.

**Negative / trade-offs:**
- Content that feels "obviously shared" (e.g., a UX principle) may still belong to a specific implementation if it names a technology.
- The one-writer rule requires discipline; version control alone does not enforce it.
- Some decisions straddle the boundary (e.g., "how do we handle API rate limiting?"). The rule: if the decision is about the algorithm, it is spec; if it is about the client library, it is design.

---

## Alternatives Considered

**Monorepo with a single shared folder**: What we have. Chosen because it keeps the formal system co-located with its instantiations, making derivation relationships visible.

**Separate repos per implementation**: Rejected. Cross-referencing between spec and implementation becomes a multi-repo coordination problem. Derivation chain is broken across repo boundaries.

**Per-implementation forks of the spec**: Rejected. The whole point is that the formal system is shared. Forks invalidate the "one spec, many designs" property.

---

## References

- [core/AI_SDLC_ASSET_GRAPH_MODEL.md](../core/AI_SDLC_ASSET_GRAPH_MODEL.md) — §1: the formal system is the shared invariant
- [ADR-S-001](ADR-S-001-specification-document-hierarchy.md) — placement rules within `specification/`
- `imp_claude/design/adrs/ADR-016` — Claude-side tolerance design (example of correctly-scoped implementation ADR)
