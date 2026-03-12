# Specification — genesis_manager

This directory contains the product specification for **genesis_manager** — the builder supervision console for Genesis.

Everything here is **tech-agnostic** (WHAT the product must do). Implementation decisions (HOW) belong in `imp_<name>/`.

---

## Document Map

| Document | Path | Status |
|----------|------|--------|
| Intent | `INTENT.md` | Draft |
| Requirements | `requirements/REQUIREMENTS.md` | Pending |
| Feature Vectors | `features/FEATURE_VECTORS.md` | Pending |
| UX | `ux/UX.md` | Draft |
| UAT Test Cases | `verification/UAT_TEST_CASES.md` | Pending |

---

## Derivation Hierarchy

```
INTENT.md                    ← anchor: the why
    ↓
requirements/REQUIREMENTS.md ← WHAT the system must do (REQ-GM-* keys)
    ↓
features/FEATURE_VECTORS.md  ← WHICH buildable units (dependency DAG)
    ↓
ux/UX.md                     ← user journeys, wireframes, validation
    ↓
verification/UAT_TEST_CASES.md ← acceptance contract (BDD-style)
```

---

## Key Concepts

### Primary User
A person building projects through Genesis — supervising an autonomous builder, not running a PM dashboard.

### Top-Level Work Areas
1. **Projects** — navigation and attention signals
2. **Overview** — one-screen project status
3. **Supervision** — active work monitoring, human gates
4. **Evidence** — gap analysis, traceability, run history
5. **Control** — command surface (start, iterate, approve, repair)
6. **Release** — ship/no-ship decision surface

### Product Invariant
Every visible technical identifier is a navigation handle into deeper context.

### Canonical Detail Pages
Project · Feature · Decision · Run · Requirement · Artifact/Module

### UX Contract (see `ux/UX.md`)
Ten UX principles govern all implementation decisions:
1. Context before substrate
2. Plain language leads, technical identifiers anchor
3. Every claim needs an adjacent evidence path
4. Summary first, drill-through always available
5. Navigability is a product invariant
6. Actionability beats exhaustiveness
7. Safe control must be explicit
8. Exceptions outrank completeness
9. One project is primary, many projects are supported
10. Consistency of meaning over visual novelty

---

## ADRs

Spec-level decisions go in `adrs/ADR-GM-*`.
