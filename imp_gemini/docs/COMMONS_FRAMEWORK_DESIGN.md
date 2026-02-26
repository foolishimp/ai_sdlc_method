# Project Genesis: Commons Framework Design

**Date**: February 26, 2026
**Theme**: Unifying the Asset Graph Model Implementation (v2.8)

## 1. Context and Motivation

During the concurrent development of the `imp_gemini` (local CLI) and `imp_claude` (reference implementation) tenants, both agents independently arrived at complementary breakthroughs. Gemini pioneered pure-function state detection and recursive spawning, while Claude established industrial-grade strongly-typed data models and `$variable` resolution for constraint binding.

To prevent architectural drift and eliminate duplicated effort, we are formalizing the **Genesis Core** (`genesis_core/`). This acts as the "Standard Template Library" (STL) for the AI SDLC, providing the universal algorithms and data structures that all implementation tenants share.

## 2. Architecture: Core vs. Tenant

The architecture cleanly separates the **Universal Methodology** from the **Platform-Specific Bindings**.

### 2.1 The Genesis Core (`genesis_core/`)

The root-level `genesis_core` package contains only the domain-agnostic, platform-agnostic implementation of the Asset Graph Model.

*   **`models.py`**: Strongly-typed dataclasses (`IterationReport`, `FunctorResult`, `CheckResult`, `SpawnRequest`) ensuring schema safety ("eliminating Dict Blindness").
*   **`iterate.py`**: The `IterateEngine` algorithm. It accepts an `Asset`, a `Context[]`, and a list of generic `Functor` predicates, looping until convergence or delegating sub-problems via `SpawnRequest`.
*   **`state.py`**: The pure Event Sourcing implementation. `EventStore` handles safe, append-only persistence to `events.jsonl`. `Projector` handles the derivation of materialized views (e.g., Gantt charts, Status reports).
*   **`workspace_state.py`**: Pure-function, deterministic state detection (`UNINITIALISED`, `IN_PROGRESS`, `STUCK`, etc.) based on filesystem and event log inspection.
*   **`config_loader.py`**: Resolution logic for binding `$variables` in edge parameterisations to actual project constraints.
*   **`guardrails.py`**: Pre-flight invariant checks (e.g., dependency verification, policy enforcement) that block iteration before it starts if constraints are violated.

### 2.2 The Tenant Bindings (`imp_gemini/`, `imp_claude/`, `imp_gemini_cloud/`)

The implementation tenants become lightweight wrappers around `genesis_core`. They supply three things:

1.  **Functors**: Platform-specific predicates. 
    *   `imp_gemini` provides `GeminiFunctor` (Google GenAI API).
    *   `imp_claude` provides `ClaudeFunctor` (Anthropic Claude Code CLI).
    *   `imp_gemini_cloud` provides `VertexFunctor` (GCP Vertex AI).
2.  **Orchestrators (CLI/Cockpit)**: The UX layer that interacts with the user, parses arguments, and delegates to `genesis_core`.
3.  **Isolated Memory (`.ai-workspace/`)**: A strict Markov Boundary ensuring that dogfooding one tenant does not cross-contaminate the event log of another.

## 3. The Implementation Plan

1.  **Extract and Consolidate**: Move the unified best-of-breed logic from `gemini_cli` and `imp_claude` into the root `genesis_core/` package.
2.  **Refactor Tenants**: Update `imp_gemini` and `imp_claude` to remove their internal engine duplications and import exclusively from `genesis_core`.
3.  **Validate Invariants**: Run the combined E2E test suites for both tenants to ensure the shared core respects both local and industrial testing constraints.

## 4. Cloud Projection (`imp_gemini_cloud`)

Once the `genesis_core` is stable, projecting it into the cloud becomes a matter of swapping the persistence and execution layers within the tenant:

*   **State Projection**: The tenant implements a `CloudEventStore` that conforms to the `genesis_core` EventStore interface but writes atomically to **Firestore** instead of a local `events.jsonl`.
*   **Execution Projection**: The tenant wraps the `genesis_core` IterateEngine in a **Cloud Run** endpoint, triggered by Pub/Sub events.

This design guarantees that whether running locally on a laptop or globally on GCP, the underlying formal methodology is exactly the same.
