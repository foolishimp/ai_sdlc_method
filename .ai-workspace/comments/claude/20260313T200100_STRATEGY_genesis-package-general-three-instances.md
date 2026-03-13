# STRATEGY: Genesis as package-general — three domain instances

**Author**: claude
**Date**: 2026-03-13T20:01:00+11:00
**Addresses**: Genesis as a general-purpose governed asset system builder — three concrete domain packages as evidence
**For**: all

## Summary

Three domain packages now exist as concrete proposals: AI SDLC, genesis_obligations, and enterprise architecture. All three use the same four primitives, the same event substrate, the same F_D/F_P/F_H evaluator model, and the same convergence loop. The domain graphs are different; the formal system is identical. This is the evidence base for the package-general direction.

## The Pattern Across All Three

| | AI SDLC | genesis_obligations | enterprise_architecture |
|---|---------|-------------------|------------------------|
| **Intent** | business/product intent | regulatory source document | business initiative |
| **Hard edge** | intent → requirements | source_provision → interpretation_case | business_initiative → architecture_requirements |
| **Hard edge output** | requirements spec | interpretation case | architecture requirements |
| **Parallel vectors** | feature vectors | obligation candidates per domain | solution candidates |
| **Spawns** | spike, discovery, POC | interpretation review, POC | POC vector, discovery vector |
| **Terminal F_H gate** | UAT + release | interpretation approval + assessment approval | architecture board CONSENSUS |
| **Feedback loop** | telemetry → intent | source change → re-interpretation | implementation drift → initiative |
| **Context[]** | project constraints, ADRs | institutional scope, regulatory domains, precedent | architecture principles, approved stacks, integration landscape |

The hard edge is always the same structure: human meaning or external signal → formal asset that downstream work evaluates against. Everything upstream of it is capturing and interpreting; everything downstream is computing against it.

## What varies

**Graph topology** — the nodes and edges are domain-specific. Software delivery, regulatory compliance, and solution architecture have different asset types and different transition structures.

**Evaluator weight distribution** — in SDLC, F_D is heavy downstream (tests, coverage, compilation). In obligations, F_H is heaviest at the interpretation edge. In architecture, F_H is heaviest at the evaluation and approval gates. The balance shifts; the three types remain the same.

**Context[] content** — different domains have different standing constraints. The mechanism — loading context into every edge traversal — is identical.

**Markov criteria** — what constitutes a stable asset is domain-specific. `dissenting_views_recorded` is a markov criterion for `solution_evaluation`. `ambiguity_notes_present` is a markov criterion for `interpretation_case`. `human_approved` appears in all three.

**Risk profile** — what it costs to be wrong at the hard edge varies enormously. A wrong architectural requirements approval causes expensive rework. A wrong interpretation approval creates regulatory exposure. A wrong requirements approval causes product failure. The methodology does not set the risk threshold — it forces the conditions of the F_H gate into the record so the institution can set it.

## What does not vary

- Append-only event stream as the substrate
- Assets as projections of the event stream
- iterate() as the only operation
- Three evaluator types
- Three processing phases (reflex, affect, conscious)
- The hard edge invariant — one primary epistemically uncertain edge per package
- Traceability — every downstream asset traces back to the hard edge output
- CONSENSUS for multi-party F_H gates
- Spawn/fold-back for time-boxed child work
- Provisional terminal state for unresolved ambiguity

## Implications for the specification

The current specification describes the four primitives as universal but illustrates them exclusively with the SDLC graph. This is not wrong — the SDLC graph is the reference implementation. But it creates an implicit conflation: readers treat the SDLC topology as the methodology rather than as one instance of it.

Three concrete domain packages make the distinction concrete and testable. The claim "Genesis is domain-general" is no longer asserted — it is demonstrated.

The required spec change is narrow: state explicitly that the SDLC graph is one package, identify the four primitives as the package-general substrate, and note that domain packages are authored against the primitive substrate with their own graph topology and constraint dimensions.

GTL formalises this authoring surface. But the packages can be written in static YAML today without waiting for GTL. The three config files above are proof.

## The next package

These three cover: building software systems, managing regulatory obligations, designing solution architectures.

The question for the next package is not "what else can Genesis do" — it is "where does a governed convergence loop with explicit human gates and full traceability produce disproportionate value over current practice?"

Candidates:
- **product roadmap governance** — initiatives, bets, validation, deprioritisation — explicit F_H gates over commitment decisions
- **risk and control framework** — control obligations, evidence, gap tracking — close cousin of obligations
- **procurement and vendor evaluation** — requirements, RFP, evaluation matrix, approval — close cousin of architecture

All the same pattern. All the same primitives.

*Reference: conversation 2026-03-13*
*Relates to: 20260313T200000_STRATEGY_genesis-enterprise-architecture-package.md, genesis_obligations spec, ADR-S-035 GTL*
