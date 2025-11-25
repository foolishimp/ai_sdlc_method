# AI SDLC Methodology Plugin - Multi-Stage Agent Configuration

**Version**: 2.0.0
**Author**: foolishimp
**Reference Guide**: [AI SDLC Methodology](../../docs/ai_sdlc_method.md)

## Overview

This plugin provides a complete **7-stage AI SDLC methodology** with fully specified AI agent configurations for each stage. It extends the foundational Key Principles with end-to-end lifecycle management from intent to runtime feedback.

## The 7 Stages

### 1. Requirements Stage

**Agent**: AISDLC Requirements Agent
**Purpose**: Transform intent into structured requirements with unique, immutable keys.

### 2. Design Stage

**Agent**: AISDLC Design Agent / Solution Designer
**Purpose**: Transform requirements into an implementable technical and data solution.

### 3. Tasks / Work Breakdown Stage

**Agent**: AISDLC Tasks Stage Orchestrator
**Purpose**: Convert design into actionable work units and orchestrate agent work.

### 4. Code Stage - TDD-Driven

**Agent**: AISDLC Code Agent / Developer Agent
**Purpose**: Implement the solution using Test-Driven Development (TDD).

### 5. System Test Stage - BDD-Driven

**Agent**: AISDLC System Test Agent / QA Agent
**Purpose**: Verify integrated system behavior using Behavior-Driven Development (BDD).

### 6. UAT Stage - BDD for Business

**Agent**: AISDLC UAT Agent
**Purpose**: Facilitate business validation using business-readable BDD scenarios.

### 7. Runtime Feedback Stage

**Agent**: AISDLC Runtime Feedback Agent
**Purpose**: Close the feedback loop between the production environment and the requirements stage.

---

## Key Principles

### Requirement Key Traceability

Every artifact at every stage of the SDLC is tagged with unique requirement keys, enabling full end-to-end traceability.

### Feedback Loops

The methodology incorporates both forward (intent-to-runtime) and backward (runtime-to-intent) traceability, allowing for a continuous feedback loop that ensures the single source of truth for requirements is always up-to-date.

### Concurrent Execution

The methodology supports the concurrent execution of multiple sub-vector SDLCs. For example, the architecture, data pipeline, and application development can all happen in parallel once the common requirements are established.

---

## Configuration Files

-   **`config/stages_config.yml`**: Contains the complete 7-stage agent configurations.
-   **`config/config.yml`**: Defines the foundational Key Principles and the TDD workflow for the Code Stage.

## Usage

### Loading the Plugin

To use this methodology, reference the configuration files in your project's `gemini-code` setup.

### Example: AISDLC Requirements Agent Configuration

```yaml
requirements_agent:
  inputs:
    - intent_from: "Intent Manager"
    - feedback_from: ["design", "tasks", "code", "test", "uat", "runtime"]
  outputs:
    - user_stories: "REQ-F-*"
    - nfrs: "REQ-NFR-*"
    - data_requirements: "REQ-DATA-*"
  quality_gates:
    - unique_keys: true
    - acceptance_criteria: required
    - product_owner_review: required
```