# Design-Tier Requirements - imp_codex

**Version**: 1.0.0
**Date**: 2026-03-09
**Tier**: Design (Codex-specific - technology-bound)
**Spec parent**: `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`

---

## Purpose

This document captures Codex-specific design requirements that refine the shared spec without changing it. These requirements exist because the Codex tenant now has an executable runtime surface (`imp_codex/runtime/`) with concrete command, event, and workspace contracts that cannot live in the platform-agnostic specification.

**Traceability tier rule**:
- `REQ-*` keys in `specification/requirements/` remain the shared spec contract.
- `REQ-F-CDX-*`, `REQ-NFR-CDX-*`, `REQ-DATA-CDX-*`, `REQ-BR-CDX-*` are Codex design-tier requirements defined here.

The design intent is not to fork the methodology. The goal is to state the Codex binding points explicitly enough that parity work against `imp_claude/` has a stable local target.

---

## 1. Executable Runtime Boundary (CDX Series)

### REQ-F-CDX-001: Runtime Command Parity

**Spec parent**: REQ-TOOL-001, REQ-ITER-001, REQ-UX-001

The Codex tenant shall expose an executable runtime entry point that covers the same operational surface as the command set documented in `imp_codex/code/commands/`.

**Acceptance**:
- `python -m imp_codex.runtime` exposes `start`, `init`, `iterate`, `status`, `review`, `spawn`, `fold-back`, `gaps`, `release`, `trace`, and `checkpoint`.
- Each subcommand returns machine-readable JSON to stdout.
- Command names map directly to Codex workflow intent, even when the human-facing trigger is natural language rather than slash-command syntax.

**Traces To**: `runtime/__main__.py`, `runtime/commands.py`

---

### REQ-F-CDX-002: Event-First Projection Writes

**Spec parent**: REQ-EVENT-001, REQ-EVENT-002, REQ-TOOL-003

Every mutating runtime command shall treat the event log as the causal record and projections as derived outputs.

**Acceptance**:
- `gen_init`, `gen_iterate`, `gen_review`, `gen_spawn`, `gen_fold_back`, `gen_checkpoint`, `gen_gaps`, and `gen_release` append RunEvents before returning.
- Feature vectors, `STATUS.md`, task views, and gap reports are rewritten from runtime projection helpers rather than manually maintained in parallel.
- No command stores an independent "current state" variable outside the event log plus replay-derived documents.

**Traces To**: `runtime/events.py`, `runtime/projections.py`, `runtime/commands.py`

---

### REQ-F-CDX-003: Explicit Human Gate Contract

**Spec parent**: REQ-EVAL-003, REQ-UX-005, REQ-SUPV-002

Human-required edges shall remain pending until a separate human decision is recorded.

**Acceptance**:
- `gen_iterate()` marks an edge `pending_review` when required deterministic/agent evaluators pass but a human evaluator is still missing.
- `gen_review()` is the only runtime entry point that can approve, reject, or refine a pending human gate.
- Approval on a zero-delta review can emit `ConvergenceAchieved`; rejection or refinement returns the edge to a non-converged state.

**Traces To**: `runtime/commands.py:gen_iterate`, `runtime/commands.py:gen_review`

---

### REQ-F-CDX-004: Tenant-Pinned Compatibility Surface

**Spec parent**: REQ-CTX-002, REQ-TOOL-005

The Codex tenant shall be allowed to pin compatibility copies of shared spec documents when local tests or design interpretation need a stable surface that cannot be enforced by editing the shared spec tree from the Codex tenant.

**Acceptance**:
- `imp_codex/tests/conftest.py` treats `imp_codex/.spec_compat/` as a tenant-owned compatibility layer.
- Shared docs are mirrored into `.spec_compat/` only when the tenant has not already pinned a tracked override.
- Tests that validate tenant compatibility read from `.spec_compat/`, not directly from the nested shared spec paths.

**Traces To**: `imp_codex/tests/conftest.py`, `imp_codex/.spec_compat/`

---

### REQ-F-CDX-005: Workspace Root Aware Bootstrap

**Spec parent**: REQ-TOOL-012, REQ-TOOL-014, REQ-TOOL-015

The Codex runtime shall treat `.ai-workspace/` as a project-level artifact rooted at the provided project root, while tenant-specific context remains under `.ai-workspace/codex/`.

**Acceptance**:
- `bootstrap_workspace(project_root)` creates `.ai-workspace/` beneath `project_root`, not beneath a hard-coded tenant path.
- Codex-specific context files live under `.ai-workspace/codex/context/`.
- Shared projections (`events/`, `features/`, `tasks/`, `snapshots/`) remain project-scoped rather than tenant-scoped.

**Traces To**: `runtime/paths.py`

---

### REQ-F-CDX-006: CONSENSUS Review-Cycle Projection

**Spec parent**: REQ-F-CONSENSUS-001, ADR-S-025

The Codex tenant shall implement CONSENSUS review state as a replay-derived projection keyed by `review_id` and `cycle_id`, rather than by a separate mutable review-state artifact.

**Acceptance**:
- A `consensus_requested` event opens a cycle with explicit `review_id` and `cycle_id`.
- Material review reset creates a new `cycle_id`; prior-cycle votes no longer count.
- Quorum, participation, gating comments, and terminal outcome can be reconstructed from events alone.

**Traces To**: `design/CONSENSUS_OBSERVER_DESIGN.md`, `design/adrs/ADR-CG-010-consensus-observer-review-cycle-projection.md`

---

### REQ-F-CDX-007: Released-Runner Self-Host Bootstrap

**Spec parent**: REQ-TOOL-004, REQ-ITER-001, REQ-SUPV-002

The Codex tenant shall support self-hosting through a released-runner bootstrap model, where a released Genesis Codex runtime supervises the workspace of the next in-development Genesis Codex version.

**Acceptance**:
- The active supervisory runner is a released or pinned Codex Genesis artifact, not the mutable development head it is supervising.
- The development target owns its own `.ai-workspace/`, event log, feature vectors, and release history.
- Promotion from development target to active runner occurs only through a released version boundary.
- The CLI, engine, and provider bridge responsibilities are documented separately enough that self-host supervision does not depend on in-place self-modification of the active engine.

**Traces To**: `design/SELF_HOST_BOOTSTRAP_DESIGN.md`, `design/CODEX_GENESIS_DESIGN.md`

---

### REQ-F-CDX-008: Logical Engine Contract Over Commands, Skill Behaviors, and Runtime Helpers

**Spec parent**: REQ-ITER-001, REQ-TOOL-001, REQ-SUPV-002

The Codex tenant shall treat the engine as a logical contract realized jointly by commands, reusable skill behaviors, runtime helpers, and the Codex session, rather than requiring a separate standalone engine service.

**Acceptance**:
- Command routing, reusable construct/evaluate/review behaviors, and runtime replay/projection authority are documented as distinct responsibilities.
- Durable state authority remains with event/projection helpers even when construction happens in-session.
- The tenant design does not require a standalone daemon or subprocess transport in order to claim it has an engine.
- Self-host bootstrap may use a released command/skill/runtime bundle as the runner boundary.

**Traces To**: `design/COMMAND_SKILL_ENGINE_MODEL.md`, `design/FRAMEWORK_COMPARISON_ANALYSIS.md`, `design/FUNCTOR_FRAMEWORK_DESIGN.md`

---

## 2. Non-Functional Requirements

### REQ-NFR-CDX-001: Deterministic Command Output Shape

**Spec parent**: REQ-TOOL-001, REQ-EVENT-002

Runtime commands shall return stable, inspectable JSON structures so Codex sessions and tests can consume them without bespoke parsing per command.

**Acceptance**:
- All runtime subcommands serialize plain JSON objects.
- File references, run IDs, status summaries, and evaluator summaries are returned with stable key names.
- Failure cases raise explicit Python exceptions rather than printing ad hoc text blobs.

**Traces To**: `runtime/__main__.py`, `runtime/commands.py`

---

## 3. Data Requirements

### REQ-DATA-CDX-001: OpenLineage-Normalized Event Payload

**Spec parent**: REQ-EVENT-003, ADR-S-011, ADR-S-012

The Codex runtime shall emit canonical RunEvents and normalize legacy rows into one internal event view.

**Acceptance**:
- New events are emitted as OpenLineage-style RunEvents with SDLC semantics carried in facets.
- `load_events()` normalizes both legacy and RunEvent rows into a common `NormalizedEvent`.
- Runtime logic reads normalized fields (`semantic_type`, `feature`, `edge`, `delta`, `status`) instead of branching on raw schema version.

**Traces To**: `runtime/events.py`

---

### REQ-DATA-CDX-002: Consensus Review Event Vocabulary

**Spec parent**: REQ-F-CONSENSUS-001, ADR-S-025

The Codex tenant shall bind CONSENSUS review semantics to an explicit event vocabulary that is sufficient to reconstruct each review cycle deterministically.

**Acceptance**:
- The tenant event model defines `consensus_requested`, `comment_received`, `comment_dispositioned`, `vote_cast`, `review_reopened`, `consensus_reached`, and `consensus_failed`.
- Every event includes `review_id`; cycle-scoped events include `cycle_id`.
- Vote and disposition payloads carry enough asset-version context to enforce replay-safe reset behavior.

**Traces To**: `design/CONSENSUS_OBSERVER_DESIGN.md`, `design/adrs/ADR-CG-010-consensus-observer-review-cycle-projection.md`

---

## 4. Business Rules

### REQ-BR-CDX-001: Iteration Event Ordering

**Spec parent**: REQ-ITER-002, REQ-EVENT-001, REQ-EVENT-004

The Codex runtime shall preserve a simple causal ordering for iteration runs.

**Acceptance**:
- `IterationStarted` is emitted before `IterationCompleted`.
- `ConvergenceAchieved` is emitted only after a successful `IterationCompleted` or approved human review.
- `intent_raised` events caused by stuck iterations are causally linked to the completed iteration event.

**Traces To**: `runtime/commands.py:gen_iterate`, `runtime/commands.py:gen_review`

---

### REQ-BR-CDX-002: Consensus Observer Idempotency and Stale-Trigger Safety

**Spec parent**: REQ-F-CONSENSUS-001, REQ-SUPV-002

The Codex consensus observer/relay package shall be stateless and replay-safe. Trigger context is advisory only until current review state is rehydrated from the event log.

**Acceptance**:
- Observer triggers include `observer_id`, `trigger_reason`, `review_id`, `cycle_id`, `artifact`, and `source_run_id`.
- A stale or malformed trigger causes a no-op exit rather than review mutation.
- Reviewer loops do not emit terminal consensus outcomes directly; only the instigator loop may emit `consensus_reached` or `consensus_failed`.
- Review progression is driven by replay-derived local invariants over review-cycle events, not by imperative cross-component sequencing.

**Traces To**: `design/CONSENSUS_OBSERVER_DESIGN.md`, `design/adrs/ADR-CG-010-consensus-observer-review-cycle-projection.md`

---

## 5. Coverage Note for /gen-gaps

This file exists so Codex-specific runtime and design work can carry first-class design-tier traceability without forcing Codex transport details into the shared spec. If future Codex code or tests use design-tier requirement tags, this document is the anchor.

---

## Change Log

- `1.3.0` (2026-03-09): Added logical engine contract requirement over commands, reusable skill behaviors, and runtime helpers.
- `1.2.0` (2026-03-09): Added released-runner self-host bootstrap requirement for Codex.
- `1.1.0` (2026-03-09): Added Codex design-tier requirements for review-cycle projection, consensus event vocabulary, and stale-trigger safety.
- `1.0.0` (2026-03-09): Initial Codex design-tier requirement set covering runtime command parity, event-first projection writes, explicit human review, tenant-pinned compat docs, workspace rooting, canonical JSON outputs, normalized event data, and iteration ordering.
