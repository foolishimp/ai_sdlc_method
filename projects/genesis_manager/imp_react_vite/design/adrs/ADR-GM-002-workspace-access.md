# ADR-GM-002: Workspace Access — Local Express Server
# Implements: REQ-DATA-WORK-001, REQ-DATA-WORK-002, REQ-F-PROJ-004

**Status**: Accepted | **Date**: 2026-03-13

## Context
A browser SPA cannot directly read the local filesystem. genesis_manager must read `.ai-workspace/events.jsonl`, feature vectors, and graph topology (REQ-DATA-WORK-001). The same access path must support writes for CTL actions (REQ-DATA-WORK-002). ASS-001: user is on the same machine as the workspace.

## Decision
**Co-located Node.js + Express server** on `localhost:3001`, started alongside Vite dev server via `concurrently`. Vite proxies `/api/*` in dev; Express serves the static build + API in production.

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Local Express server** | Full filesystem access; handles both reads and writes; single architecture for dev+prod; REST is testable | Requires starting two processes; adds Node.js server dependency |
| **Tauri / Electron** | Native filesystem access; single-process | Requires packaging as native app; blocks browser-based deployment; heavy toolchain; out of scope for initial delivery |
| **File System Access API (browser)** | No server required; pure browser | Requires user file permission dialogs per workspace; no background polling; write support limited; poor DX for power users with multiple workspaces |

## Consequences
- `server/` directory in `imp_react_vite/` holds Express routes and workspace readers
- Workspace path registry stored in `~/.genesis_manager/workspaces.json` (server-side, survives browser localStorage clear)
- `vite.config.ts` sets `proxy: { '/api': 'http://localhost:3001' }` for dev
- `npm run dev` uses `concurrently` to start both Vite and `tsx watch server/index.ts`
- **Phase 4 (CTL) consequence**: writes to `events.jsonl` go through `POST /api/workspaces/:id/events` — same server, append-only endpoint with file lock
- **Connects to**: REQ-DATA-WORK-001 (read-only default), REQ-DATA-WORK-002 (write only on explicit action via API)
