# ADR-002: Local Filesystem Storage

**Status**: Accepted
**Date**: 2026-02-26

## Context
The methodology must operate on local developer workspaces without requiring external databases.

## Decision
Use the local filesystem (specifically the `.ai-workspace` directory) for all state and asset storage.

## Alternatives Considered
- **SQLite**: Good for structured data, but makes the workspace less "transparent" to simple grep/text tools.
- **Cloud Storage**: Adds latency and dependency on network connectivity.

## Consequences
- Workspace is fully portable and version-controllable (via git).
- Easy inspection of methodology state using standard CLI tools.
