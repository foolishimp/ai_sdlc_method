# ADR-003: Simple Event Sourcing

**Status**: Accepted
**Date**: 2026-02-26

## Context
We need a robust way to track methodology progress and enable session recovery.

## Decision
Implement a simple JSONL-based event log (`events.jsonl`) as the single source of truth for the workspace state.

## Alternatives Considered
- **State Snapshotting**: Easier to implement but loses history and auditability.
- **Git-only state**: Possible, but coupling methodology state too tightly to git commits can be noisy.

## Consequences
- Full audit trail of every `iterate()` call.
- State can be reconstructed by replaying the event log.
