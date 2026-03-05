# GAP: Specification Master Consistency, Boundaries, and Forward Intent

**Author**: codex
**Date**: 2026-03-05T07:32:57Z
**Addresses**: `specification/` as the master contract for downstream design cleanup
**For**: all

## Summary
The spec is not yet internally consistent enough to act as a strict master baseline for design normalization. The highest-risk issues are contradictory requirement/feature counts across top-level spec docs, boundary-rule violations (spec says tech-agnostic while normative text embeds implementation-specific mechanisms), and conflicting semantics on whether intermediate nodes are mandatory vs discretionary. Resolve those first, then proceed with implementation design cleanup.

## Findings (Severity-Ordered)

### Critical
1. **Canonical counts conflict across master docs**
- Current source-of-truth appears to be **83 requirements / 14 feature vectors**:
  - `specification/features/FEATURE_VECTORS.md:522`
  - `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` (83 REQ headings)
- Contradictory older counts remain:
  - `specification/INTENT.md:51` / `:59` / `:67` (69 requirements)
  - `specification/README.md:59` / `:61` / `:90` (74 requirements, 13 features)
  - `specification/verification/UAT_TEST_CASES.md:30` (69 requirements)
  - `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md:1481` (79 total in summary table)

### High
2. **Boundary contract is self-contradictory**
- Spec README states strict tech-agnostic boundary:
  - `specification/README.md:5` (“No Claude, no MCP, no slash commands”)
- Spec ADR text includes implementation-specific mechanics as normative detail:
  - `specification/adrs/ADR-S-016-invocation-contract.md:15`, `:51`, `:173`

3. **Intermediate-node semantics drift (mandatory vs discretionary)**
- ADR-S-006/007 frame explicit decomposition nodes as standard-path structure:
  - `specification/adrs/ADR-S-006-feature-decomposition-node.md:41`, `:78`
  - `specification/adrs/ADR-S-007-module-decomposition-basis-projections.md:34`, `:112`
- `PROJECTIONS_AND_INVARIANTS` frames intermediates as “add when needed” complexity tool:
  - `specification/core/PROJECTIONS_AND_INVARIANTS.md:145`, `:856`

### Medium
4. **Naming taxonomy drift**
- Canonical names in ADRs use `feature_decomposition` / `module_decomposition`.
- Core/requirements examples still frequently use `feature_decomp` / `module_decomp` shorthands:
  - `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md:63`, `:155`
  - `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md:1125`

5. **Forward ADR coverage lag in spec map**
- `README.md` hierarchy/reference sections appear stale relative to S-013..S-017 acceptance:
  - `specification/README.md:39`, `:96` onward

### Low
6. **Broken local links**
- Broken relative references in:
  - `specification/core/PROJECTIONS_AND_INVARIANTS.md:868`
  - `specification/core/PROJECTIONS_AND_INVARIANTS.md:869`

## Boundary and Intent Resolution (Recommended)
1. **One canonical counter source**
- Declare canonical totals in one place (requirements count, feature-vector count, ADR coverage), then reference it from `README`, `INTENT`, and `UAT_TEST_CASES`.

2. **Spec boundary rule (normative)**
- Keep spec normative text platform-agnostic.
- Permit implementation examples only as non-normative examples, clearly labeled.

3. **Node semantics reconciliation**
- Define explicit policy: which projection profiles require explicit decomposition nodes and which may collapse them.
- Ensure `AI_SDLC_ASSET_GRAPH_MODEL`, `PROJECTIONS_AND_INVARIANTS`, `ADR-S-006`, `ADR-S-007`, and requirements text use the same rule language.

4. **Canonical naming freeze**
- Freeze canonical node names (`feature_decomposition`, `module_decomposition`, `basis_projections`) and explicitly document any legacy aliases as non-canonical compatibility labels.

5. **Spec consistency gate before merge**
- Add checks for:
  - stale count literals (69/74/79/13)
  - broken relative links
  - boundary lint violations (platform-specific normative text)
  - canonical naming consistency

## Recommended Action
1. Execute a spec-only normalization pass for Findings 1–3 before any broad design cleanup.
2. Run naming/link/map cleanup (Findings 4–6) in same PR if possible.
3. Freeze a “spec master ready” checkpoint tag only after passing the consistency gate.
