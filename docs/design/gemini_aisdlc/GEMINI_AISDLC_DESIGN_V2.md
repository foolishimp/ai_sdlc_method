# Gemini AI-SDLC Implementation Design - V2 (CLI-Native)

**Date**: 2025-12-16
**Status**: Proposed
**Version**: 2.0

## 1. Overview

This document outlines the **CLI-Native** design for the Gemini implementation of the AI-SDLC methodology. This design is a practical, feasible approach grounded in the native capabilities of the Gemini CLI agent and its available tools.

It supersedes the previous hypothetical, cloud-native design and is based on the foundational decisions captured in the following ADRs:

-   **[ADR-008: Gemini CLI-Native Orchestration](./adrs/ADR-008-gemini-cli-native-orchestration.md)**: Establishes the Gemini CLI agent as the central orchestrator of the file-based methodology.
-   **[ADR-009: Reuse Claude-Code Prompts for Gemini Agent Context](./adrs/ADR-009-reuse-claude-code-prompts.md)**: Mandates the direct reuse of the mature `claude-code` prompt assets to minimize customization and maintain a single source of truth.

## 2. Core Architecture: Agent-Orchestrated Automation

The Gemini implementation's architecture is defined by the **Gemini CLI agent acting as the execution engine** for the established AI-SDLC file-based structure. The user provides high-level guidance, and the agent performs the full lifecycle.

### Architectural Diagram

```
┌───────────────────────────────────────┐
│              USER (Navigator)         │
└───────────────────┬───────────────────┘
                    │ High-level goals
                    ▼
┌──────────────────────────────────────────────────────────┐
│              GEMINI CLI AGENT (Orchestrator)             │
│                                                          │
│  ┌────────────────────┐   ┌────────────────────────────┐ │
│  │ My Internal Logic  │   │  My Native Tools           │ │
│  │ (Workflow Engine)  │   │  (run_shell_command, etc.) │ │
│  └────────────────────┘   └────────────────────────────┘ │
└───────────────────┬──────────────────────────────────────┘
                    │ Reads context / instructions
                    ▼
┌──────────────────────────────────────────────────────────┐
│                  PROJECT REPOSITORY (Git)                │
│                                                          │
│  ┌────────────────────────┐   ┌────────────────────────┐ │
│  │ claude-code/           │   │ gemini-code/           │ │
│  │                        │   │                        │ │
│  │  ▶ Prompts (Agents)   │   │  ▶ Executable Skills   │ │
│  │  ▶ Prompts (Skills)   │   │  ▶ Validation Scripts  │ │
│  │  ▶ Config (YAML)      │   │  (for Quality Gates)   │ │
│  └────────────────────────┘   └────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Component Translation

This table defines the "native" translation from the conceptual `claude-code` implementation to the concrete Gemini CLI implementation.

| Methodology Component | `claude-code` Implementation (Human-Driven) | Gemini CLI-Native Implementation (Agent-Driven) |
| :--- | :--- | :--- |
| **Workflow Engine** | Human developer following prompts. | **The Gemini agent's internal logic**, guided by user commands and agent persona files. |
| **Agents** | Markdown prompts that guide the human. | The agent reads the **same markdown prompts** from `claude-code/agents/` to set its own persona for each stage. |
| **Skills** | Markdown prompts (`SKILL.md`) describing a task for a human to do. | **Executable scripts** (`.py`, `.sh`) in `gemini-code/skills/`. The agent reads the corresponding `claude-code` skill prompt for the *goal*, then executes the script to achieve it. |
| **Quality Gates** | Checklists and manual verification steps. | **Validation scripts** in `gemini-code/validation/`. The agent runs these scripts at stage boundaries and handles failures, providing automated enforcement. |
| **Commands** | UI slash commands that provide text assistance. | High-level user instructions that the agent translates into a series of **native tool calls** (e.g., "commit" -> `git add`, `git commit`). |
| **Configuration**| YAML files read by the Claude assistant. | The agent **directly reads the same YAML files** from `claude-code/config/` to configure its behavior and script parameters. |

## 3. Workflow Example: Code Stage TDD Cycle

This example illustrates how the agent automates the TDD cycle.

**User**: "Implement the login feature as defined in `REQ-F-AUTH-001`."

1.  **Set Persona**: The agent enters the "Code" stage. It reads `claude-code/.../agents/aisdlc-code-agent.md` to understand its role is to perform TDD.

2.  **Read Skill Prompt**: The agent reads the `claude-code/.../skills/code/tdd/red-phase/SKILL.md` prompt to understand the goal: "Create a failing test that captures the requirement."

3.  **Execute Executable Skill**: The agent runs the corresponding script: `run_shell_command("python gemini-code/skills/create_failing_test.py --requirement REQ-F-AUTH-001")`. This script creates the new test file.

4.  **Verify Red Phase**: The agent runs `run_shell_command("pytest")` and checks the output to ensure the test fails as expected.

5.  **Green & Refactor**: The agent repeats this pattern for the Green and Refactor phases, reading the `claude-code` skill prompts for the goals and executing its own `implement_code.py` and `refactor_code.py` scripts.

6.  **Enforce Quality Gate**: Before finishing, the agent runs the quality gate script: `run_shell_command("python gemini-code/validation/check_test_coverage.py --min 80")`. If the script fails, the agent reports the failure and may loop back to a previous step.

7.  **Commit**: The agent reads `claude-code/.../commands/aisdlc-commit.md` to understand how to form a good commit message, then uses `run_shell_command` to execute `git commit -m "..."`.

## 4. Implementation Details

-   The `gemini-code` directory will be the home for all executable logic. It will *not* contain duplicates of the markdown prompts from `claude-code`.
-   Scripts in `gemini-code/skills/` should be designed to be idempotent and focused on a single task where possible.
-   The initial "bootstrap" instructions for the Gemini agent must include the knowledge that it should use the `claude-code` directory as the source for its contextual prompts.

This design provides a clear path forward, leveraging existing assets while fully embracing the automation capabilities of the Gemini CLI to create a more powerful and efficient implementation of the AI-SDLC.
