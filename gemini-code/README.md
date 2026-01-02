# Gemini Code - AI-SDLC Implementation

This directory contains the **executable** implementation of the AI-SDLC methodology for the Gemini CLI agent, as defined in `docs/design/gemini_aisdlc/GEMINI_AISDLC_DESIGN_V2.md`.

## Architecture Overview

This implementation uses the Gemini CLI agent as a central orchestrator. Unlike the `claude-code` implementation, which contains prompt-based guidance for a human developer, this directory contains **executable scripts** that the Gemini agent runs to automate the software development lifecycle.

-   **Prompt Source**: The Gemini agent reads its contextual instructions and persona-based prompts from the `claude-code` directory (see `ADR-009`).
-   **Execution Engine**: This `gemini-code` directory provides the executable "muscle" for the Gemini agent to perform actions.

### Directory Structure

-   `installers/`: Scripts for setting up projects (may be subject to review/update).
-   `skills/`: Contains executable scripts that represent a specific "skill" the agent can perform (e.g., creating a test, implementing code). This is the "action" layer.
-   `validation/`: Contains executable scripts that act as "Quality Gates." The agent runs these at the end of stages to enforce methodology rules (e.g., checking test coverage).

## How it Works

1.  **User** provides a high-level command (e.g., "Implement the login feature").
2.  **Gemini Agent** reads its persona from the `claude-code/agents/` prompts.
3.  **Gemini Agent** reads the goal of a specific skill from the `claude-code/skills-consolidated/` prompts.
4.  **Gemini Agent** executes the corresponding executable script from this `gemini-code/skills/` directory using its `run_shell_command` tool to accomplish the goal.
5.  **Gemini Agent** runs a validation script from `gemini-code/validation/` to ensure the quality gate is passed.
6.  The cycle repeats for all stages of the AI-SDLC.
