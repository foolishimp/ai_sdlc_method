# ADR-GM-005: Workspace Write Protocol — Append-Only File Lock via Express
# Implements: REQ-DATA-WORK-002, REQ-F-CTL-001, REQ-F-CTL-002, REQ-F-CTL-003

**Status**: Accepted | **Date**: 2026-03-13

## Context
REQ-F-CTL-002 requires emitting `review_approved` to `events.jsonl`. REQ-DATA-WORK-002 requires writes only on explicit user action, with a log entry per write. REQ-DATA-WORK-001 states `events.jsonl` is append-only. The Genesis bootloader §V states "events are never modified or deleted." Concurrent writes from multiple browser tabs or the CTL action plus background polling must not corrupt the event log.

## Decision
**Express server handles all writes**. The `POST /api/workspaces/:id/events` endpoint:
1. Acquires a file lock (`proper-lockfile` npm package) on `events.jsonl`
2. Appends the event as a single JSON line + newline
3. Releases the lock
4. Logs the write (timestamp, action type, workspace path) — satisfying REQ-DATA-WORK-002 AC3

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Express + proper-lockfile** | Simple; crash-safe (lock released on process exit); append-only enforced at server; no external dependency | `proper-lockfile` is a file-based lock — not a DB-level lock; adequate for single-user tool |
| **SQLite as event store** | ACID transactions; concurrent-safe | Breaks REQ-DATA-WORK-001 (events.jsonl as source of truth); genesis_manager must not replace the event format |
| **Browser File System Access API (write)** | No server needed | No concurrency control; no lock primitive available in browser; data integrity risk |

## Consequences
- Single write endpoint: `POST /api/workspaces/:id/events` body: `{ event_type, feature, edge, data, actor?, comment? }`
- Server constructs the full event JSON (adds `timestamp`, `project`) — client never constructs raw event
- Write log appended to `~/.genesis_manager/write_log.jsonl` per write (REQ-DATA-WORK-002 AC3)
- `proper-lockfile` added to server dependencies
- **Connects to**: REQ-DATA-WORK-002 (write only on explicit action), REQ-F-CTL-002 (gate approval/rejection), REQ-F-CTL-003 (spawn), REQ-F-CTL-004 (auto-mode)
