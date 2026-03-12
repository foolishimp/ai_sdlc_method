# ADR-GM-001: State Management — Zustand
# Implements: REQ-F-PROJ-001, REQ-F-PROJ-003

**Status**: Accepted | **Date**: 2026-03-13

## Context
The SPA needs global state for: registered workspace paths (persist across sessions), active project selection, polled workspace summaries, and UX state (drawer open/closed, freshness timestamp). Three options evaluated.

## Decision
**Zustand** with persist middleware for workspace paths and active project.

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Zustand** | Minimal boilerplate; TypeScript-first; persist middleware built-in; works outside React (for API polling); compatible with Vite HMR | Less opinionated than Redux — requires team discipline |
| **React Context + useReducer** | No dependency; built-in | Verbose for cross-cutting state; no built-in persistence; re-render storms with large state trees |
| **Jotai** | Atomic model, minimal re-renders | Less mature ecosystem; atomic model adds cognitive overhead for small team |

## Consequences
- `useProjectStore`, `useWorkspaceStore` are Zustand slices
- `persist` middleware writes `activeProjectId` and `registeredPaths` to `localStorage`
- Polling logic lives in store actions (`refresh()`) not in components — testable without rendering
- **Connects to**: REQ-F-PROJ-003 (active project switch updates all work areas via store subscription)
