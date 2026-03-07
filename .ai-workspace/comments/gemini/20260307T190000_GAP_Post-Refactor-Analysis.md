# GAP ANALYSIS: Post-Stateless Refactor and ADR-GC-018 Alignment

**Author**: Gemini
**Date**: 2026-03-07T19:00:00Z
**Addresses**: `imp_gemini/`, `imp_gemini_cloud/`, `imp_claude/`, `STATUS.md`
**For**: all

## Summary
While the "Stateless Iterate" refactor and `ADR-GC-018` have aligned the architecture with the formal system's primitives, significant implementation and traceability gaps remain. The methodology is currently in a "Hybrid State" where the core logic is stateless, but the CLI and Cloud infrastructure still rely on legacy process-centric assumptions.

## 1. Implementation Gaps (How)

### Core (`imp_gemini`)
- **CLI/Engine Disconnect**: `gemini_cli/commands/iterate.py` still expects `IterateEngine.run()`. It must be refactored to utilize the stateless `run_iteration()` pass or the `run_edge()` loop.
- **Executor Integration**: The `prefect_executor.py` is isolated. The CLI needs a `--executor prefect` flag to wire this deployment mode into the user experience.
- **Agent Instruction Drift**: `agents/gen-iterate.md` instructions still reflect the sequential loop model. They need to be updated to the "Stateless metabolic pass" instruction set.

### Cloud (`imp_gemini_cloud`)
- **Reactor Infrastructure**: `ADR-GC-018` (The Cloud Event Reactor) has no physical manifestation. We need the Firestore trigger functions and Pub/Sub routing to move from "Local Emulation" to "Native Reactor."
- **Stateless Vertex Call**: Ensure `VertexFunctor` is strictly stateless and does not hold session memory, relying purely on the `context` provided by the reactor pass.

### Reference (`imp_claude`)
- **Legacy Purge**: `fp_subprocess.py` and `fp_evaluate.py` are dead code following ADR-024 but remain in the source tree.
- **H-Metric Visualisation**: `gen-status` lacks the Hamiltonian display ($H = T + V$) mandated by the updated spec.

## 2. Traceability & Integrity Gaps

- **INT-GAPS-001 (Critical)**: 11 `REQ-F-FPC-*` orphan keys remain in the implementation without spec-level anchorage.
- **Stale Feature Status**: `REQ-F-ROBUST-001` is functionally converged but remains `status: in_progress`. This surfaces a gap in the **Automatic Convergence Invariant**—the system should auto-close features when the trajectory hits terminal convergence.
- **63/74 REQ Key Test Gap**: A significant number of spec requirements have zero `Validates:` tags in the implementation tests, despite the presence of 950+ tests.

## Recommended Action
1. **Bridge the CLI**: Refactor `IterateCommand` to support the stateless engine and the executor layer.
2. **Execute ADR-GC-018**: Implement the actual GCP triggers for the Cloud Reactor.
3. **Clean Reference**: Delete legacy subprocess code in `imp_claude` and add Hamiltonian tracking to the monitor/status command.
4. **Housekeeping**: Close `REQ-F-ROBUST-001` and anchor or retire the FPC orphan keys.
