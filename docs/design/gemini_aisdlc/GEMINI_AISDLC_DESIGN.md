# AI SDLC Methodology - Gemini Implementation Design

This document outlines the design for the Gemini implementation of the AI SDLC Methodology, based on the foundational decisions in ADR-006.

## 1. Overview

The Gemini implementation of the AI SDLC will be built on a suite of native Google Cloud and Gemini tools. This approach moves beyond the file-based MVP architecture of the Claude implementation to a more robust, scalable, and automated "Infrastructure-as-Code" model for AI-driven development.

The core decision, as detailed in **[ADR-006: Gemini Native Toolchain for AISDLC Implementation](./adrs/ADR-006-gemini-toolchain-for-aisdlc-implementation.md)**, is to map the conceptual components of the AI SDLC (Stages, Agents, Skills, Quality Gates) to specific, structured cloud services.

## 2. Core Architecture: The Gemini Toolchain

The implementation will be centered around four key services:

1.  **Gemini Blueprints (for Skills)**: All 41+ reusable skills (e.g., `requirement-extraction`, `tdd-workflow`) will be implemented as versioned, structured prompt templates called "Blueprints." These will be stored and managed in Google Cloud's **Artifact Registry**, allowing for strong versioning, typed inputs/outputs, and organization-wide sharing.

2.  **Gemini Workflows (for Stages & Agents)**: The 7-stage SDLC pipeline will be defined as a YAML-based "Gemini Workflow." This workflow will orchestrate the execution of "Blueprints" in the correct sequence. Agents (e.g., `Requirements Agent`, `Code Agent`) will be defined as roles or properties within the workflow steps, specifying which Gemini model or configuration to use for a given task.

3.  **Gemini Guardrails (for Quality Gates & Principles)**: The methodology's quality gates and "Key Principles" will be implemented as programmatic policies in "Gemini Guardrails." For example, a Guardrail policy can be written to automatically fail a "Code" stage workflow run if the generated code has a test coverage below 80%, providing true, automated enforcement rather than simple suggestion.

4.  **Gemini Code Assist (for User Interaction)**: The developer's primary interface will be the "Gemini Code Assist" IDE extension. Slash commands like `/aisdlc-commit-task` will act as user-friendly triggers for invoking the corresponding backend "Gemini Workflows."

## 3. Workflow Example: TDD Cycle

The TDD cycle (RED-GREEN-REFACTOR) in the "Code" stage would be executed as follows:

1.  A developer, acting as the "Code Agent," runs `/aisdlc-tdd-cycle --requirement REQ-F-AUTH-001`.
2.  **Gemini Code Assist** triggers the `tdd-workflow` **Gemini Workflow**.
3.  The workflow executes the first step, which calls the `red-phase` **Gemini Blueprint**. The output (a failing test file) is generated.
4.  A **Gemini Guardrail** policy verifies that the tests are indeed failing before allowing the workflow to proceed.
5.  The workflow proceeds to the `green-phase` and `refactor-phase` Blueprints, with Guardrails continuously checking for test pass rates and code quality.
6.  The final step calls the `commit-with-req-tag` Blueprint to generate the final commit message.

## 4. Future Work

The implementation plan is now defined by the rollout of this new architecture:

1.  **Phase 1: Blueprint Definition**: Convert all existing markdown-based skills into structured "Gemini Blueprint" templates.
2.  **Phase 2: Workflow Implementation**: Build the main 7-stage "Gemini Workflow" in YAML, referencing the newly created Blueprints.
3.  **Phase 3: Guardrail Policies**: Implement the core "Key Principles" and quality gates as programmatic policies in "Gemini Guardrails."
4.  **Phase 4: IDE Integration**: Connect the slash commands in the "Gemini Code Assist" extension to trigger the backend workflows.
