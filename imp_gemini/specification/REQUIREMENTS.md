# Requirements: Gemini Genesis — Asset Graph Engine

**Version**: 1.0.0
**Date**: 2026-02-26
**Feature**: REQ-F-ENGINE-001
**Intent**: INT-AISDLC-001

---

## Overview
This document defines the core Asset Graph Engine requirements for the Gemini implementation. It codifies the graph topology, iteration function, and convergence mechanics.

## Asset Graph Requirements

### REQ-GRAPH-001: Asset Type Registry
**Priority**: Critical | **Type**: Functional
The system shall maintain a registry of asset types (Intent, Requirements, Design, Code, Tests, etc.) with typed interfaces and Markov criteria.

### REQ-GRAPH-002: Admissible Transitions
**Priority**: Critical | **Type**: Functional
The system shall define and enforce directed edges between asset types. Only admissible transitions can be traversed.

### REQ-GRAPH-003: Asset as Markov Object
**Priority**: High | **Type**: Functional
An asset achieves stable status only when it satisfies all evaluators for its type (Boundary, Independence, Stability).

## Iteration Engine Requirements

### REQ-ITER-001: Universal Iteration Function
**Priority**: Critical | **Type**: Functional
Implement single iteration function: `iterate(Asset, Context[], Evaluators) \u2192 Asset'`. Same logic for all edges, parameterised by evaluators.

### REQ-ITER-002: Convergence and Promotion
**Priority**: Critical | **Type**: Functional
Candidates are promoted to the next asset type only upon evaluator convergence (\u03b4 < \u03b5).

## Traceability
All artifacts must carry REQ keys tracing back to this specification.
