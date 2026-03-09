# Design Document Index — Claude Code Implementation

Design documents are the primary artifacts of the `requirements→design` edge.
Each document covers one subsystem or feature. ADRs capture individual decisions
made *during* design; this index tracks the design docs themselves.

| Document | Subsystem | Feature | Status |
|----------|-----------|---------|--------|
| [AISDLC_V2_DESIGN.md](AISDLC_V2_DESIGN.md) | Top-level system architecture | All features | Accepted |
| [FUNCTOR_FRAMEWORK_DESIGN.md](FUNCTOR_FRAMEWORK_DESIGN.md) | Functor encoding (F_D/F_P/F_H) | REQ-F-FUNCTOR-001 | Accepted |
| [ENGINE_DESIGN_GAP.md](ENGINE_DESIGN_GAP.md) | Engine gap analysis | REQ-F-ENGINE-001 | Analysis |
| [FRAMEWORK_COMPARISON_ANALYSIS.md](FRAMEWORK_COMPARISON_ANALYSIS.md) | Cross-platform comparison | — | Analysis |
| [DESIGN_REQUIREMENTS.md](DESIGN_REQUIREMENTS.md) | Design-level requirements | — | Reference |
| [CONSENSUS_DESIGN.md](CONSENSUS_DESIGN.md) | CONSENSUS functor | REQ-F-CONSENSUS-001 | Proposed |

## Status values

| Status | Meaning |
|--------|---------|
| Proposed | Drafted, awaiting F_H review |
| Accepted | Human-approved, driving code |
| Superseded | Replaced by a later document |
| Analysis | Not a design artifact — reference/comparison only |
| Reference | Stable reference, not a design output |
