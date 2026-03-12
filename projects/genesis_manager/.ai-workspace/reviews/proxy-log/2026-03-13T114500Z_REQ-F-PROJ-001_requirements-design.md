# Proxy Decision — requirements→design

**Decision**: approved
**Actor**: human-proxy
**Timestamp**: 2026-03-13T11:45:00Z
**Feature**: REQ-F-PROJ-001
**Edge**: requirements→design
**Gate**: human_approves_architecture
**Artifact**: imp_react_vite/design/REQ-F-PROJ-001-design.md

## Criterion: Architecture is sound and trade-offs are acceptable

**Evidence**:

1. **Local Express server** resolves the browser-filesystem gap correctly. The constraint (ASS-001: same machine) makes this the natural solution. Vite proxy in dev, Express serves SPA in prod — clean dev/prod parity.

2. **Zustand** is appropriate for this scale. The store boundary is clear (project list + active project + workspace summaries). Persist middleware handles localStorage without custom code. Alternatives (Context+useReducer) were correctly rejected for their re-render and persistence limitations.

3. **React Router 6** with `createBrowserRouter` gives REQ-F-NAV-005 bookmarkable canonical URLs. The `ROUTES` constant pattern prevents link drift — sound.

4. **Tailwind + shadcn/ui** is right for a single-developer tool: owned components (no dependency lock-in), accessible defaults, Vite-compatible. MUI correctly rejected (bundle weight, styling friction).

5. **Server-side workspace registry** (`~/.genesis_manager/workspaces.json`) is a good call over browser localStorage for path persistence — survives browser clear, survives profile reset.

6. **Workspace write path** (CTL Phase 4) routed through same Express server at `POST /api/workspaces/:id/events` with append-only + file lock. Correct for REQ-DATA-WORK-002.

7. **No ADR gaps**: all 4 TBD areas from design_recommendations are resolved. ADR-005 (write serialisation) correctly deferred to Phase 4 — it's not needed until CTL design.

**Risk check**: The only risk I see is the Express server startup coupling (both processes must be running). Mitigation: `concurrently` in dev; single process in prod (Express serves static build). Acceptable for a local dev tool.

**Result**: PASS — architecture is sound and all trade-offs are acceptable.
