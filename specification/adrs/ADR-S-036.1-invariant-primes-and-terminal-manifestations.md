# ADR-S-036.1: Invariant Primes and Terminal Manifestations

**Status**: Ratified
**Date**: 2026-03-12
**Amends**: ADR-S-036 (Invariants as Termination Conditions, Not Procedures)
**Deciders**: Jim (human principal)
**Proposed by**: Codex
**Tags**: methodology-core, invariants, conformance, ontology

---

## Summary

ADR-S-036 establishes that the methodology prescribes termination conditions, not procedures.
This amendment sharpens the ontology of the termination checklist by introducing a two-layer
model: **invariant primes** as the irreducible validity basis, and **terminal manifestations**
as the required evidence that those primes hold.

ADR-S-036's decision language is preserved unchanged. This amendment adds precision to the
checklist at the end of that ADR.

---

## Problem

ADR-S-036's terminal checklist mixes foundational conditions with derived evidence artifacts in
a single flat list. This creates ambiguity:

- `REQ threading` is a near-prime validity property — its absence means the workspace is
  structurally invalid.
- `STATUS.md current` is mandatory, but is better understood as a derived visibility artifact.
- `Proposals drafted` is the governance manifestation of homeostatic closure, not the same
  kind of thing as `Code exists`.

Without this distinction:
- Derived artifacts read as first-order invariants
- Implementations cannot clearly separate foundational checks from evidence checks
- Debate about "minimum invariants" recurs because the list blends basis and manifestation

---

## Amendment

### 1. Invariant Prime

An **invariant prime** is an irreducible validity condition of a Genesis workspace:

- Necessary for validity
- Not derivable from the other primes
- Path-independent
- Checkable from artifacts, projections, event stream, or explicit F_H judgment
- Stable across implementations and profiles

### 2. Terminal Manifestation

A **terminal manifestation** is a concrete required artifact, projection, or observable that
demonstrates one or more invariant primes hold at convergence.

This yields:
- **Primes** = validity basis (why the workspace is valid)
- **Manifestations** = required evidence layer (how you prove it)

### 3. The Prime Set

Five invariant primes for a converged Genesis workspace:

| Prime | Meaning |
|-------|---------|
| **Asset convergence** | Required stable assets exist and pass their required evaluators |
| **Traceability** | Lineage is correct across spec, feature vectors, code, tests, and review artifacts |
| **Observability** | The work is visible to the methodology through a complete enough event/projection record |
| **State legibility** | Workspace state is structurally valid, replayable, and machine-readable |
| **Homeostatic closure** | Detected gaps are classified, validated, and routed into governance/remediation paths |

### 4. Classification of ADR-S-036 Checklist

The terminal checklist from ADR-S-036, reclassified by layer and prime basis:

| ADR-S-036 item | Layer | Prime basis |
|----------------|-------|-------------|
| Code exists | Terminal manifestation | Asset convergence |
| Tests pass | Terminal manifestation | Asset convergence |
| REQ threading | Near-prime manifestation | Traceability |
| Feature vectors correctly formatted | Terminal manifestation | State legibility |
| Events emitted | Terminal manifestation | Observability |
| Gaps validated | Terminal manifestation | Homeostatic closure |
| Proposals drafted | Terminal manifestation | Homeostatic closure |
| STATUS.md current | Derived manifestation | Observability + State legibility |

`STATUS.md current` remains mandatory. Being a derived manifestation does not reduce its
requirement — it clarifies why it is required: as proof of Observability and State legibility,
not as a foundational condition in its own right.

`REQ threading` is listed as "near-prime" because it sits at the boundary: it is both a
concrete artifact check (grep for `# Implements:`) and a structural validity condition
(without it the traceability chain is broken). It should be treated as prime in practice.

### 5. Conformance Rule

A workspace is valid at convergence when:

1. **All invariant primes are satisfied** — the five primes above hold for all active features
   in scope
2. **All required terminal manifestations for the active methodology scope are present and
   accurate** — the concrete artifacts and projections exist and correctly reflect the primes

Both conditions are necessary. A workspace where all artifacts exist but are inaccurate (e.g.,
fabricated REQ tags) fails condition 2. A workspace where artifacts are absent but primes
structurally hold still fails condition 2 — evidence is mandatory, not optional.

---

## What This Changes

This amendment does not change ADR-S-036's core decision:
- Path freedom remains intact
- Invariants remain terminal conditions
- Assurance passes remain valid
- Derived evidence is still mandatory

What changes is ontological precision. The amendment explains why some required artifacts are
basis conditions while others are proof surfaces. This makes:

- **Implementation reviews** cleaner — reviewers can distinguish "foundational gap" from
  "evidence gap"
- **Tenant conformance work** cleaner — tenants know which checks are basis-level vs
  evidence-level
- **Future spec discussion** cleaner — "minimum invariants" debates resolve by pointing to
  the prime set

---

## Relationship to Other ADRs

- **ADR-S-036** — amended by this document; decision preserved unchanged
- **Bootloader §XI** — path-independence invariant: this amendment extends the same
  path-independence to the prime layer (primes hold regardless of path)
- **ADR-S-013** (Completeness Visibility) — observability and state legibility primes ground
  the completeness visibility requirement formally

---

*Ratified: 2026-03-12*
*Proposed by Codex; accepted by human principal*
*Applies to: all Genesis implementations*
