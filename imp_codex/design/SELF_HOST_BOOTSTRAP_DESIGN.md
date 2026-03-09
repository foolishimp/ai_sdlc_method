# Codex Self-Host Bootstrap Design

**Version**: 1.0.0
**Date**: 2026-03-09
**Purpose**: Define how `genesis.codex` dogfoods itself safely across released and in-development versions
**Scope**: Codex tenant design only

---

## 1. Problem

Codex needs the same self-hosting posture already used in the Claude tenant:

- a **released** Genesis binding that is trusted to supervise work,
- an **actively developed** Genesis binding that is the target of that work,
- a clean promotion path from released runner to next released runner.

Without this split, the same mutable runtime becomes:

- the supervisor,
- the worker,
- the artifact under modification,
- and the release candidate.

That collapses accountability boundaries and makes failures difficult to interpret. A bug in the runner, a bug in the target, and a bug in migration logic all look the same.

---

## 2. Design Decision

Codex self-hosting uses a **two-lane bootstrap**:

```text
genesis.codex.commands+skills@1.0
  -> logical engine contract@1.0
  -> workspace: genesis-codex@1.1-dev
```

Meaning:

- `1.0` is the **released runner**. It is the active supervisory authority.
- `1.1-dev` is the **development target**. It is just another Genesis project from the runner's perspective.
- `1.1-dev` does not become the supervising runner until it has been released as `1.1.0`.

The next cycle repeats:

```text
genesis.codex.commands+skills@1.1.0
  -> logical engine contract@1.1.0
  -> workspace: genesis-codex@1.2-dev
```

This is the Codex tenant's canonical dogfood pattern.

---

## 3. Logical Split

The self-host model assumes a hard separation between four concerns, but they do
not have to be packaged as four standalone services.

### 3.1 Commands

Human-facing relay surface.

Responsibilities:
- parse command intent,
- collect flags and human input,
- render status and reports,
- trigger the correct methodology path.

### 3.2 Reusable Skill Behaviors

Stable reusable execution patterns shared across commands and edges.

Responsibilities:
- candidate construction,
- checklist/evaluation passes,
- review preparation,
- edge-specific procedural guidance.

Codex does not currently expose these as a separate `skills/` directory in
`imp_codex`, but the self-host model assumes the behavior contract exists.

### 3.3 Runtime Helpers

Deterministic durable substrate.

Responsibilities:
- replay events,
- rebuild projections,
- emit canonical events,
- generate trace and release artifacts,
- preserve authoritative state.

### 3.4 Codex Session / Provider Surface

Probabilistic fulfillment boundary.

Responsibilities:
- run Codex-native construction and reasoning,
- perform bounded artifact generation or high-context evaluation,
- hand candidate outputs back into the deterministic substrate.

The **engine** is the logical contract formed by these layers together, not
necessarily a separate binary.

---

## 4. Bootstrap Topology

The released runner and the development target must not share mutable authority.

### 4.1 Released Runner

The released runner is:

- installed or pinned at a released version,
- treated as operationally stable,
- allowed to supervise a separate target workspace.

Its job is to run:

- `start`,
- `iterate`,
- `review`,
- `gaps`,
- `trace`,
- `release`,
- and any future supervisory sagas

against the dev target workspace.

### 4.2 Development Target

The development target is:

- a Genesis project representing the next Codex version,
- event-sourced independently,
- free to mutate under supervision,
- not trusted to supervise itself until released.

The target contains:

- the `imp_codex/` work being changed,
- its own `.ai-workspace/`,
- its own feature vectors,
- its own release state.

### 4.3 Promotion Boundary

Promotion from target to runner occurs only when:

1. the target workspace converges on its planned release scope,
2. gaps are checked,
3. release artifact is created,
4. the release is cut as `vX.Y.Z`,
5. that released artifact becomes the next installed/pinned runner.

Until then, the target remains only a project under supervision.

---

## 5. Operational Flow

For `1.0 -> 1.1`:

1. Install or pin `genesis.codex@1.0.0` as the active runner.
2. Create a separate project/workspace for `genesis-codex@1.1-dev`.
3. Use `1.0.0` to initialize and supervise the `1.1-dev` workspace.
4. Express `1.1` work as normal feature vectors:
   - command/skill engine split
   - provider bridge contract
   - consensus observer
   - release hardening
   - self-host packaging
5. Run normal Genesis loops:
   - `start`
   - `iterate`
   - `review`
   - `gaps`
   - `trace`
6. When converged, create the release artifact:
   - `gen-gaps`
   - `gen-release --version 1.1.0`
7. Install/pin `1.1.0` as the new released runner.
8. Begin `1.2-dev` using `1.1.0`.

This is self-hosting by **released-runner supervision**, not self-modifying in-place execution.

---

## 6. Workspace and Repo Boundaries

The design does not require a specific monorepo layout, but it does require these conceptual boundaries:

### 6.1 Runner Artifact Boundary

The released runner must be identifiable as a distinct artifact:

- installed package,
- pinned checkout,
- tagged release directory,
- or equivalent immutable runtime reference.

The key invariant is that the active runner is not the mutable dev head.

### 6.2 Target Workspace Boundary

The target workspace must have:

- its own `.ai-workspace/`,
- its own event log,
- its own feature vectors,
- its own release history,
- its own context manifest.

The runner may supervise many targets, but each target remains a separate accountability domain.

### 6.3 Event Authority Boundary

Events emitted while building `1.1-dev` belong to the `1.1-dev` workspace, not to the released runner's own operational workspace.

The runner supervises; the target owns the work record.

---

## 7. Why This Is the Right Dogfood Model

This design preserves the methodology's core invariants:

- **event log authority**: each target has its own causal record
- **accountability boundaries**: the released runner stays stable while supervising change
- **immutable lineage**: promotion is new release lineage, not mutation of the runner's authority state
- **done vs done-done**: the next runner is not trusted because it exists; it is trusted because the current runner released it

It also makes failures interpretable:

- runner bug,
- target implementation bug,
- packaging bug,
- migration bug

can be distinguished by which side of the boundary they occur on.

---

## 8. Non-Goals

This design does **not** require:

- a single runtime process controlling both runner and target,
- in-place self-modification of the active supervising runtime,
- mutable upgrade of the engine while it is supervising the same workspace,
- special dogfood-only lifecycle semantics.

The target is simply another Genesis project, with the extra fact that its product is the next Genesis runner.

---

## 9. Immediate Codex Implications

Codex should now formalize:

1. commands as the thin human-facing adapter,
2. reusable skill behaviors as the stable prompt/runtime execution layer,
3. runtime helpers as the deterministic supervisory substrate,
4. the provider bridge as the probabilistic construction boundary,
5. release promotion as the only way a dev target becomes the next supervising runner.

This means the Codex tenant should optimize for:

- durable logical engine contracts,
- stable release artifacts,
- replay-safe target workspaces,
- and explicit promotion points.

That is the right self-host posture for `genesis.codex`.
