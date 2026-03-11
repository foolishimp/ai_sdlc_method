# Upgrade Plan: imp_gemini v2.8 → v3.0 Parity

**Objective**: Bring `imp_gemini` to the same level of completion as `imp_claude` (v3.0), implementing the full OpenLineage-wrapped event taxonomy, decoupled engine logic, Hamiltonian metrics ($H = T + V$), and human accountability gates.

---

## Phase 1: Core Models & Event Taxonomy (ADR-S-011, ADR-S-012)
- **Implement `ol_event.py`**: Port the OpenLineage constructor from `imp_claude`.
  - Support `causation_id` and `correlation_id` on every event.
  - Implement the semantic event map (`IterationStarted`, `EdgeConverged`, etc.).
  - Add the `normalize_event` compatibility layer for reading legacy flat events.
- **Update `models.py`**:
  - Add Hamiltonian fields (`hamiltonian_T`, `hamiltonian_V`) to `InstanceNode` and `IterationRecord`.
  - Update `EngineConfig` to include v3.0 timeouts and budget constraints.
  - Implement `SpawnRequest` and `FoldBackResult` dataclasses.

## Phase 2: Engine Decoupling & Metrics (ADR-019, ADR-S-020)
- **Refactor `engine/iterate.py`**:
  - Decouple `iterate_edge()` from lifecycle decisions (spawn, fold-back).
  - Implement `run_edge()` as the orchestrator that detects spawn conditions.
  - Integrate $T$ (cumulative iteration count) and $V$ (current delta) tracking.
- **Implement `fd_spawn.py`**:
  - Port deterministic recursive spawn logic with time-box support.
  - Implement `link_parent_child` and `fold_back_child`.

## Phase 3: Internal Utilities & State Detection (REQ-UX-005)
- **Update `internal/workspace_state.py`**:
  - Implement `detect_workspace_state` with v3.0 states: `STUCK`, `ALL_BLOCKED`, `NEEDS_CONSTRAINTS`.
  - Add `verify_genesis_compliance` to check bootloader markers and graph invariants.
  - Implement `verify_spec_hashes` (REQ-EVOL-004) for spec-workspace consistency.
  - Port `project_instance_graph` for derived state projection.

## Phase 4: Human Accountability & Commands (REQ-EVAL-003)
- **Implement `human_audit.py`**:
  - Structured `human_gate_entered` and `human_decision` events.
  - Decision types: `approve`, `reject`, `override`, `defer`.
  - Attribution guard (rejects AI identities for human decisions).
- **Update Commands**:
  - `status.py`: Update `STATUS.md` generator to include $H = T + V$ table and diagnostic patterns.
  - `review.py`: Extend to support human gate decisions, not just feature proposals.
  - `start.py`: Integrate v3.0 state detection and auto-selection of the next edge.

## Phase 5: Validation & Dogfooding
- **Port Tests**: Adapt `imp_claude` v3.0 unit and integration tests.
- **Self-Convergence**: Run `imp_gemini` engine against its own codebase to verify delta=0.
- **Compliance Audit**: Run `/gen-status` and verify 100% methodology compliance.
