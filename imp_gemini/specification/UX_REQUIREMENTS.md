# Requirements: REQ-F-UX-001 — User Experience

**Version**: 1.0.0
**Date**: 2026-02-27
**Feature**: REQ-F-UX-001
**Intent**: INT-AISDLC-001

Implements: REQ-F-UX-001

---

## Overview
The UX layer provides a simplified, state-driven interface to the methodology. It abstracts away command complexity and provides high-level observability.

## Functional Requirements

### REQ-UX-001: State-Driven Routing
**Priority**: Critical
**Description**: Detect project state from the filesystem and route to the correct command.
**Acceptance Criteria**:
- Support 8 core project states.
- Derive state from event log and folder structure.

### REQ-UX-003: Project-Wide Observability
**Priority**: High
**Description**: Provide a unified status view across all active features.

### REQ-UX-004: Automatic Feature/Edge Selection
**Priority**: High
**Description**: Select the highest priority actionable feature and edge automatically.

## Traceability
All artifacts must carry REQ keys tracing back to this specification.
