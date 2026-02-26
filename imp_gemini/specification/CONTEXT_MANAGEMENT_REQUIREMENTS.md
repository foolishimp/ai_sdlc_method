# Requirements: REQ-F-CTX-001 — Context Management

**Version**: 1.0.0
**Date**: 2026-02-27
**Feature**: REQ-F-CTX-001
**Intent**: INT-AISDLC-001

---

## Overview
Context management ensures that construction is bounded by a persistent constraint surface. It handles the storage, composition, and reproducibility of the specification.

## Functional Requirements

### REQ-CTX-001: Context Store
**Priority**: Critical
**Description**: The system must maintain a persistent store for ADRs, data models, templates, and policy.
**Acceptance Criteria**:
- Files stored in `.ai-workspace/{design_tenant}/`.
- Context is version-controlled via git.

### REQ-CTX-002: Context Hierarchy
**Priority**: High
**Description**: Support hierarchical composition: global \u2192 org \u2192 team \u2192 project.
**Acceptance Criteria**:
- Later contexts override earlier ones.
- Merged context available to the `iterate()` engine.

### REQ-INTENT-004: Spec Reproducibility
**Priority**: High
**Description**: The spec must be canonically serialisable and hashable.
**Acceptance Criteria**:
- Deterministic hash of intent + context.
- Recorded at each iteration for audit.

## Traceability
All artifacts must carry REQ keys tracing back to this specification.
