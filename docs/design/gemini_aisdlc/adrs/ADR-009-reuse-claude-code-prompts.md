# ADR-009: Reuse Claude-Code Prompts for Gemini Agent Context

**Date**: 2025-12-16
**Status**: Proposed

## Context

As decided in ADR-008, the Gemini AI-SDLC implementation will be orchestrated by the Gemini CLI agent. This agent requires context, instructions, and persona definitions to perform its duties at each of the 7 lifecycle stages.

The `claude-code` implementation contains a rich, mature, and comprehensive set of prompts for this exact purpose, located in `claude-code/.claude-plugin/plugins/aisdlc-methodology/`. This includes detailed markdown files for agents, commands, and skills.

We need to decide how the Gemini agent will source its operational context.

## Decision

The Gemini CLI agent will **directly read and use the existing `claude-code` markdown and YAML files for its contextual understanding**.

Instead of creating a new, parallel set of `gemini-code` prompts, the agent will be directed to the `claude-code` directory to source its instructions.

The mapping will be as follows:

| Gemini Agent Need | Source `claude-code` Asset | How it will be Used |
| :--- | :--- | :--- |
| **Stage Persona** | `agents/*.md` | The Gemini agent will read the appropriate agent file at the start of each stage to set its persona, role, and responsibilities. |
| **Skill Logic** | `skills-consolidated/*.md` or `skills/**/SKILL.md` | Before executing an *executable skill script* (per ADR-008), the agent will first read the corresponding `claude-code` skill markdown file to understand the goal, context, and steps required. The script automates the "how," but the prompt file defines the "what" and "why." |
| **Command Interpretation** | `commands/*.md` | When a user gives a command-like instruction (e.g., "commit the task"), the agent will read the corresponding command markdown file to understand the expected behavior and sequence of actions to perform. |
| **Configuration** | `config/*.yml` | The agent will read the `stages_config.yml` and `config.yml` files to get configuration details, such as quality gate thresholds or Key Principles. |

## Rationale

This decision is based on the principle of **Reuse Before Build** (Key Principle #4).

*   **Minimize Customization**: The `claude-code` prompts have been refined over time and are considered the canonical definition of the methodology's text-based logic. Reusing them directly saves significant effort and avoids a content fork.
*   **Single Source of Truth**: The `claude-code` implementation remains the primary reference for the methodology's logic and prompts. The Gemini implementation becomes a different *execution layer* on top of the same source of truth.
*   **Simplified Maintenance**: Any updates to the core methodology prompts only need to be made in one place (`claude-code`). The Gemini agent will automatically pick up the changes on its next run.
*   **Focus on Automation**: This allows development effort for the Gemini implementation to focus on building robust *executable scripts* for skills and validation, rather than duplicating and maintaining a parallel set of prompt documentation.

## Consequences

- The `gemini-code` directory will contain primarily executable scripts (`.py`, `.sh`) and any necessary Gemini-specific configuration, but it will *not* duplicate the agent, skill, or command markdown prompts.
- The Gemini agent's bootstrap instructions must include paths to the `claude-code` plugin directory.
- A failure or ambiguity in the core `claude-code` prompts will affect both the Claude and Gemini implementations, reinforcing its status as the single source of truth.
- The Gemini implementation's "special sauce" is its ability to translate the instructions from the `claude-code` prompts into automated actions using its native tools, a capability the Claude assistant lacks.
