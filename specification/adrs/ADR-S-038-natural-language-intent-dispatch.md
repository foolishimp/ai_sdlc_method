# ADR-S-038: Natural Language Intent Dispatch

**Status**: Accepted
**Date**: 2026-03-12
**Deciders**: Jim (product), Claude Sonnet 4.6 (design peer)
**Implements**: REQ-UX-008
**Supersedes**: —
**Related**: ADR-S-032 (IntentObserver/EDGE_RUNNER dispatch), ADR-S-036 (invariants as termination conditions)

---

## Context

The Genesis methodology has a two-command UX goal: **Start** ("Go.") and **Status** ("Where am I?"). In practice, users still need to know:

- That `/gen-start` exists and that `--auto` is the flag for autonomous iteration
- That `/gen-gaps` is different from `/gen-status --health`
- That `/gen-spawn --type feature` is how you create a new feature vector
- Which feature ID and edge to pass to `/gen-iterate`

This is the **command vocabulary problem**: the methodology has powerful state-machine routing, but accessing it requires knowing the command names and flags. This is the equivalent of a text adventure game that requires the player to know `NORTH`, `TAKE TORCH`, `OPEN DOOR` rather than accepting "go north", "pick up the torch", "open the door".

A second problem: **cold-start context loss**. When a new Claude session begins without conversation history, the routing knowledge that built up in the previous session is gone. The user has to re-orient the agent manually.

The question is: **what is the minimal mechanism to make natural language a sufficient entry point to the methodology?**

---

## Decision

**The Genesis Bootloader is the routing vocabulary. The workspace state personalises it. The LLM is the routing layer.**

No separate NLP model is needed. No separate routing table needs to be maintained. The bootloader already contains the complete methodology vocabulary — the eight functional units, the graph topology, the processing phases, the convergence criteria. A session that has loaded the bootloader and current workspace state has everything needed to map natural language to methodology operations.

The dispatch mechanism is:

```
User input (natural language)
    ↓
LLM + bootloader axioms + workspace state
    ↓
intent_routed{input, routed_to, feature, edge, confidence}   ← observable
    ↓
F_D process chain (gen-iterate, gen-start, gen-gaps, ...)
```

The `/gen-genesis` command is the session bootstrap: it loads the bootloader and reads workspace state to build a personalised routing context. After `/gen-genesis`, every user message is treated as natural language intent.

### Routing Confidence Thresholds

| Confidence | Action |
|-----------|--------|
| ≥ 0.85 | Silent dispatch — show one-liner `→ /gen-iterate --feature REQ-F-SENSE-002 --edge requirements` |
| 0.50–0.85 | Present two candidate operations — user selects |
| < 0.50 | Single minimal clarification question — never the full command menu |

The confidence thresholds are F_D constraints on the routing function itself. The routing layer is observable and subject to the same convergence criteria as any other F_D check.

### Personalisation from Workspace State

"Fix it" is ambiguous without workspace state. "Fix it" with workspace state resolves to `gen-iterate --feature REQ-F-SENSE-002 --edge requirements` because:
- REQ-F-SENSE-002 is the most recently touched active feature
- `requirements` is its current (non-converged) edge

The routing table has two layers:

1. **Static patterns** — fixed by the bootloader vocabulary, same in every workspace:
   - `"what's broken"` → `gen-status --health`
   - `"find gaps"` → `gen-gaps`
   - `"go"` / `"continue"` → `gen-start --auto`

2. **Dynamic patterns** — personalised to workspace state, rebuilt by `/gen-genesis`:
   - `"fix {feature_title}"` → `gen-iterate --feature {id} --edge {current_edge}`
   - `"review {proposal_id}"` → `gen-review-proposal --show {id}`
   - `"work on {feature_id}"` → `gen-iterate --feature {id} --edge {current_edge}`

### The `intent_routed` Event

Every NL dispatch at confidence ≥ 0.85 emits an `intent_routed` event:

```json
{
  "event_type": "intent_routed",
  "timestamp": "{ISO 8601}",
  "project": "{project_name}",
  "data": {
    "input": "{verbatim user text}",
    "routed_to": "{command string}",
    "confidence": 0.95,
    "feature": "{feature_id or null}",
    "edge": "{edge or null}",
    "basis": "{bootloader section or workspace artifact that justified the routing}"
  }
}
```

This closes the observability loop: NL dispatch is recorded in the event log alongside all other methodology operations. Routing decisions are auditable and replayable. Patterns in `intent_routed` events (e.g., "fix it" appears 40 times → this is the dominant user verb) feed back as methodology improvement signals.

### Cold-Start Guarantee

The cold-start problem is solved durably:

- **Durable artifacts**: bootloader (`GENESIS_BOOTLOADER.md`) and workspace state (feature YAMLs, events.jsonl) are filesystem-persistent
- **Session bootstrap**: `/gen-genesis` rebuilds full routing context from durable artifacts — no dependence on conversation history
- **Axiom drift protection**: re-running `/gen-genesis` after long sessions or context compression reloads the bootloader axioms, preventing drift from methodology constraints

---

## Alternatives Considered

### Alt A: Hard-coded routing table (YAML/JSON file)

Maintain a static `nl_routing_table.yml` mapping patterns to commands.

**Rejected**: The table would need to be updated every time a feature vector is created or an edge changes. The workspace state already contains all the personalisation information — duplicating it into a routing table creates maintenance debt and divergence risk. The bootloader is already the authoritative vocabulary; a separate table would re-encode it.

### Alt B: Separate NLP classifier model

Train or fine-tune a classifier to map user input to methodology operations.

**Rejected**: The LLM already has the reasoning capability. The bootloader axioms are the constraint set that makes the LLM's classification reliable within this domain. A separate model would need to be maintained, versioned, and deployed — adding infrastructure cost for capability the LLM provides natively.

### Alt C: Fuzzy command completion

Extend the CLI with fuzzy matching over command names and flags (e.g., `gen-it` completes to `gen-iterate`).

**Rejected**: Solves the typing problem but not the vocabulary problem. The user still needs to know that "iterate" is the verb and that `--feature` and `--edge` are the parameters. It also doesn't personalise to workspace state.

### Alt D: Keep current command vocabulary, improve documentation

Better help text, examples, and autocomplete.

**Rejected**: Documentation solves the learning problem, not the UX problem. The goal is that users should never need to consult documentation during active use. The adventure-game model means the system meets the user's vocabulary, not the other way around.

---

## Consequences

### Positive

- **Zero command vocabulary burden**: users interact in natural language; the system routes
- **Session-persistent routing**: `/gen-genesis` rebuilds full context from durable artifacts in any new session
- **Observable dispatch**: `intent_routed` events make NL routing as auditable as any other operation
- **Self-improving**: patterns in `intent_routed` events reveal dominant user verbs → feeds back as methodology improvement signals (source_finding intents)
- **Coherent with the bootloader principle**: the bootloader is already the methodology's axiom set; this ADR formalises it as the routing vocabulary too

### Negative

- **Confidence calibration required**: the 0.85/0.50 thresholds are initial values — they need tuning from real usage (intent_routed event analysis)
- **Cold-start latency**: `/gen-genesis` reads bootloader + all workspace files — on large workspaces this takes a few seconds before routing is active
- **Ambiguity edge cases**: some inputs will be genuinely ambiguous regardless of workspace context (e.g., "fix the problem" with multiple active features at the same edge) — the clarification path must be fast and not annoying

### Neutral

- Methodology operations themselves are unchanged — only invocation changes
- Existing command-syntax invocation remains valid — `/gen-gaps`, `/gen-start --auto` etc. continue to work as before

---

## Implementation Notes

**`/gen-genesis` command** (`.claude/commands/gen-genesis.md`):
- Reads `specification/core/GENESIS_BOOTLOADER.md`
- Reads all active feature vectors and their current edges
- Builds personalised routing table
- Emits session confirmation
- Activates NL dispatch mode for the session

**`intent_routed` event type**:
- Add to `KNOWN_EVENT_TYPES` in `test_integration_uat.py` (both imp_claude and imp_codex)
- Add to `fd_classify.py` `EVENT_CLASSIFICATIONS` map
- Add to `migrate_events_v1_to_v2.py` known types

**REQ-UX-008 feature vector** (`REQ-F-UX-002`):
- Tracks implementation of this ADR
- At `requirements` edge — design and code work still pending
- Acceptance criteria include: routing confidence thresholds operational, `intent_routed` events emitted, cold-start guarantee via `/gen-genesis`

---

## Appendix: The Bootloader as Routing Vocabulary

The bootloader (§VII) defines eight functional units:

| Functional Unit | Methodology Verb | Default NL Pattern |
|----------------|-----------------|-------------------|
| `sense` | Observe workspace health | "what's broken", "check", "health" |
| `evaluate` | Run convergence checks | "find gaps", "coverage", "validate" |
| `iterate` | Advance a feature edge | "fix", "work on", "iterate", "improve" |
| `route` | Select next feature/edge | "what's next", "go", "continue", "start" |
| `propose` | Spawn new feature vector | "new feature", "add", "create" |
| `emit` | Record state to event log | (internal — not user-facing) |
| `classify` | Categorise signal/intent | "what kind of issue is X" |
| `decide` | Human gate / review | "review", "approve", "reject" |

These units are F_D-categorised in the bootloader. The NL routing table is their natural language surface — making the methodology's own vocabulary the user interface.
