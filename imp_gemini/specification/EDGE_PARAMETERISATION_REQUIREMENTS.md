# Requirements: REQ-F-EDGE-001 — Edge Parameterisations

**Version**: 1.0.0
**Date**: 2026-02-27
**Feature**: REQ-F-EDGE-001
**Intent**: INT-AISDLC-001

---

## Overview
Edge parameterisations define the specific evaluator configurations and construction patterns for different transitions in the asset graph. They ensure that domain-specific workflows (like TDD or BDD) are consistently applied.

## Functional Requirements

### REQ-EDGE-001: TDD Workflow
**Priority**: High
**Description**: Support TDD co-evolution (RED/GREEN/REFACTOR) at Code \u2194 Tests edges.
**Acceptance Criteria**:
- Edge is bidirectional (co-evolution).
- Evaluators check both code and tests for convergence.

### REQ-EDGE-002: BDD Scenarios
**Priority**: High
**Description**: Support BDD Given/When/Then at Design \u2192 Test edges.
**Acceptance Criteria**:
- Use Gherkin or equivalent structured scenarios.
- Traceable to REQ keys.

### REQ-EDGE-003: ADR Generation
**Priority**: High
**Description**: Automate Architecture Decision Record generation at Requirements \u2192 Design edges.

### REQ-EDGE-004: Code Tagging Discipline
**Priority**: Critical
**Description**: Enforce `Implements: REQ-*` and `Validates: REQ-*` tagging in artifacts.

## Traceability
All artifacts must carry REQ keys tracing back to this specification.
