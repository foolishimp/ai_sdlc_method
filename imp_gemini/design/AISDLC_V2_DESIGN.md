# AI SDLC — Gemini Implementation Design (v2.8)

This document describes the Gemini implementation of the AI SDLC Asset Graph Model.

## 1. Architecture Overview

### 1.1 The Three Layers
The implementation follows the three-layer conceptual model:
- **Layer 1: ENGINE (universal)**: Implements the 4 primitives and the universal `iterate()` function.
- **Layer 2: GRAPH PACKAGE (domain-specific)**: Defines the graph topology, edge configurations, and projection profiles.
- **Layer 3: PROJECT BINDING (instance-specific)**: Projects-specific constraints and context.

## 2. Formal System

### 2.1 Primitives and Operations
The methodology is defined by four invariants:
- **Graph**: Topology of typed assets.
- **Iterate**: The universal operation.
- **Evaluators**: Convergence criteria.
- **Spec + Context**: The constraint surface.

### 2.2 Processing Phases
The IntentEngine implements three processing phases:
- **Reflex**: Autonomic event emission and protocol enforcement.
- **Affect**: Signal classification and triage.
- **Conscious**: Deliberative judgment and intent generation (conscious phase).
Evaluators declare their `processing_phase` (reflex, affect, or conscious).

## 3. Execution Model

### 3.1 Functors and Escalation
The system uses a functor-based execution model ($F_D \to F_P \to F_H$).
- **Deterministic ($F_D$)**: Zero ambiguity.
- **Probabilistic ($F_P$)**: Bounded ambiguity.
- **Human ($F_H$)**: Persistent ambiguity.

### 3.2 Event Sourcing
All state changes are recorded in `.ai-workspace/events/events.jsonl`.
Supported event types: `project_initialized`, `iteration_completed`, `edge_started`, `edge_converged`, `spawn_created`, `spawn_folded_back`, `checkpoint_created`, `review_completed`, `gaps_validated`, `release_created`, `intent_raised`, `spec_modified`, `encoding_escalated`, `interoceptive_signal`, `exteroceptive_signal`, `affect_triage`, `draft_proposal`, `claim_rejected`, `edge_released`, `claim_expired`, `convergence_escalated`, `evaluator_detail`, `command_error`, `health_checked`, `iteration_abandoned`.

## 4. Sensory Systems

### 1.8 Sensory Service
The sensory service implements REQ-F-SENSE-001.

#### 1.8.1 Service Architecture
The sensory service runs independently to watch the workspace and run monitors.

#### 1.8.2 Interoceptive Monitors
Concrete monitors observe the system's own health state (INTRO-001 through INTRO-007):
- **INTRO-001**: Event freshness
- **INTRO-002**: Feature vector stall
- **INTRO-003**: Test health
- **INTRO-004**: STATUS freshness
- **INTRO-005**: Build health
- **INTRO-006**: Spec/code drift
- **INTRO-007**: Event log integrity
Events: `interoceptive_signal`.

#### 1.8.3 Exteroceptive Monitors
Monitors observe the external environment (EXTRO-001 through EXTRO-004):
- **EXTRO-001**: Dependency freshness
- **EXTRO-002**: CVE scanning
- **EXTRO-003**: Runtime telemetry
- **EXTRO-004**: API contract changes
Events: `exteroceptive_signal`.

#### 1.8.4 Affect Triage Pipeline
Signals pass through a triage pipeline for classification and escalation.
Events: `affect_triage`.
Uses `affect_triage.yml` and `sensory_monitors.yml` schemas.

#### 1.8.5 Homeostatic Responses
Draft proposals are generated for escalated signals.
Events: `draft_proposal`.

#### 1.8.6 Review Boundary
Separates autonomous sensing from human-approved changes.

#### 1.8.7 Event Contracts
Defined for all sensory signals.

#### 1.8.8 Monitor Reference
Mapping of all monitors to their detection logic.

## 5. User Experience

### 1.9 Two-Command UX Layer
Implements ADR-012 for simplified interaction.
- **Start**: Automated routing through the state machine.
- **Status**: Aggregated observability and "You Are Here" indicators.

## 1.10 Multi-Agent Coordination
Implements REQ-F-COORD-001 using event-sourced claims.

## 1.11 Context Source Resolution
Implements resolution of `context_sources` from `project_constraints.yml`. External collections are resolved and copied into `.ai-workspace/context/` subdirectories such as `adrs/`, `data_models/`, `templates/`, `policy/`, and `standards/`.

## 7. Protocol Enforcement
Every `iterate()` invocation enforces mandatory side effects via Reflex Hooks.

## 8. Consciousness Loop
The design implements the **Consciousness Loop** (ADR-011) where the system observes its own deltas and feeds them back as intent.

## 9. Feature Vector Coverage
This design ensures 11 feature vectors covered, including REQ-F-SENSE-001 and REQ-F-COORD-001.
