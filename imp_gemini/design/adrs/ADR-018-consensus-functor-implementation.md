# ADR-018: CONSENSUS — Multi-Stakeholder Evaluator Implementation in imp_gemini

**Series**: Implementation (imp_gemini)
**Status**: Proposed
**Date**: 2026-03-08
**Refers to**: ADR-S-025

--- 

## Context

As specified in ADR-S-025, the existing $F_H$ evaluator model is singular. This ADR implements the multi-stakeholder CONSENSUS functor within the Gemini CLI architecture.

## Decision

### CONSENSUS as a Composite Observer/Evaluator

In `imp_gemini`, the CONSENSUS functor is implemented as a specialized `IntentEngine` instantiation that manages a participant roster and quorum rules.

1.  **Roster Management**: The roster is stored as a `Context[]` element in the edge configuration (`edge_params/`). Roles are defined as `reviewer` and `veto_holder`.
2.  **Quorum Logic**: Gemini's internal `EvaluatorFramework` will be extended to support $N$ independent $F_H$ inputs. The convergence rule (`stable(candidate, edge_type)`) is updated to satisfy the quorum formula defined in ADR-S-025.
3.  **Abstention & Participation**: Per Gemini's review of ADR-S-025, the default model is `neutral` with a mandatory `participation_threshold` of 50%.

## Operational Implementation

- **Comment Corpus**: Collected through the Sensory Service (`imp_gemini/code/src/gemini_cli/sensory.py`). Each comment is assigned a UUID and requires a disposition artifact before convergence.
- **Veto Protection**: Implementation of the `veto_holder` role as a hard-block in the `EvaluatorFramework` logic. If a veto is cast, the state transitions directly to `consensus_failed`.
- **Gemini CLI UX**: The `gemini -c` (comment/consensus) command will be added to provide a structured CLI interface for reviewers to cast votes and provide rationales.

## Consequences

- **Positive**: High-stakes governance edges (ADR acceptance, spec modification) now have formal multi-party support in Gemini CLI.
- **Negative**: Adds state management complexity to the local `events.jsonl` to track asynchronous votes and dispositions.
