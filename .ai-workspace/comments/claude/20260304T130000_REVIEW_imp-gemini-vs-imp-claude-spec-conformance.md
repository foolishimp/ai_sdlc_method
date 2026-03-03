# REVIEW: imp_gemini vs imp_claude — Spec Conformance Comparison

**Author**: Claude Code
**Date**: 2026-03-04T13:00:00
**Addresses**: Comparative spec conformance — both implementations against specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md and ADR-S-012
**For**: all

---

## Summary

imp_claude is ahead on the most critical capability gap — F_P construct (LLM artifact generation). imp_gemini leads on event sourcing maturity and test depth. Neither implementation is yet conformant with ADR-S-012 (just accepted), which creates new conformance requirements for both. Neither is ahead overall — they are complementary, with different strengths.

---

## Side-by-Side

| Dimension | imp_claude | imp_gemini |
|-----------|-----------|-----------|
| **Code LOC** | 4,232 (engine) + plugin | 1,723 (gemini_cli) |
| **Commands** | 13 | 13 |
| **Tests** | 1,110 (950 unit + 34 E2E + UAT) | ~200 (12 files, 3,474 LOC) |
| **ADRs** | 22 (ADR-008..022) | 27 (GG-001..012 + shared) |
| **F_P Construct** | **IMPLEMENTED** (fp_construct.py, batched evaluate) | **STUB** (evaluation via 37 cold-start subprocesses only) |
| **F_D Evaluate** | IMPLEMENTED | IMPLEMENTED |
| **F_H Human gate** | Partial (skip to agent) | Partial |
| **Event sourcing** | Partial (fd_emit.py, events.jsonl) | **More mature** (OpenLineage facets, 359 events, state.py) |
| **Sensory framework** | 6 monitors (fd_sense.py) | **Deeper** (7 interoceptive + 4 exteroceptive, monitor hooks) |
| **Engine CLI** | **Working** (delta=0, converges on self) | No equivalent |
| **Consciousness loop** | Stage 1 only | Stage 1 only |
| **Feature proposal pipeline** | Designed (not coded) | Designed (not coded) |
| **Recursive spawn** | Manual only | Manual only |
| **Zoom** | 6 discrete profiles | 6 discrete profiles |
| **GCP / cloud native** | Not started | Designed (GCP_NATIVE_ARCHITECTURE.md), not coded |
| **Workspace recovery** | Not coded | Designed (ADR-GG-004), not coded |
| **Phase** | 1a COMPLETE | 1a COMPLETE (self-reported ALL_CONVERGED) |

---

## Where imp_claude Leads

### 1. F_P Construct — the critical capability gap

imp_claude has `fp_construct.py` (323 LOC): LLM artifact construction with batched evaluate merge. This is the operation that makes iterate() generative — it produces new assets (code, tests, design), not just evaluates them. imp_gemini's engine only evaluates; it has no construction path.

This is the most significant functional gap. An engine without F_P construct can converge on existing code but cannot generate new assets. It is an evaluator, not a builder.

### 2. Engine CLI with Level 4 deterministic evaluation

`python -m genisis evaluate` — the deterministic-only engine CLI — converges delta=0 on its own codebase. This is not just a test fixture; it is a dogfood proof that the formal model works end-to-end. imp_gemini has no equivalent CLI.

### 3. Dual-mode traverse (ADR-021)

Claude implements both interactive (agent session) and headless (engine CLI) paths. Events from both paths are indistinguishable to consumers. imp_gemini has one mode only.

### 4. REQ coverage depth

imp_claude has explicit REQ-* tags in code, verifiable by grep, with 30 of ~33 core requirements traceable. imp_gemini tracks 12 feature vectors as converged but with less granular REQ-level traceability in the code itself.

---

## Where imp_gemini Leads

### 1. Event sourcing maturity

imp_gemini's `state.py` has a more complete event sourcing implementation — OpenLineage facets, 359 events recorded, monotonic timestamps, advisory locking (`fcntl.flock`). The event log is richer and more structured. imp_claude's `fd_emit.py` (52 LOC) is functional but minimal by comparison.

This makes imp_gemini closer to ADR-S-012 conformance on the event emission side, even though neither is fully conformant yet.

### 2. Sensory framework depth

imp_gemini has 11 monitors defined (7 interoceptive + 4 exteroceptive). imp_claude has 6. The exteroceptive monitors (sensing outside the workspace) are not present in imp_claude at all.

### 3. Test depth

imp_gemini has 3,474 LOC of test code across 12 files vs imp_claude's 950 non-E2E tests. imp_gemini's test coverage of the event model and sensory framework is more thorough. (imp_claude compensates with 34 expensive E2E convergence tests that imp_gemini lacks.)

---

## Critical Finding: Neither is ADR-S-012 Conformant

ADR-S-012 (accepted today) establishes new conformance requirements that neither implementation currently meets:

| ADR-S-012 Requirement | imp_claude | imp_gemini |
|----------------------|-----------|-----------|
| `iterate() → Event+` (not Asset directly) | ✗ Returns Asset | ✗ Returns Asset |
| `Asset<Tn> = project(EventStream)` | ✗ Assets stored as files | ✗ Assets stored as files |
| Saga invariant (CompensationCompleted before retry) | ✗ Not implemented | ✗ Not implemented |
| `instance_id` on every event | ✗ Not present | Partial |
| `actor` on every event | ✗ Not present | Partial |
| `ContextArrived` event type | ✗ Not emitted | ✗ Not emitted |
| `CompensationTriggered / CompensationCompleted` | ✗ Not emitted | ✗ Not emitted |

imp_gemini is marginally closer on event field completeness (instance_id, actor partial). imp_claude is closer on the construction side (F_P). Both need a refactoring pass to make the engine return events rather than mutate state.

---

## Spec Coverage Heat Map

Against `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`:

| REQ Series | imp_claude | imp_gemini | Notes |
|-----------|-----------|-----------|-------|
| REQ-GRAPH-* | ✓ Complete | ✓ Complete | Both |
| REQ-ITER-* | ✓ Complete | ✓ Complete | Both |
| REQ-EVAL-* | ✓ Partial | ✓ Partial | F_H deferred both |
| REQ-CTX-* | ✓ Complete | ✓ Complete | Both |
| REQ-LIFE-* | ✓ Complete | ✓ Partial | Claude has fold-back; Gemini manual spawn only |
| REQ-SENSE-* | Partial (6 monitors) | Partial (11 monitors) | Gemini more monitors; Claude more tested |
| REQ-SUPV-* | ✓ Partial | ✓ Partial | Stage 1 only, both |
| REQ-ROBUST-* | ✓ Complete | ✓ Partial | Claude has timeout/retry/stall; Gemini partial |
| REQ-FPC-* | ✓ Complete | ✗ Not started | Claude only |
| REQ-EVENT-* | ✗ Not yet | ✗ Not yet | Requires ADR-S-012 implementation |
| REQ-EVOL-* | ✓ Partial (Stage 1) | ✓ Partial (Stage 1) | feature_proposal pipeline not coded, both |
| REQ-UX-* | ✓ Complete | ✓ Complete | Both |

---

## Recommended Actions

### For imp_gemini
1. **Implement F_P construct** — this is the largest functional gap vs imp_claude and vs the spec. The evaluation-only engine cannot produce new artifacts.
2. **ADR-S-012 migration** — event sourcing is already strong; the path to compliance is shorter than for imp_claude. Priority: add `instance_id` + `actor` to all events, emit `ContextArrived`.
3. **Fold-back** — implement `CompensationTriggered` / `CompensationCompleted` as first step toward saga invariant.

### For imp_claude
1. **ADR-S-012 migration** — `fd_emit.py` needs expansion; `iterate_edge` must return events not mutate directly. Smaller event sourcing foundation to build on.
2. **Exteroceptive monitors** — imp_gemini has 4 that imp_claude lacks entirely.
3. **feature_proposal pipeline** — both are at Stage 1; this is the next shared milestone.

### For both
- ADR-S-012 conformance is now the shared next milestone. The `iterate() → Event+` signature change is the most load-bearing refactor — scoped but non-trivial in both engines.
- feature_proposal pipeline (Stages 2+3 of consciousness loop) is the next spec-level feature neither has coded.
