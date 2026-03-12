# /gen-genesis - Refresh Genesis Context and Activate NL Routing

Load the Genesis Bootloader into active context, read current workspace state, and
activate natural language intent routing. Run this at the start of any session to
restore full NL dispatch without needing to remember command names or flags.

<!-- Implements: REQ-UX-008 (Natural Language Intent Dispatch) -->
<!-- Implements: REQ-UX-001 (State-Driven Routing), REQ-UX-002 (Progressive Disclosure) -->

## Usage

```
/gen-genesis
```

No arguments. This is the session bootstrap command.

## Instructions

### Step 1: Load the Bootloader

Read `specification/core/GENESIS_BOOTLOADER.md`. This is the axiom set that constrains
all reasoning within this session. Do not summarise or paraphrase — load it as standing
context. If the file is missing, fall back to the bootloader section in `CLAUDE.md`.

The bootloader defines:
- Four primitives (Graph, Iterate, Evaluators, Spec+Context)
- The iterate() function and event stream substrate
- Eight functional units (evaluate, construct, classify, route, propose, sense, emit, decide)
- Functor encoding (F_D / F_P / F_H)
- The gradient: delta(state, constraints) → work
- Processing phases (reflex → affect → conscious)

### Step 2: Read Workspace State

Read the following to build a personalised routing context:

1. **Active features** — all `.ai-workspace/features/active/*.yml`
   - For each: feature ID, title, current edge (first non-converged trajectory entry)
2. **Completed features** — list `.ai-workspace/features/completed/` (count only)
3. **Last 10 events** — tail of `.ai-workspace/events/events.jsonl`
   - Identify the most recently touched feature and edge
4. **Pending proposals** — list `.ai-workspace/reviews/pending/PROP-*.yml` if any
5. **Project name** — from `.ai-workspace/context/project_constraints.yml` or directory name

### Step 3: Build the NL Routing Table

Construct a routing table personalised to the current workspace. Each entry maps a
natural language pattern to a concrete command invocation resolved from workspace state.

Standard patterns (always present):

| Natural Language | Routes To | Basis |
|-----------------|-----------|-------|
| "what's broken" / "health check" / "check" | `/gen-status --health` | Bootloader §VIII (tolerances as sensors) |
| "where am I" / "status" / "show progress" | `/gen-status` | REQ-UX-003 |
| "find gaps" / "coverage" / "what's missing" | `/gen-gaps` | REQ-TOOL-005 |
| "release" / "ship it" | `/gen-release` | Graph terminal edge |
| "start" / "go" / "continue" / "next" | `/gen-start --auto` | REQ-UX-001 |
| "new feature" / "add feature" / "create feature" | `/gen-spawn --type feature` | REQ-FEAT-001 |

Workspace-personalised entries (generated from active features):

For each active feature F with current edge E, add:

| Natural Language | Routes To |
|-----------------|-----------|
| "fix {F.title}" / "work on {F.id}" / "iterate {F.id}" | `/gen-iterate --feature {F.id} --edge {E}` |
| "what does {F.id} need" | `/gen-trace --feature {F.id}` |

For each pending proposal P, add:

| Natural Language | Routes To |
|-----------------|-----------|
| "review {P.proposal_id}" / "approve {P.title}" | `/gen-review-proposal --show {P.proposal_id}` |

### Step 4: Activate and Confirm

Output the following:

```
═══ GENESIS ACTIVE ═══
Bootloader: v{version} loaded
Project:    {project_name}
State:      {detected state from workspace}

Active Features ({n}):
  {F.id}  "{F.title}"          → {current_edge} (iter {n})
  ...

Completed: {n} features

Routing active. You can use natural language:
  "what's broken?"        → /gen-status --health
  "fix {title}"           → /gen-iterate --feature {id} --edge {edge}
  "find gaps"             → /gen-gaps
  "go" / "next"           → /gen-start --auto
  ...{workspace-personalised entries}

Type anything. Genesis will route it.
═══════════════════════
```

### Step 5: Enter NL Dispatch Mode

After this command completes, treat all subsequent user input as natural language
intent until the session ends or `/gen-genesis` is re-run.

**Routing algorithm** (apply to every message):

1. **Match against routing table** (exact and fuzzy). If confidence ≥ 0.85: route silently
   and execute. Show what you routed to as a one-liner before executing:
   ```
   → /gen-iterate --feature REQ-F-SENSE-002 --edge requirements
   ```

2. **If 0.5 ≤ confidence < 0.85**: show two options and ask which:
   ```
   Did you mean:
     1. /gen-iterate --feature REQ-F-SENSE-002 --edge requirements
     2. /gen-status --health
   ```

3. **If confidence < 0.5**: ask a single minimal clarification question. Do not show
   the full command menu — one question only.

4. **Emit `intent_routed` event** for every routed dispatch (confidence ≥ 0.85):
   ```json
   {"event_type": "intent_routed", "timestamp": "{ISO}", "project": "{name}",
    "data": {"input": "{user text}", "routed_to": "{command}", "confidence": 0.95,
             "feature": "{id or null}", "edge": "{edge or null}"}}
   ```

**Never ask the user to remember a command name.** If they say "fix the health wiring",
route it. If they say "what's next", derive it from workspace state and route it.

## Design Rationale

The bootloader contains the methodology's axioms. Loading it makes the LLM reason within
the formal system rather than pattern-match templates. The workspace state personalises
the routing — "fix it" resolves to a specific feature and edge, not a generic command.

Together they give Claude enough context to act as the NL dispatch layer described in
REQ-UX-008: the user narrates, the system routes, the F_D processes execute.

The `intent_routed` event closes the observability loop: every NL dispatch is recorded
in the event log, making the routing auditable and replayable.

## Cold Start vs Warm Session

| Condition | What gen-genesis does |
|-----------|----------------------|
| Cold start (no prior context) | Loads bootloader + full workspace state — full routing table built |
| Mid-session (context exists) | Re-reads workspace state — refreshes personalised entries |
| After long session (context compressed) | Re-loads bootloader axioms — prevents axiom drift |

Run `/gen-genesis` whenever you notice routing degrading or after context compression.
