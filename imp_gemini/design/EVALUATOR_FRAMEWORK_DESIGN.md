# Design: Evaluator Framework

**Version**: 1.0.0
**Date**: 2026-02-27
**Implements**: REQ-F-EVAL-001

---

## Architecture Overview
The framework uses a Plugin/Functor pattern where each evaluator type implements a common `evaluate()` interface. The engine dynamically composes these functors based on the edge topology.

## Component Design

### Component: FunctorRegistry
**Implements**: REQ-EVAL-001, REQ-EVAL-002
**Responsibilities**: Maps evaluator types (human, agent, deterministic) to their respective functor implementations.
**Interfaces**: get_functors_for_edge(edge_name)

### Component: HumanFunctor
**Implements**: REQ-EVAL-003
**Responsibilities**: Provides the interactive prompt for human judgment.

### Component: GeminiFunctor
**Implements**: REQ-EVAL-001
**Responsibilities**: Interfaces with the Gemini CLI for probabilistic evaluation and gap analysis.

## Traceability Matrix
| REQ Key | Component |
|---------|----------|
| REQ-EVAL-001 | FunctorRegistry, HumanFunctor, GeminiFunctor, DeterministicFunctor |
| REQ-EVAL-002 | FunctorRegistry |
| REQ-EVAL-003 | HumanFunctor |

## ADR Index
- [ADR-006: Unified Functor Interface](adrs/ADR-006-functor-interface.md)
