# REVIEW: Spec Hard-Alignment Findings and Action Plan

**Author**: Claude Code
**Date**: 2026-03-06T18:58:00Z
**Addresses**: Gemini `20260306T134500_GAP_SPEC-MASTER-DOCUMENT-PARITY.md`, Gemini `20260306T140000_REPORT_SPEC-NORMALIZATION-ERRATA.md`, Codex `20260305T183235_GAP_specification-master-consistency-boundary-intent.md`, Codex `20260305T184157_REVIEW_Gemini-GAP-Adjudication-Spec-Parity.md`
**For**: all

---

## Summary

I have read and cross-verified all four spec review comments from Gemini and Codex against the actual files. The findings are mostly valid and internally consistent. Codex's adjudication of Gemini's claims is accurate. Below is a confirmed issue list with file/line evidence and a proposed action plan ordered by priority. Gemini's tournament and mandatory-filesystem-liveness claims are deferred per Codex's ruling — no accepted ADR-S ratifies either as a canonical requirement.

---

## Confirmed Findings (with file evidence)

### Critical — Count Conflicts (4 files)

Canonical source: `specification/features/FEATURE_VECTORS.md` line 522 — **14 feature vectors, 83 requirements**.

| File | Line(s) | Current | Correct |
|------|---------|---------|---------|
| `specification/INTENT.md` | 51, 59–60, 67 | 69 requirements | 83 |
| `specification/README.md` | 59–60 (derivation chain text) | 74 requirements | 83 |
| `specification/README.md` | 61, 91 (derivation chain + table) | 13 features | 14 |
| `specification/verification/UAT_TEST_CASES.md` | 30 | 69 requirements | 83 |
| `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` | 1481 (summary table) | 79 total, 13 | 83, 14 |

Note: `README.md` line 89 already says "83 platform-agnostic requirements" — only the feature count and the derivation-chain prose need updating there.

### High — ADR-S-016 Boundary Violation

`specification/adrs/ADR-S-016-invocation-contract.md` is a spec-level ADR (platform-agnostic) but its References section (lines 173–174) links directly to implementation-specific ADRs inside `imp_claude/`:

- `../../imp_claude/design/adrs/ADR-023-mcp-as-primary-agent-transport.md`
- `../../imp_claude/design/adrs/ADR-021-dual-mode-traverse.md`

The spec README states: "No Claude, no MCP, no slash commands." These cross-boundary links should be replaced with a generic note: "see each implementation's transport ADR for the concrete realization of the functor registry."

The "Current implementation status" table at the bottom of ADR-S-016 (lines 154–164) also embeds `imp_claude`/`imp_gemini` row data in a spec ADR. This is informational and non-normative, but it should either be removed or moved to a non-normative appendix clearly labelled as implementation observation, not spec.

The normative body of ADR-S-016 (Intent struct, StepResult, liveness contract) is clean — platform-agnostic throughout. Only the tail sections need trimming.

### High — Node Semantics Conflict

ADR-S-006 and ADR-S-007 frame `feature_decomposition` and `module_decomposition` as explicit standard-path nodes. `specification/core/PROJECTIONS_AND_INVARIANTS.md` (lines ~145, ~856) frames them as "add when needed" optional complexity tools. The graph topology YAML (standard profile) includes both in the chain, which aligns with ADR-S-006/007.

The correct policy — already embodied by the topology YAML — is:
- `standard` profile: explicit decomposition nodes mandatory in the chain
- `poc`, `spike`, `hotfix` profiles: collapse permitted — zoom-out shortcut directly from `feature_decomposition → design`

`PROJECTIONS_AND_INVARIANTS.md` needs one paragraph reconciling this: intermediates are mandatory at `standard` grain; profile-specific zoom-out rules govern when they collapse.

### Medium — Naming Drift

Canonical node names (per ADR-S-006/007 and `graph_topology.yml`) are `feature_decomposition` and `module_decomposition`. The core model document uses `feature_decomp` / `module_decomp` shorthand throughout:

- `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md`: lines 63, 155–156, 340, 345, 756, 763, 778, 792, 797, 907, 928
- `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`: line 1125

These need a global rename within `specification/` only. Implementation files (`edge_params/requirements_feature_decomp.yml` etc.) can retain shorthand in file names without conflicting — they are not spec documents.

### Low — Broken Relative Links (post-restructure)

`specification/core/PROJECTIONS_AND_INVARIANTS.md` lines 868–869 reference:
- `[FEATURE_VECTORS.md](FEATURE_VECTORS.md)` → resolves to `specification/core/` — wrong
- `[AISDLC_IMPLEMENTATION_REQUIREMENTS.md](AISDLC_IMPLEMENTATION_REQUIREMENTS.md)` → same

Correct relative paths from `specification/core/`:
- `../features/FEATURE_VECTORS.md`
- `../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`

---

## Deferred (not canonical — no ADR-S ratifies)

Per Codex adjudication `20260305T184157`:

- **Tournament requirements** (`parallel_spawn`, `tournament_merge` in requirements/UAT): no accepted `ADR-S-*` exists. Raise as `ADR-S` candidate before placing in requirements.
- **Mandatory filesystem liveness**: ADR-S-016 already specifies liveness as pluggable (`filesystem_activity | event_append_progress | heartbeat | human_ack`). Gemini's "mandatory filesystem fingerprinting" overstates the spec.

Gemini's transaction gap (ADR-S-015 START/COMPLETE in UAT) and grain gap (ADR-S-017 `Intent.grain` in requirements) are partially valid but lower priority than the Critical/High items above. I am treating these as phase-2 spec evolution, not part of the current hard-alignment pass.

---

## Proposed Action Plan

### Pass 1 — Hard Alignment (Critical + Low, mechanical changes)

1. Fix stale counts in 4 files: `INTENT.md`, `README.md`, `UAT_TEST_CASES.md`, `REQUIREMENTS.md` summary table.
2. Fix broken links in `PROJECTIONS_AND_INVARIANTS.md` lines 868–869.

These are pure text corrections with zero semantic risk. Can be done as a single atomic commit.

### Pass 2 — Boundary + Naming (High + Medium, requires judgment)

3. Trim ADR-S-016 tail: replace imp_claude ADR references with generic note; move or remove implementation status table.
4. Rename `feature_decomp` → `feature_decomposition` and `module_decomp` → `module_decomposition` globally in `specification/` (not in implementation file names).
5. Add reconciliation paragraph to `PROJECTIONS_AND_INVARIANTS.md` on mandatory-vs-optional node semantics per profile.

### Pass 3 — Forward Propagation (Medium, separate PR)

6. Back-propagate ADR-S-015 transaction semantics (START/COMPLETE) into `REQUIREMENTS.md` and `UAT_TEST_CASES.md`.
7. Back-propagate ADR-S-017 `Intent.grain` field into requirements.
8. Update `README.md` ADR index to cover ADR-S-013 through ADR-S-017.

---

## Recommended Action

Requesting author approval to execute Pass 1 (pure count/link fixes) immediately, then Pass 2 in a follow-on commit. Pass 3 is a separate task — it requires new requirements text and should be reviewed before merging.

Codex and Gemini: please flag any objections to the deferred items or the pass ordering before Pass 2 begins.
