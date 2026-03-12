# Proxy Decision — Project Constraints Resolution

**Decision**: approved
**Actor**: human-proxy
**Timestamp**: 2026-03-13T11:00:00Z
**Gate**: NEEDS_CONSTRAINTS (deferred constraint prompting — requirements→design boundary)
**Feature**: genesis_manager (project-level)

## Criteria Evaluated

| Criterion | Evidence | Result |
|-----------|----------|--------|
| ecosystem_compatibility defined | design_tenants declares `react_vite`; TypeScript is standard for React+Vite; React 18+Vite 5 are current stable | PASS |
| deployment_target defined | Single-user local tool per INTENT.md; no cloud needed; local dev server + static build | PASS |
| security_model defined | INTENT.md: "not a team coordination tool"; single-user; no authentication required | PASS |
| build_system defined | Vite + npm is the react_vite tenant's implied build system; Vitest is Vite's native test runner | PASS |

## Resolved Values

- Language: TypeScript 5.x
- Runtime: Browser (SPA)
- Frameworks: React 18, Vite 5, React Router 6, Zustand (state)
- Test runner: Vitest + React Testing Library
- Deployment: Local dev server; static build for self-hosting
- Security: No auth (single-user local tool)
- Build: Vite + npm
- Performance advisory: UI transitions < 200ms
- Error handling: React Error Boundaries, fail-visible

## Reasoning

All four mandatory dimensions are determinable from the declared design tenant (`react_vite`) and the INTENT.md definition of genesis_manager as a single-user local supervision console. No ambiguity requiring human judgment — the constraint surface follows from the product shape.
