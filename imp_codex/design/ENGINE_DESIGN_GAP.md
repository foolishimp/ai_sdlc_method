# Engine Design Gap Analysis - imp_codex

**Date**: 2026-03-09
**Priority**: High
**Feature**: REQ-F-ENGINE-001, REQ-F-FP-001, REQ-F-CONSENSUS-001, REQ-F-NAMEDCOMP-001

---

## What Exists

The Codex tenant is no longer design-only. `imp_codex/runtime/` provides a working executable baseline:

| Module | What it does | Status |
|--------|-------------|--------|
| `commands.py` | `gen_init`, `gen_iterate`, `gen_review`, `gen_spawn`, `gen_fold_back`, `gen_status`, `gen_trace`, `gen_gaps`, `gen_release`, `gen_checkpoint` | Working |
| `events.py` | OpenLineage-style RunEvent emission + normalization | Working |
| `projections.py` | Replay-derived state, routing, status, stuck detection, health | Working |
| `evaluators.py` | Deterministic checks + heuristic agent checks | Working, partial on F_P semantics |
| `traceability.py` | REQ inventory, context manifest, gaps, release, trace reports | Working |
| `paths.py` | Workspace bootstrap and tenant overlay layout | Working |
| `__main__.py` | JSON CLI wrapper | Working |

The runtime already covers:
- event emission,
- feature vector projection,
- explicit review boundaries,
- spawn and fold-back bookkeeping,
- replay-driven status and health,
- cross-artifact trace reports.

This means parity work should build on a real engine, not assume a blank slate.

---

## What Is Still Missing

### Gap 1: No Construct Path in the Runtime

`gen_iterate()` now records candidate artifact refs and hashes, but it still does not own candidate artifact construction. Artifact creation still lives in the interactive Codex session rather than in the executable runtime.

**What exists**:
- runtime can infer evaluator sets,
- runtime can emit iteration events,
- runtime can update feature vectors and projections,
- runtime can persist candidate artifact refs/hashes as part of the iteration record.

**What is needed**:
- a true construct action per edge,
- policy for which artifacts are required/optional for a given traversal,
- tighter linkage between candidate artifacts and evaluator execution beyond metadata recording.

**Why it matters**:
Without a construct contract, REQ-F-FP-001 remains design-tier only. The runtime can validate a candidate, but it cannot yet generate one as part of the same bounded unit of work.

---

### Gap 2: Agent Evaluation Is Heuristic, Not a True Codex F_P Relay Contract

`run_agent_checks()` performs useful file- and traceability-based heuristics, but it is not equivalent to a true probabilistic constructor/evaluator relay.

**What exists**:
- heuristic checks over requirements, design text, code/test tags, and constraint dimensions,
- deterministic summary into `delta` and evaluator payloads.

**What is needed**:
- a real Codex-side F_P invocation contract,
- bounded retries/timeouts for that contract,
- batched edge-level agent evaluation rather than only local heuristics.

**Why it matters**:
Today the runtime gives honest partial coverage of F_P semantics. It does not yet provide the deeper construct/evaluate behavior that Claude's design requirements were aiming at.

---

### Gap 3: No Executable Package Yet for CONSENSUS and Only a Baseline Named-Composition Package

The accepted spec and recent ADRs now include:
- `REQ-F-CONSENSUS-001` for multi-stakeholder review semantics,
- `REQ-F-NAMEDCOMP-001` for named composition libraries and intent-vector envelopes.

**What exists**:
- ordinary human review (`gen_review`),
- named composition registry in `graph/named_compositions.yml`,
- typed `intent_vector` payloads on stuck-iteration and gap-driven `intent_raised` events,
- profile and graph configuration infrastructure,
- tenant design package for the `CONSENSUS` observer in `design/CONSENSUS_OBSERVER_DESIGN.md` and `design/adrs/ADR-CG-010-consensus-observer-review-cycle-projection.md`.

**What is needed**:
- executable review publication, comment, disposition, vote, and replay commands,
- pure projection functions for review-cycle state and deterministic quorum math,
- explicit `CONSENSUS` review publication, roster, quorum, and failure semantics,
- invariant-driven review choreography rather than a monolithic consensus orchestrator,
- broader named composition execution beyond intent routing,
- richer lineage, parentage, and bounded project-state semantics around composition-carrying intents.

**Why it matters**:
Codex now has a concrete local design target for `CONSENSUS`, but not the executable package yet. The next slice is no longer "invent the design"; it is "implement the replay/projection surface the design already names."

---

### Gap 4: Workspace Root Enforcement Needs Structural Self-Checks

The runtime now warns when the caller points it at an implementation tenant rather than the real project root. What it still lacks is a stronger structural self-check layer.

**What exists**:
- root-relative bootstrap layout,
- tenant overlay under `.ai-workspace/codex/`,
- tenant-scope warning surfaced by `gen_init()`.

**What is needed**:
- stronger self-checks for nested or duplicate workspaces across sibling tenants,
- broader runtime coverage beyond `gen_init()` for root-scope guidance,
- explicit enforcement policy for when tenant-scoped bootstrap should hard-fail versus warn.

**Why it matters**:
This is the design-level difference between "the code can do the right thing if called correctly" and "the runtime enforces the methodology invariant."

---

### Gap 5: No Formal Released-Runner Self-Host Contract

The Codex tenant now has enough runtime surface to dogfood itself, but it still lacked an explicit rule for how the active runner and the development target should relate.

**What exists**:
- a working runtime,
- release manifest generation,
- project-scoped workspaces,
- stable event and projection contracts.

**What was missing**:
- a documented split between released runner and mutable dev target,
- a formal statement that self-hosting should use a released runner to supervise the next dev version,
- an explicit CLI / engine / provider bridge boundary for that bootstrap.

**Why it matters**:
Without this, dogfooding easily collapses into in-place self-modification, which blurs accountability boundaries and makes runner bugs, target bugs, and migration bugs hard to distinguish.

**Current design response**:
- `design/SELF_HOST_BOOTSTRAP_DESIGN.md` now defines the released-runner bootstrap model as the Codex tenant's canonical self-host pattern.

---

### Gap 6: No Explicit Reusable Skill-Behavior Layer

The Codex tenant has command specs, agent specs, and runtime helpers, but it still lacked an explicit statement of the reusable behavior layer between raw command triggers and one-off session reasoning.

**What exists**:
- command surface,
- prompt-layer agents,
- runtime helpers,
- strong interactive Codex tool access.

**What was missing**:
- a Codex-native model for "skills" that does not regress to v1 stage personas,
- a statement that the engine is a logical contract spanning commands, reusable behaviors, runtime helpers, and the session,
- a cleaner explanation of how self-hosting works without a mandatory separate service.

**Why it matters**:
Without this, design language keeps oscillating between:
- "the runtime is the engine"
- and "the session is the methodology"

Neither is precise enough by itself.

**Current design response**:
- `design/COMMAND_SKILL_ENGINE_MODEL.md` now defines the missing layer and reprices the engine as a logical contract rather than a mandatory process shape.

---

## Implementation Order

1. Define a construct contract for `gen_iterate()` that records candidate artifact paths and hashes.
2. Replace or augment heuristic agent checks with a real Codex F_P invocation boundary.
3. Tighten workspace-root enforcement from warning to structural self-check coverage.
4. Keep the released-runner self-host split explicit as command / skill / runtime / provider contracts harden.
5. Turn the reusable skill-behavior layer from design-only into explicit executable conventions.
6. Implement phase-2 extensions in order: `CONSENSUS` projection package first, then deepen named composition execution beyond typed intent routing.

---

## Verification

Current baseline verification:

```bash
python -m pytest -q imp_codex/tests
```

Runtime smoke path:

```bash
python -m imp_codex.runtime init --project-root .
python -m imp_codex.runtime iterate --project-root . --feature REQ-F-ENGINE-001 --edge "intent→requirements"
python -m imp_codex.runtime status --project-root .
```

Traceability smoke path:

```bash
python -m imp_codex.runtime trace --project-root . --req-key REQ-F-ENGINE-001
```

---

## What This Enables

Once these gaps are closed, the Codex tenant can stop treating the runtime as "projection and bookkeeping around an interactive session" and start treating it as a true hybrid methodology executor:
- session-side construction,
- runtime-side validation and replay,
- explicit human or consensus review,
- typed intent and composition outputs.
