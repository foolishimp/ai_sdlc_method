# STRATEGY: Genesis as enterprise architecture package — graph topology proposal

**Author**: claude
**Date**: 2026-03-13T20:00:00+11:00
**Addresses**: Genesis graph package for enterprise solution architecture design and evaluation
**For**: all

## Summary

Enterprise architecture is a natural Genesis domain. The four primitives apply directly: a business initiative is the intent, architecture requirements are the hard edge output, solution candidates are parallel feature vectors, POC and discovery are time-boxed spawns, and the architecture board approval is a CONSENSUS gate. The result is a governed, traceable, auditable architecture process with explicit dissent recording and a clean handoff surface to delivery.

## The Hard Edge

`business_initiative → architecture_requirements`

Same invariant as every other domain. Before any design work begins, a human must approve what the architecture must satisfy — functional requirements, quality attributes, applicable principles, and constraints. Everything downstream evaluates deterministically against this surface.

Architecture principles, engineering standards, approved stacks, and the integration landscape are Context[] — standing constraints loaded into every edge traversal, not graph nodes.

## Asset Types

### Normalization layer (upstream of design)
- `business_initiative` — the business problem or strategic directive (INT-SEQ)
- `architecture_requirements` — tech-agnostic requirements with quality attributes and principle application (ARCH-REQ-SEQ) — **the hard edge output**

### Design layer
- `solution_candidate` — a proposed solution with stack, pattern, tradeoffs, risks, and open questions (SOL-SEQ-VARIANT)
- `poc_vector` — time-boxed proof-of-concept for a specific risk in a candidate (POC-SEQ)
- `discovery_vector` — time-boxed research to resolve an open question (DISC-SEQ)

### Evaluation and approval layer
- `solution_evaluation` — comparative matrix across candidates, incorporating POC and discovery fold-backs (EVAL-SEQ)
- `approved_architecture` — selected and approved solution with conditions and review triggers (ARCH-SEQ)
- `implementation_brief` — handoff artifact scoped for delivery teams (BRIEF-SEQ)

## Transition Structure

```
business_initiative
    → architecture_requirements          [F_P draft + F_H approve — HARD EDGE]
        → solution_candidate (×N)        [parallel tournament vectors]
            → poc_vector                 [spawn — time-boxed, fold-back]
            → discovery_vector           [spawn — time-boxed, fold-back]
        → solution_evaluation            [tournament arbitration — all candidates + fold-backs]
            → approved_architecture      [CONSENSUS gate — architecture board quorum]
                → implementation_brief   [handoff scoping]
```

Multiple `solution_candidate` vectors run in parallel. POC and discovery are spawned from candidates when open questions or unacceptable risks are identified. Their results fold back into the candidate before evaluation. The tournament collects all candidates and produces a ranked evaluation. The CONSENSUS gate selects.

## Constraint Dimensions (Context[])

- `architecture_principles` — governing architectural principles (mandatory)
- `engineering_principles` — engineering standards (mandatory)
- `approved_stacks` — available technologies (mandatory)
- `restricted_technologies` — prohibited or exception-required technologies (mandatory)
- `integration_landscape` — existing systems requiring integration (mandatory)
- `evaluation_quorum` — who must approve, minimum approvers, dissent handling (mandatory)

## Key Design Decisions

### Dissenting views as a markov criterion

`solution_evaluation` cannot converge without `dissenting_views` being explicitly recorded — even if the list is empty. Architecture reviews routinely lose minority positions in the meeting. Making dissent a convergence criterion forces it into the record.

### Open decisions as a handoff surface

`implementation_brief` lists decisions explicitly delegated to delivery teams. The gap between what was decided at architecture level and what delivery teams think was decided is a primary source of architectural drift. Explicit `open_decisions` closes that gap.

### POC and discovery as first-class spawns

POC and discovery are not informal parallel work summarised in a slide. They are time-boxed child vectors with fold-back — their outputs become part of the evaluation context with full traceability. A candidate's risk assessment is only as strong as the POC evidence behind it.

### Provisional approval

`approved_architecture` carries a `provisional` flag and explicit `conditions` list. Architecture approvals under unresolved constraints — tight timelines, missing landscape data, deferred security review — are common. The methodology forces those conditions into the record rather than treating provisional approval as unconditional.

## Profiles

| Profile | Use | Graph |
|---------|-----|-------|
| `full` | Strategic initiative, multiple candidates, full POC/discovery | All edges |
| `standard` | Significant project, single preferred candidate with POC | Candidate → POC optional |
| `spike` | Quick feasibility — is this worth pursuing? | Initiative → Requirements → one Candidate |
| `poc` | Known direction, specific risk to validate | Candidate → POC → Evaluation |

## What this is not

This is not a document repository for architecture artefacts. It is not a presentation template. It is a governed convergence loop that produces traceable, auditable architecture decisions with explicit dissent, explicit conditions, and a clean delivery handoff.

*Reference: conversation 2026-03-13, Genesis as general-purpose builder*
*Relates to: genesis_obligations package, GTL package-general direction*
