# Design: User Experience

**Version**: 1.0.0
**Date**: 2026-02-27
**Implements**: REQ-F-UX-001

---

## Architecture Overview
The UX layer is implemented as a thin controller over the toolchain. It uses a StateManager to identify the current ProjectState and select the next task.

## Component Design

### Component: StateManager
**Implements**: REQ-UX-001
**Responsibilities**: Drives the state machine logic from the event log and filesystem.

### Component: StartCommand
**Implements**: REQ-UX-001, REQ-UX-004
**Responsibilities**: The primary entry point for methodology execution.

### Component: StatusCommand
**Implements**: REQ-UX-003
**Responsibilities**: Aggregates state across all feature vectors.

## Traceability Matrix
| REQ Key | Component |
|---------|----------|
| REQ-UX-001 | StateManager, StartCommand |
| REQ-UX-003 | StatusCommand |
| REQ-UX-004 | StateManager, StartCommand |

## ADR Index
- [ADR-011: Two-Verb UX Architecture](adrs/ADR-011-two-verb-ux.md)
