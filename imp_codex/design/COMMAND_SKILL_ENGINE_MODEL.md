# Codex Command-Skill Engine Model

**Version**: 1.0.0
**Date**: 2026-03-09
**Purpose**: Define the Codex-native engine shape when the tenant is realized through Codex sessions, reusable skill behaviors, commands, and runtime helpers rather than a mandatory standalone engine service
**Scope**: Codex tenant design only

---

## 1. Problem

The Codex tenant already has:

- a strong command surface,
- a Codex session with first-class tool access,
- reusable prompt-layer command and agent specs,
- and runtime helpers for replay, events, projections, and reports.

What it does **not** need is a forced translation of the Claude transport model into a second mandatory standalone engine process.

The risk is architectural confusion:

- if "engine" means only `imp_codex/runtime/`, the tenant under-prices commands and the Codex session,
- if "engine" means only the live session, the tenant loses durable authority over events, projections, and release state.

The Codex-native answer is to treat the engine as a **logical contract**, not a required process shape.

---

## 2. Decision

For Codex, the methodology stack can be realized as:

```text
codex + commands + reusable skill behaviors + runtime helpers
```

with the following meaning:

- **Codex session**: the probabilistic constructive worker
- **commands**: ingress, routing, and human-facing workflow triggers
- **reusable skill behaviors**: stable execution patterns reused across commands and edges
- **runtime helpers**: durable event, replay, projection, traceability, and release substrate

Together, these realize the **logical engine contract**.

The engine is therefore not defined by "is there a separate daemon or binary?" It is defined by whether these invariants are held:

1. graph authority is coherent,
2. event authority is coherent,
3. projection authority is coherent,
4. convergence authority is coherent,
5. release authority is coherent.

If those five are coherent, the tenant has an engine even if the implementation is prompt-native and command-driven.

---

## 3. Layer Model

### 3.1 Commands

Commands are the stable human-facing trigger surface.

Examples:
- `start`
- `status`
- `iterate`
- `review`
- `gaps`
- `trace`
- `release`

Command responsibilities:
- normalize user intent into methodology operations,
- select or force the workflow path,
- gather explicit flags and human decisions,
- invoke the correct reusable behavior chain.

Commands are not themselves the full engine. They are the main ingress surface.

### 3.2 Reusable Skill Behaviors

Codex does not currently maintain a separate `skills/` package in `imp_codex`, but the tenant still needs the concept.

In this document, **skill behavior** means:

- a reusable, stable prompt/runtime behavior contract,
- shared across multiple commands or edges,
- small enough to be composed,
- not tied to one stage-specific persona.

Examples of skill-behavior roles:
- construct candidate artifact
- run agent-style checklist pass
- summarize delta
- perform review preparation
- apply edge-specific guidance
- prepare release or traceability report

The old v1 stage-specific skill model is not being revived. The Codex tenant uses **composable behaviors**, not many hard-coded stage personas.

### 3.3 Runtime Helpers

Runtime helpers remain the durable deterministic substrate.

Current examples:
- event emission
- replay
- projections
- traceability
- release reports
- workspace bootstrap

These do not need to own every constructive step to remain authoritative for durable state.

### 3.4 Codex Session

The live Codex session is the default F_P surface:
- reads workspace state,
- reasons over edge configs and context,
- constructs artifacts,
- uses tools,
- applies patches,
- hands results back into the deterministic substrate.

This is the data plane for ambiguous work.

---

## 4. Logical Engine Contract

The Codex engine is the combination of all pieces that preserve methodology invariants.

### 4.1 What the engine must own

Regardless of packaging, the engine must own:

- graph and edge legality
- feature and vector progression
- event write authority
- projection rebuild authority
- convergence determination
- release and traceability state

### 4.2 What the engine does not require

The engine does **not** require:

- a separate long-lived service
- a second CLI process
- nested subprocess transport like `claude -p`
- a hard split where all methodology logic moves into Python

Codex already has tool-calling inside the main session. The methodology should exploit that instead of emulating another platform's transport constraints.

---

## 5. Self-Host Implication

In the self-host bootstrap, a released runner can therefore be understood as:

```text
released command pack
  + released shared skill behaviors
  + released runtime helpers
  + released Codex binding conventions
```

supervising:

```text
next-version target workspace
```

This is still a real runner boundary even without a monolithic engine binary.

What matters is that the released supervisory contract is stable while the target workspace is mutable.

---

## 6. Relationship to Existing Runtime

This decision does **not** remove or weaken `imp_codex/runtime/`.

Instead it reprices it:

- `runtime/` is the deterministic substrate and replay authority
- command and agent specs are the reusable workflow surface
- the Codex session is the primary F_P constructor

So the right Codex statement is not:

> "the runtime is the entire engine"

It is:

> "the runtime is the durable deterministic part of the engine; the full engine is realized by commands, reusable skill behaviors, runtime helpers, and the Codex session together."

---

## 7. Design Consequences

### 7.1 Good consequences

- avoids overfitting to Claude transport
- keeps self-hosting lightweight
- preserves a strong deterministic substrate
- makes Codex-native tool access a first-class advantage

### 7.2 Required discipline

This only works if methodology authority is not scattered arbitrarily.

The tenant must keep:
- command semantics stable,
- reusable behaviors explicit,
- runtime helpers authoritative for durable state,
- release boundaries explicit.

If those drift into unrelated prompts, the logical engine dissolves.

---

## 8. Recommended Implementation Direction

The next Codex steps should be:

1. keep `commands` as the main user/relay interface,
2. define reusable skill-behavior contracts for construct/evaluate/review paths,
3. keep `runtime/` as event/projection/release authority,
4. treat "engine" as the logical composition of those layers,
5. avoid introducing a standalone service unless the current model demonstrably fails.

This is the Codex-native engine shape.
