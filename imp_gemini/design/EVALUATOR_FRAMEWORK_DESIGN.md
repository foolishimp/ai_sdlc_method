# Design: Evaluator Framework (Multi-Stakeholder CONSENSUS)

**Version**: 1.1.0
**Date**: 2026-03-08
**Implements**: REQ-F-EVAL-001, ADR-S-025

--- 

## Architecture Overview
The framework uses a Composite Functor pattern to support multi-stakeholder evaluation (CONSENSUS). It dynamicallly composes $N$ independent $F_H$ (human) inputs into a single convergence signal based on a quorum rule.

## Component Design

### Component: FunctorRegistry (Refactored)
**Implements**: REQ-EVAL-001, REQ-EVAL-002
**Responsibilities**: Maps evaluator types (F_D, F_P, F_H) and higher-order functors (CONSENSUS, PLAN) to their respective implementations.
**Interfaces**: get_functors_for_composition(composition_name)

### Component: ConsensusFunctor (New)
**Implements**: ADR-S-025
**Responsibilities**: Manages a participant roster, quorum rules, and comment disposition lifecycle. Aggregates multiple $F_H$ inputs into a single convergence signal.
**Interfaces**: evaluate(candidate, roster, quorum_rule) 	o {reached|failed}

### Component: ParticipationTracker
**Implements**: ADR-S-025
**Responsibilities**: Tracks asynchronous votes, abstentions, and participation thresholds across the review window.

## Quorum Implementation
- **Formula**: `approve_ratio = approve_votes / (approve_votes + reject_votes)` (neutral abstention model).
- **Thresholds**: majority (>0.5), supermajority (>=0.66), unanimity (1.0).
- **Participation Threshold**: Mandates at least 50% roster turnout.

## Traceability Matrix
| REQ Key | Component |
|---------|----------|
| REQ-EVAL-001 | FunctorRegistry, HumanFunctor, GeminiFunctor, ConsensusFunctor |
| ADR-S-025 | ConsensusFunctor, ParticipationTracker |

## ADR Index
- [ADR-018: CONSENSUS — Multi-Stakeholder Evaluator Implementation](adrs/ADR-018-consensus-functor-implementation.md)
