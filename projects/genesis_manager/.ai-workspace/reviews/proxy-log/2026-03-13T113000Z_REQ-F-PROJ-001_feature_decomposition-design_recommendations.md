# Proxy Decision — feature_decomposition→design_recommendations

**Decision**: approved
**Actor**: human-proxy
**Timestamp**: 2026-03-13T11:30:00Z
**Feature**: REQ-F-PROJ-001 (project-level design recommendations, applies to all MVP features)
**Edge**: feature_decomposition→design_recommendations
**Gate**: human_approves_design_order
**Artifact**: specification/design_recommendations/DESIGN_RECOMMENDATIONS.md

## F_H Criteria Evaluated

### Criterion 1: Phase ordering makes sense — nothing critical is scheduled late

**Evidence**:
- Phase 1 (PROJ) is the foundation — workspace model before anything else ✓
- Phase 2 (NAV + UX) parallelises the two infrastructure layers efficiently ✓
- Phase 3 (OVR + SUP + EVI) maximises parallelism with 3 work areas simultaneously ✓
- Phase 4 (CTL) correctly deferred until SUP defines the supervision surface ✓
- Critical path identified: PROJ → NAV → SUP → CTL — this is the correct minimum path to
  a working supervision+control loop (matches INTENT §core product questions 3, 5)
- REQ-F-EVI-001 (trust contract — question 6) is in Phase 3, parallel with SUP — correct,
  it doesn't need to block CTL

**Result**: PASS — ordering is sound; nothing critical is late

### Criterion 2: Cross-cutting concerns are complete — nothing important is missing

**Evidence**:
- WorkspaceReader (I/O layer): identified ✓ — centralises filesystem reads
- Canonical URL schema (ROUTES constant): identified ✓ — prevents link drift
- Live polling / useWorkspaceData hook: identified ✓ — single subscription model
- Event emission write serialisation (WorkspaceWriter): identified ✓ — highest-risk concern
- Component design system (shared primitives): identified ✓ — prevents per-feature reinvention
- Missing check: **authentication / session** — N/A, single-user no auth confirmed ✓
- Missing check: **error propagation across components** — partially covered by Error Boundaries
  in project_constraints; Error Boundaries are a design system concern, could be explicit.
  Advisory — not a blocker.

**Result**: PASS — five concerns cover the meaningful cross-cutting surface for this SPA

### Criterion 3: ADR areas correctly identified — no decisions deferred that shouldn't be

**Evidence**:
- All 4 mandatory constraint dimensions: RESOLVED ✓
- State management (Zustand vs alternatives): TBD with note that ADR-001 must precede Phase 3 ✓
- Router choice: TBD with Phase 2 timing ✓
- Workspace write protocol: TBD with explicit note that ADR-005 must precede CTL design ✓ — this
  is the right call; prematurely resolving it risks designing for a wrong constraint
- Workspace read protocol: TBD with spike recommendation ✓ — correct to flag before committing
- Component library: TBD with Phase 1 timing ✓ — early enough to unblock all phases

**Result**: PASS — ADR areas correctly named; none deferred past their natural resolution point

## Overall Decision

APPROVED. All three F_H criteria pass. Design recommendations are consistent with the
feature decomposition and the product intent. Phase ordering respects the DAG. Cross-cutting
concerns are complete. ADR areas are correctly timed.

## Review Instructions (for morning human review)

To dismiss: add `Reviewed: 2026-03-13` to this file.
To override: run `/gen-review --feature REQ-F-PROJ-001 --edge feature_decomposition→design_recommendations`
