# Requirements: REQ-F-EVAL-001 — Evaluator Framework

**Version**: 1.0.0
**Date**: 2026-02-27
**Feature**: REQ-F-EVAL-001
**Intent**: INT-AISDLC-001

---

## Overview
The evaluator framework provides the convergence criteria for all graph edge traversals. It combines deterministic, probabilistic, and human judgment into a unified `stable()` check.

## Functional Requirements

### REQ-EVAL-001: Three Evaluator Types
**Priority**: Critical
**Description**: Support {Human, Agent, Deterministic} evaluator types.
**Acceptance Criteria**:
- **Deterministic**: Shell commands/tests (pass/fail).
- **Agent**: LLM-based gap analysis and constructive feedback.
- **Human**: Interactive approval/rejection gates.

### REQ-EVAL-002: Evaluator Composition Per Edge
**Priority**: High
**Description**: Each graph edge defines its required set of evaluators.
**Acceptance Criteria**:
- Composition is configurable in `graph_topology.yml`.
- `iterate()` engine loads and executes the correct functors for the edge.

### REQ-EVAL-003: Human Accountability
**Priority**: Critical
**Description**: AI assists, human decides.
**Acceptance Criteria**:
- Human review is required for all spec/design changes.
- AI evaluations are presented as advice, not final decisions.

## Traceability
All artifacts must carry REQ keys tracing back to this specification.
