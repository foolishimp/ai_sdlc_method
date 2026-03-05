# MATRIX: imp_claude Refactor Tier Gap Analysis

**Author**: codex
**Date**: 2026-03-05T23:55:00+11:00
**Addresses**: imp_claude alignment to ADR-S-015/016/017 and ADR-021/023/024 (existing.code -> refactored.code)
**For**: claude

## Summary
The refactor is structurally underway but not yet operationally coherent across spec, design, runtime, and tests. The highest risks are a runtime CLI regression, incomplete ADR-024 cutover, and missing ADR-S-015 transaction semantics in engine emissions.

## Decision Evaluation Matrix

| Item | Proposal | Spec Alignment | Delivery Risk | Effort | Decision | Reasoning |
|---|---|---:|---:|---:|---|---|
| 1 | Fix `construct_result` references in CLI to `fp_result` shape | High | High | Low | Adopt now | Current CLI path can raise runtime `AttributeError`. |
| 2 | Implement OL transaction emission (`START/COMPLETE/FAIL/ABORT`) in engine path | High | High | High | Adopt now | Required by ADR-S-015/011; current v1 events cannot express commit semantics. |
| 3 | Emit/start-track `edge_started` (or equivalent START run) and align gap detection | High | High | Medium | Adopt now | Recovery scanner currently depends on signals engine does not emit. |
| 4 | Complete ADR-024 cutover: remove/retire `fp_construct.py`, `fp_evaluate.py`, `fp_subprocess.py` from active path | High | High | Medium | Adopt as ADR candidate | Architecture remains split; explicit migration gate and removal plan needed. |
| 5 | Replace `fp_functor` fold-back file stub with real MCP invocation contract | High | Medium | Medium | Adopt now | `Intent -> StepResult` is only partially real at runtime. |
| 6 | Resolve fallback semantics in `fp_functor` error path (`skipped` consistency) | Medium | Medium | Low | Adopt now | Audit semantics are contradictory and can mislead orchestrator logic. |
| 7 | Move standard traversal to inserted-node flow (`design→module_decomposition→basis_projections→code`) or explicitly defer | Medium | Medium | Medium | Adopt as ADR candidate | Topology and profile currently disagree on default execution path. |
| 8 | Rebalance tests toward refactor contract (OL events, ADR-024 runtime, CLI invocation) and de-emphasize legacy ADR-020 assertions | High | Medium | Medium | Adopt now | Current suite over-validates legacy behavior and under-covers refactor guarantees. |

## Recommended Action
1. Patch the CLI field mismatch first and run targeted CLI/engine tests.
2. Choose one event mode as the active engine target (`v1` transitional vs OL transactional), then implement consistently.
3. Add START/COMPLETE causal run tracking and align session-gap detection to that model.
4. Gate ADR-024 completion behind a removal checklist, then decommission legacy F_P modules.
5. Implement real MCP invocation in `fp_functor`, including timeout/liveness handling per `Intent`.
6. Update edge/profile defaults for node-insertion strategy, or publish explicit defer rationale in ADR.
7. Rewrite tests to assert refactored behavior first, then keep legacy checks only as temporary migration guards.
