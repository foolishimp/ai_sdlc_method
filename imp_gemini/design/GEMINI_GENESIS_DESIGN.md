# Design: Spec Evolution Pipeline (REQ-F-EVOL-001)

This document defines the architectural implementation of the event-sourced spec evolution pipeline for the Gemini tenant.

<!-- Implements: REQ-EVOL-001, REQ-EVOL-002, REQ-EVOL-003, REQ-EVOL-004, REQ-EVOL-005 -->

## 1. Overview
The pipeline enables the promotion of homeostasis signals into the formal specification via a structured proposal and review process.

## 2. Components

### 2.1 Feature Proposal Engine
- **Source**: Affect Triage signals (`signal_source: gap | ecosystem`).
- **Action**: Emits `feature_proposal` events (REQ-EVOL-003).
- **Persistence**: Event log only (no filesystem mutation during proposal).

### 2.2 Review Boundary
- **Tool**: `gemini review` (REQ-SENSE-005).
- **Gate**: Human approval ($F_H$) required for all promotions.

### 2.3 Promotion Logic
- **Action**: Appends to `specification/features/FEATURE_VECTORS.md`.
- **Event**: Emits `spec_modified` with causal link to proposal (REQ-EVOL-004).

## 3. Data Model
- Proposals are stored as `OTHER` events with `sdlc_event_type.type: feature_proposal`.
- Joins are performed in-memory by the `Projector` class (REQ-EVOL-002).
