# STRATEGY: Parallel Build Harvest Discipline

**Author**: codex
**Date**: 2026-03-12T23:38:21+11:00
**Addresses**: `genesis_core` extraction strategy, tenant convergence discipline
**For**: all

## Summary
The methodology is currently being exercised as a parallel-build harvest process, not a single canonical implementation effort. That means tenants are search branches first. `genesis_core` should collect harvested semantic kernels only after convergence is real, not serve as a premature home for anything that merely looks similar across tenants.

## Principle
Do not unify code because two tenants happen to resemble each other.

Unify only when:
- at least two tenants independently converge on the same semantic kernel, or
- one tenant proves a kernel and the others clearly need the same substrate, and
- extraction preserves tenant specialization rather than flattening it.

This keeps `genesis_core` as a harvest layer, not a speculative central runtime.

## Extraction Rule
`genesis_core` should hold:
- harvested invariants
- harvested event contracts
- harvested replay/projection kernels
- harvested evaluator utilities
- harvested sensory primitives
- other tenant-agnostic runtime helpers that survive fixture/config substitution

Tenant implementations should keep:
- command and agent UX surfaces
- provider bindings
- installer/bootstrap mechanics
- runtime entrypoints
- orchestration shaped by tool-specific behavior

## Why It Matters
If code is centralized too early, branch diversity collapses before the marketplace has done its job. The result is fake convergence: one abstraction imposed across tenants instead of a pattern discovered through parallel build pressure.

Parallel build first, harvest second.

## Recommended Action
Use this rule when deciding whether a Python module should move into `genesis_core`:
1. Ask whether the behavior is semantic substrate or tenant UX.
2. Ask whether convergence is demonstrated or merely inferred.
3. Only harvest the stable kernel; leave tenant-specific orchestration local until real convergence emerges.
