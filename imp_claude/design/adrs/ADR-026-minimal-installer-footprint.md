# ADR-026: Minimal Permanent Installer Footprint

**Status**: Accepted
**Date**: 2026-03-07
**Deciders**: Methodology Author
**Requirements**: REQ-TOOL-011 (Installability), REQ-UX-001 (State-Driven Routing), REQ-UX-002 (Progressive Disclosure)
**Extends**: ADR-012 (Two-Command UX), ADR-018 (Plugin Marketplace Distribution)

---

## Context

The installer (`gen-setup.py`) and `/gen-init` command were written as bootstrap scaffolding — a ladder to climb from "blank project" to "methodology running." They perform ~15 operations: copying configs, scaffolding directories, registering marketplaces, injecting the bootloader, creating templates, and writing settings.json.

This complexity made sense at genesis. It no longer makes sense for a mature system.

### The Ladder Problem

An evolved system can be recognised by what it no longer needs. The bootstrap artifacts that created it can be lifted away once the system is capable of deriving them itself. Wittgenstein's ladder: climb it, then kick it away.

The question is: **what is the minimal footprint that genuinely cannot be self-derived?**

### What Cannot Be Self-Derived

Three artifacts are non-derivable because they are integration contracts with external systems, not methodology artifacts:

1. **`.claude/settings.json`** — Claude Code reads this on startup to discover the marketplace. There is no in-session mechanism for the methodology to register itself. This is an integration boundary.

2. **`.ai-workspace/events/events.jsonl`** — The event log must exist (even as an empty file) before any event can be appended. It cannot be created by the first event that writes to it. This is a bootstrapping precondition, not a derived view.

3. **`CLAUDE.md` bootloader injection** — The LLM axiom set must be present in the session context before the first methodology command runs. Without it, the LLM pattern-matches templates instead of reasoning within the formal system. This is a constraint-surface precondition.

### What Can Be Self-Derived (the ladder)

Everything else the installer currently creates can be derived lazily by `/gen-start` when it detects `UNINITIALISED` state:

| Artifact | Why it's derivable |
|----------|-------------------|
| `.ai-workspace/graph/graph_topology.yml` | Copy from plugin canonical config on first use |
| `.ai-workspace/graph/edges/` | Copy from plugin `config/edge_params/` on first use |
| `.ai-workspace/profiles/` | Copy from plugin `config/profiles/` on first use |
| `.ai-workspace/context/project_constraints.yml` | Derive from project detection (language, test runner, etc.) |
| `.ai-workspace/features/feature_index.yml` | Create empty on first feature |
| `.ai-workspace/tasks/active/ACTIVE_TASKS.md` | Create empty on first iteration |
| `specification/INTENT.md` | Template, created during intent→requirements edge |
| `imp_{impl}/design/adrs/ADR-000-template.md` | Template, created during design edge |
| `.ai-workspace/STATUS.md` | Derived view of events.jsonl — generated on demand |

These are scaffolding, not constraints. A ladder, not the floor.

---

## Decision

### 1. Minimal Permanent Installer Footprint

`gen-setup.py` is reduced to three operations:

```
1. Write .claude/settings.json          → marketplace + plugin registration
2. Touch .ai-workspace/events/events.jsonl  → event log bootstrapping precondition
3. Append GENESIS_BOOTLOADER to CLAUDE.md  → axiom set injection
```

All other scaffolding is removed from the installer. No workspace directory copying. No config file population. No template creation.

Optionally: emit a `project_initialized` event to `events.jsonl` on first install.

### 2. `/gen-start` Owns UNINITIALISED State

When `/gen-start` detects state `UNINITIALISED` (`.ai-workspace/` absent or empty event log), it performs lazy scaffolding inline:

- Copies graph topology + edge configs + profiles from plugin canonical configs
- Runs project detection (language, test runner, linter) and writes `project_constraints.yml`
- Presents the user with ≤5 questions (REQ-UX-002)
- Asks for initial intent
- Emits `project_initialized` event
- Proceeds directly to `intent→requirements` edge

This is the same behaviour as the current `/gen-init`, but triggered automatically by state detection rather than requiring the user to know to run `/gen-init` first.

### 3. `/gen-init` Becomes a Power-User Command

`/gen-init` is retained as an explicit escape hatch for:
- Re-scaffolding after a workspace is corrupted
- Upgrading graph topology configs to a new plugin version
- Explicit re-initialisation with `--force`

It is no longer a required step in the onboarding flow.

### 4. The Bootloader is Transitional

The CLAUDE.md bootloader injection is itself a ladder. The correct long-run design is for Claude Code to load the methodology axiom set natively (via the plugin system's agent files or a session-start hook). Until that mechanism exists, the bootloader injection in `CLAUDE.md` is the necessary workaround.

ADR-018 already captures the hook delivery mechanism (`hooks.json` with `${CLAUDE_PLUGIN_ROOT}`). When Claude Code's plugin system is mature enough to guarantee axiom loading, the CLAUDE.md injection can be removed from the installer and the ladder is fully lifted.

---

## Consequences

### Positive

- Installer is trivially auditable: 3 operations, no hidden state
- Onboarding path collapses: `curl | python3 -` → restart → `/gen-start` (no `/plugin install` required as a manual step if bundled correctly; no `/gen-init` required)
- State machine in `/gen-start` is the single source of truth for what a project needs at each state — no duplication between installer and init command
- Evolved systems dissolve their own scaffolding: as the plugin system matures, each of the three remaining installer operations can be removed one by one

### Negative

- `/gen-start` UNINITIALISED handler is now load-bearing — it must be robust and idempotent
- First-run latency: lazy scaffolding means the first `/gen-start` does more work than a pre-scaffolded workspace
- `/gen-init` loses its primary use case and becomes harder to justify maintaining

### Neutral

- `gen-setup.py` still exists — it just does less. The curl-pipe-python UX is preserved.
- REQ-TOOL-011 (idempotent, verifiable install) is still satisfied by the reduced footprint

---

## The Invariant

A methodology that installs itself by writing three files and then derives everything else from the formal system on first use is a methodology that has successfully eaten its own bootstrap. The measure of maturity is not feature count — it is how little scaffolding remains.

---

## References

- ADR-012: Two-Command UX Layer (UNINITIALISED state in gen-start state machine)
- ADR-018: Plugin Marketplace Distribution (settings.json structure, bootloader delivery)
- REQ-TOOL-011: Installability
- REQ-UX-001: State-Driven Routing (UNINITIALISED detection)
- REQ-UX-002: Progressive Disclosure (≤5 questions at init)
- `imp_claude/code/installers/gen-setup.py`: Current installer (to be simplified)
- `imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-init.md`: Init command (demoted to power-user escape hatch)
- `imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md`: State-driven entry point (promoted to own UNINITIALISED)
