# ADR-001: React 19 + Vite 6 as Frontend Stack

**Status**: Accepted | **Date**: 2026-03-12
**Implements**: REQ-NFR-ARCH-001, REQ-F-APPSHELL-001

## Decision

Use React 19 with Vite 6 and TypeScript 5.x for the frontend.

## Rationale

- Declared in `project_constraints.yml` — not a new decision, binding confirmed here
- React 19 concurrent features (Suspense, transitions) align with async data loading UX
- Vite 6 provides fast HMR and ESM-native build — no webpack module federation complexity needed (see `ai_mfe_portal` analysis: the navigator is a single app, not a shell)
- TypeScript types generated from OpenAPI schema provide end-to-end type safety

## Consequences

- Frontend is a single-page application, not a micro-frontend shell
- All inter-view communication is through React state/context, not an event bus
- Build output: static HTML/CSS/JS deployable anywhere (file://, localhost, VS Code webview)
