# ADR-010: Command-Plugin Architecture

**Status**: Accepted
**Date**: 2026-02-27

## Context
We need to allow the methodology tooling to be easily extended with new commands without changing the core engine.

## Decision
Implement a plugin-based architecture where commands are registered in `plugin.json`. The CLI will dynamically load these commands and map them to their Python implementations.

## Consequences
- Commands can be developed and versioned independently.
- Users can install custom methodology plugins to extend the Gemini CLI.
