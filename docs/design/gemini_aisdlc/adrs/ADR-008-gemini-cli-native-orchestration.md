# ADR-008: Gemini CLI-Native Orchestration

**Date**: 2025-12-16
**Status**: Proposed

## Context

The AI-SDLC methodology requires a platform for execution. The initial `claude-code` implementation relies on a human developer, assisted by the Claude AI, to manually drive the 7-stage lifecycle by following prompts and conventions defined in markdown and YAML files.

The goal for the Gemini implementation is to increase automation and enforcement of the methodology. The primary, non-negotiable constraint is that this implementation **must** be built using the native capabilities of the Gemini CLI agent as the execution platform.

## Decision

We will implement the Gemini AI-SDLC by using the **Gemini CLI agent as the central, active orchestrator** of the existing file-based methodology.

Instead of a human driving the process, the Gemini agent will be responsible for reading the methodology files, executing the required steps, and using its built-in tools (`run_shell_command`, `read_file`, `write_file`, `replace`) to interact with the project repository.

The architecture will be as follows:

1.  **Workflow Engine**: The Gemini CLI agent itself will serve as the workflow engine. Its internal logic, guided by the user and the agent persona prompts, will manage the state transitions between the 7 SDLC stages.

2.  **Skills**: "Skills" will be implemented as **executable scripts** (e.g., `.py`, `.sh`) stored in the repository. The Gemini agent will invoke these skills using its `run_shell_command` tool. This makes skills testable, version-controlled, and more robust than pure prompt text.

3.  **Quality Gates**: "Guardrails" or quality gates will be implemented as **validation scripts**. At the end of each stage, the Gemini agent will execute a script (e.g., `validate_coverage.py`) to programmatically check for compliance. A script failure signals a failed gate, which the agent will handle, thus providing automated enforcement.

4.  **Commands**: User-facing "commands" (e.g., `/commit`) will be interpreted by the Gemini agent as high-level instructions, which it will translate into a sequence of actions using its native tools (e.g., running `git commit` via `run_shell_command`).

## Rationale

This approach provides a pragmatic path to a more automated and robust implementation without requiring a new, hypothetical cloud platform.

*   **Feasibility**: It is immediately implementable using the Gemini CLI's existing feature set.
*   **Automation**: It replaces manual human execution with automated agent orchestration, reducing errors and increasing speed.
*   **Robustness**: By converting conceptual "skills" and "gates" into executable and testable scripts, the methodology becomes less ambiguous and more reliable.
*   **Reusability**: It provides a framework for reusing the significant investment in the `claude-code` methodology's prompts and structure, as detailed in ADR-009.

## Consequences

- The "Gemini implementation" will consist of the Gemini agent plus a set of version-controlled scripts and configuration files in the `gemini-code` directory.
- The user's role shifts from a "driver" to a "navigator," providing high-level direction to the Gemini agent.
- The `claude-code` implementation serves as the foundational "source code" for the prompts and logic that the Gemini implementation will adapt and automate.
- New development will focus on creating robust, executable skill and validation scripts rather than just markdown prompt files.
