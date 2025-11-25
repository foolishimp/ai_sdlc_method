# ADR-006: Gemini Native Toolchain for AISDLC Implementation

**Status**: Proposed
**Date**: 2025-11-25
**Deciders**: Development Tools Team
**Requirements**: REQ-F-PLUGIN-001, REQ-F-CMD-001, REQ-NFR-TRACE-001
**Depends On**: ADR-001 (Decision to use a native platform)

---

## Context

The AI SDLC methodology requires a platform for delivering its 7-stage framework. For the Gemini implementation, we must select a technology stack that is native to the Google and Gemini ecosystem, moving beyond the simple file-based approach of the Claude MVP. The goal is to leverage a more powerful, integrated, and scalable toolchain that is purpose-built for orchestrating AI-driven development workflows.

### The Problem

A direct 1:1 copy of the Claude file-based system (`.gemini/commands/*.md`, `.gemini/agents/*.md`) for the Gemini implementation would fail to leverage the potential of Google's broader developer ecosystem. It would be a less powerful, less integrated, and less scalable solution than what is possible. We need a design that maps the AI SDLC's concepts (Agents, Skills, Stages) to a plausible, powerful Gemini-native toolchain.

---

## Decision

**We will implement the Gemini AI SDLC using a suite of hypothetical, but plausible, Gemini-native developer tools:**

1.  **Gemini Blueprints**: A service for creating, versioning, and sharing reusable, structured prompts. This will be the implementation for our **Skills**. Instead of simple markdown files, Blueprints are registered in a central repository (e.g., Google Cloud's Artifact Registry) and are strongly typed.
2.  **Gemini Workflows**: A CI/CD-style orchestration service for AI agents. This will be the implementation for the **7 SDLC Stages**. A workflow will be defined in YAML, chaining together various "Blueprints" (Skills) and assigning them to specific Gemini models (Agents).
3.  **Gemini Guardrails**: A policy-as-code service for defining and enforcing quality and security constraints on AI-generated outputs. This will be the implementation for our **Quality Gates** and **Key Principles**.
4.  **Gemini Code Assist**: The core IDE extension that provides the user interface and invokes "Gemini Workflows". Slash commands (`/aisdlc-*`) will be shortcuts to trigger these workflows.

This toolchain moves the implementation from "prompts-as-documentation" (the Claude approach) to "prompts-as-code".

---

## Rationale

### Why This Toolchain?

**1. Native Ecosystem Integration** ✅
This approach deeply integrates the AI SDLC into the Google developer ecosystem, leveraging existing services like Artifact Registry for versioning and IAM for permissions. This is a more robust and enterprise-ready solution than loose files in a git repository.

**2. Scalability and Reliability** ✅
- **Gemini Workflows** are designed for orchestration. They can run in parallel, have explicit dependency management, and provide robust logging and error handling, overcoming the limitations of a single-file task list.
- **Gemini Blueprints** are versioned, typed, and testable artifacts, making them far more reliable than plain markdown prompts.

**3. From Documentation to Infrastructure-as-Code** ✅
The AI SDLC methodology becomes a set of version-controlled, deployable assets, not just documentation for an AI to read.
```yaml
# claude-code (Prompts-as-Documentation)
- Agents are long markdown files.
- Skills are instructional documentation.
- The AI reads and interprets.

# gemini-code (Prompts-as-Code)
- Agents are roles within a Gemini Workflow.
- Skills are versioned Gemini Blueprints (structured prompts).
- The Workflow engine executes the Blueprints.
```

**4. Explicit Quality Enforcement** ✅
- **Gemini Guardrails** provide programmatic enforcement of the "Key Principles". Instead of an agent *reading* about the TDD principle, a Guardrail policy can programmatically fail a workflow step if the generated code does not include a corresponding test file. This is a major leap in reliability.

**5. Clear Separation of Concerns**
This model maps perfectly to the conceptual architecture:
- **Agents (WHO)** → `roles` defined in a `Gemini Workflow` YAML.
- **Skills (HOW)** → `Gemini Blueprints` called by the workflow.
- **Commands (WHAT)** → Shortcuts in `Gemini Code Assist` that trigger a `Gemini Workflow`.
- **Stages (WHERE)** → `stages` within the `Gemini Workflow` YAML definition.

---

## Consequences

### Positive

- **Robustness & Reliability**: Typed, versioned prompts and programmatic workflows are less ambiguous and more reliable than interpreting markdown files.
- **Scalability**: This architecture can easily scale to large teams and complex projects.
- **True Automation**: Quality gates are programmatically enforced, not just suggested to an AI.
- **CI/CD Integration**: Gemini Workflows can be triggered by standard CI/CD events (e.g., a `git push` could trigger the "System Test" workflow).

### Negative

- **Increased Complexity**: The initial setup is more complex than creating markdown files. It requires defining YAML workflows and managing artifacts in a registry.
- **Vendor Lock-in**: This design deeply embeds the solution within the Google Cloud and Gemini ecosystem. Porting it to another platform (like OpenAI) would require a complete re-architecture.
- **Hypothetical Tooling**: This design relies on a plausible but currently hypothetical set of Gemini tools. The actual implementation would depend on the real-world tools Google provides.

---

## Mapping to Requirements

| Requirement | Satisfied? | How |
|---|---|---|
| REQ-F-PLUGIN-001 | ✅ | "Gemini Blueprints" serve as versioned, shareable plugins for skills. |
| REQ-F-CMD-001 | ✅ | Slash commands in the IDE trigger "Gemini Workflows". |
| REQ-NFR-TRACE-001 | ✅ | Each step in a "Gemini Workflow" is logged and can be tagged with the initiating REQ-* key, providing end-to-end traceability. |
| REQ-NFR-FEDERATE-001| ✅ | Blueprints stored in Artifact Registry can be shared across the organization, enabling a federated model. |

---

**Decision**: This ADR proposes a forward-looking, robust architecture for the Gemini implementation. We accept the trade-off of increased initial complexity for a significant gain in reliability, scalability, and true automation. This design will be the guiding vision for the `gemini-aisdlc` implementation.
