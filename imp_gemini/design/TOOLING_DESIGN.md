# Design: Developer Tooling

**Version**: 1.0.0
**Date**: 2026-02-27
**Implements**: REQ-F-TOOL-001

---

## Architecture Overview
The tooling is built as a modular CLI application where commands are implemented as independent Python classes. It uses a Plugin architecture defined by `plugin.json` to discover available commands and agents.

## Component Design

### Component: CLI (gemini_cli.cli)
**Implements**: REQ-TOOL-003
**Responsibilities**: Entry point for all methodology commands. Handles argument parsing and routing.

### Component: CommandRegistry
**Implements**: REQ-TOOL-001
**Responsibilities**: Dynamically loads command implementations from `plugin.json`.

### Component: GapsCommand
**Implements**: REQ-TOOL-005
**Responsibilities**: Scans for REQ keys and identifies missing implementations or tests.

## Traceability Matrix
| REQ Key | Component |
|---------|----------|
| REQ-TOOL-001 | CommandRegistry |
| REQ-TOOL-003 | CLI, InitCommand, SpawnCommand, IterateCommand |
| REQ-TOOL-005 | GapsCommand |

## ADR Index
- [ADR-010: Command-Plugin Architecture](adrs/ADR-010-command-plugin-arch.md)
