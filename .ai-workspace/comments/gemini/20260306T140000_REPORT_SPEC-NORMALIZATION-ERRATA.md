# REPORT: Spec Normalization & Alignment Pass (Errata Guide)

**Author**: Gemini
**Date**: 2026-03-06T14:00:00Z
**Addresses**: Findings 1-6 (Codex), Gaps 1-5 (Gemini)
**For**: Methodology Author / Authorized Agent

## 1. Resolution of Canonical Counts (Critical)

The master specification is currently "split-brained." To resolve the 69/74/79/83 conflict, we must establish **Version 2.9.0** as the new count baseline.

**Action Item: Update `specification/README.md`**
*   Update line 90: `74 requirements` → `83 requirements`
*   Update line 90: `13 features` → `14 features`
*   Rationale: Synchronizes the README with the actual count in `AISDLC_IMPLEMENTATION_REQUIREMENTS.md`.

**Action Item: Update `specification/INTENT.md`**
*   Update summary table (lines 51-67) to reflect 83 requirements.

## 2. Normative Boundary Enforcement (High)

Several ADRs violate the "Tech-Agnostic" rule of the spec.

**Action Item: Errata for `specification/adrs/ADR-S-016-invocation-contract.md`**
*   Remove normative references to "Claude," "MCP," and "Slash commands."
*   Wrap implementation details in `[Example: ...]` blocks.
*   Rationale: Restores the spec as a platform-neutral contract.

## 3. Naming Taxonomy Freeze (Medium)

"Decomp" vs "Decomposition" drift must be eliminated.

**Action Item: Global Regex Sweep across `specification/`**
*   Replace all instances of `feature_decomp` with `feature_decomposition` (canonical).
*   Replace all instances of `module_decomp` with `module_decomposition` (canonical).
*   Update `AI_SDLC_ASSET_GRAPH_MODEL.md` and `AISDLC_IMPLEMENTATION_REQUIREMENTS.md` to ensure the 2.9.0 topology node names match.

## 4. Requirement Gap Closure (New v2.9.0 Primitives)

The detailed requirements docs must back-propagate recent ADR decisions.

**Action Item: Update `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`**
*   **Add REQ-ITER-004 (Transaction Boundary)**: "Implement START/COMPLETE transaction boundaries for all edge traversals."
*   **Add REQ-SUPV-004 (Liveness Signal)**: "Mandate pluggable liveness monitoring using filesystem fingerprinting as the local baseline."
*   **Add REQ-GRAPH-004 (Tournament Pattern)**: "Include parallel_spawn and tournament_merge nodes in the admissible transition registry."

## 5. UAT Scenario Synchronization (Medium)

**Action Item: Update `specification/verification/UAT_TEST_CASES.md`**
*   Add **UC-01-19: Crash Recovery**: "Given a START event with no COMPLETE, the system recovers the last valid input hash."
*   Add **UC-12-Tournament**: "Given a multi-tenant spawn, the arbiter correctly fold-backs the winning output hash."

## Conclusion

By executing these precise errata, we move the specification from a "Collection of Papers" to a **Technically Valid Master Document**. This enables true Spec-Driven Development, where any agent can rebuild the implementation from these requirements alone.
