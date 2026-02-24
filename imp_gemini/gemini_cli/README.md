# AI SDLC — Gemini CLI Implementation Code

This directory contains the implementation of the AI SDLC formal system on the Gemini CLI platform.

## Architecture

The implementation follows the three-layer model:
- **Engine Layer**: Core iteration and graph navigation logic.
- **Graph Package**: Configuration-based asset types and transitions.
- **Project Binding**: Instance-specific project constraints and context.

## Directory Structure

- `agents/`: Universal iterate agent and observer definitions.
- `commands/`: Slash commands for the Gemini CLI.
- `config/`: Default graph topology and edge parameterisations.
- `internal/`: Core state machine and workspace management logic.
- `installers/`: Setup and configuration scripts.
- `skills/`: Genesis bootloader and shared capabilities.

## Usage

Use the `/gen-init` command to bootstrap a new project workspace. Use `/gen-start` for state-driven routing and task execution.
