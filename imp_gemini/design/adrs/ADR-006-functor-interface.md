# ADR-006: Unified Functor Interface

**Status**: Accepted
**Date**: 2026-02-27

## Context
We need to execute different types of evaluations (tests, AI analysis, human approval) within the same iteration loop.

## Decision
Implement a `Protocol`-based interface (`Functor`) with a single `evaluate(candidate, context) \u2192 FunctorResult` method. All evaluators must return a standard `FunctorResult` containing a numerical `delta` and a string `reasoning`.

## Consequences
- `IterateEngine` can handle all evaluator types polymorphically.
- Standardised `delta` enables consistent convergence checks across all edges.
